#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测 HarmonyOS / DevEco 本机环境，输出文本或 JSON。"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from search_kb import _resolve_resource

EXPECTED = {"devecocli": "1.3.12", "deveco": "0.2.5"}
ENV_KEYS = [
    "DEVECO_CLI_STUDIO_PATH",
    "DEVECO_CLI_CLT_PATH",
    "DEVECO_CLI_DOCS",
    "DEVECO_CLI_INDEX",
    "DEVECO_CLI_ROOT",
    "DEVECO_TESTING_HOME",
    "DEVECO_HOME",
]


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def run_command(args: list[str], timeout: int = 20) -> dict[str, Any]:
    name = args[0]
    executable = shutil.which(name)
    if not executable:
        return {"available": False, "path": None, "args": args, "error": "not found"}
    try:
        proc = subprocess.run(
            [executable, *args[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        output = (proc.stdout or "").strip()
        error = (proc.stderr or "").strip()
        return {
            "available": True,
            "path": executable,
            "args": args,
            "exit_code": proc.returncode,
            "stdout": output,
            "stderr": error,
        }
    except subprocess.TimeoutExpired:
        return {"available": True, "path": executable, "args": args, "error": "timeout"}
    except Exception as exc:
        return {"available": True, "path": executable, "args": args, "error": str(exc)}


def first_line(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().splitlines()[0].strip()


def parse_json_output(result: dict[str, Any]) -> Any:
    if result.get("exit_code") != 0:
        return None
    text = result.get("stdout") or ""
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass
    return None


def find_project_root(start: Path | None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / "build-profile.json5").is_file() or (
            candidate / "oh-package.json5"
        ).is_file():
            return candidate
    return None


def resolve_knowledge_base() -> dict[str, Any]:
    docs = _resolve_resource("docs.zip", "DEVECO_CLI_DOCS")
    index = _resolve_resource("index.zip", "DEVECO_CLI_INDEX")
    return {
        "docs_path": docs,
        "docs_exists": bool(docs and Path(docs).is_file()),
        "index_path": index,
        "index_exists": bool(index and Path(index).is_file()),
    }


def build_report(project_arg: str | None, skip_devices: bool) -> dict[str, Any]:
    cli = run_command(["devecocli", "--version"])
    code = run_command(["deveco", "--version"])
    report: dict[str, Any] = {
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "cwd": str(Path.cwd()),
        "cli": {
            "version": first_line(cli.get("stdout")) or first_line(cli.get("stderr")),
            "path": cli.get("path"),
            "available": cli.get("available", False),
            "raw": cli,
        },
        "deveco_code": {
            "version": first_line(code.get("stdout")) or first_line(code.get("stderr")),
            "path": code.get("path"),
            "available": code.get("available", False),
            "raw": code,
        },
        "environment": {
            key: {"value": os.environ.get(key), "exists": Path(os.environ[key]).exists() if os.environ.get(key) else False}
            for key in ENV_KEYS
        },
        "project_root": None,
        "knowledge_base": resolve_knowledge_base(),
    }

    root = find_project_root(Path(project_arg) if project_arg else None)
    report["project_root"] = str(root) if root else None

    warnings: list[str] = []
    for key, expected in EXPECTED.items():
        entry = "cli" if key == "devecocli" else "deveco_code"
        actual = report[entry]["version"]
        if actual and actual != expected:
            warnings.append(f"{key} version drift: expected {expected}, got {actual}")
        if not actual:
            warnings.append(f"{key} unavailable")
    kb = report["knowledge_base"]
    if not kb.get("docs_exists") or not kb.get("index_exists"):
        warnings.append("offline knowledge base incomplete")
    if root is None:
        warnings.append("no HarmonyOS project found from cwd")

    if not skip_devices and report["cli"]["available"]:
        devices = run_command(["devecocli", "device", "list", "--format", "json"], timeout=20)
        emulators = run_command(["devecocli", "emulator", "list", "--format", "json"], timeout=20)
        report["devices"] = parse_json_output(devices)
        report["emulators"] = parse_json_output(emulators)
        report["device_query"] = {"devices": devices, "emulators": emulators}
        if devices.get("exit_code") != 0:
            warnings.append("device list failed")
        if emulators.get("exit_code") != 0:
            warnings.append("emulator list failed")

    testing = run_command(["devecocli", "testing", "--help"], timeout=15)
    report["deveco_testing"] = {
        "available": testing.get("exit_code") == 0,
        "exit_code": testing.get("exit_code"),
        "message": first_line(testing.get("stderr")) or first_line(testing.get("stdout")),
    }
    report["warnings"] = warnings
    return report


def print_text(report: dict[str, Any]) -> None:
    print("HarmonyOS / DevEco 环境")
    print(f"  cwd: {report['cwd']}")
    print(f"  devecocli: {report['cli']['version'] or 'unavailable'} ({report['cli']['path']})")
    print(f"  deveco: {report['deveco_code']['version'] or 'unavailable'} ({report['deveco_code']['path']})")
    print(f"  project: {report['project_root'] or 'not found'}")
    kb = report["knowledge_base"]
    print(f"  docs: {kb.get('docs_path')} exists={kb.get('docs_exists')}")
    print(f"  index: {kb.get('index_path')} exists={kb.get('index_exists')}")
    if "devices" in report:
        print(f"  devices: {json.dumps(report.get('devices'), ensure_ascii=False)}")
        print(f"  emulators: {json.dumps(report.get('emulators'), ensure_ascii=False)}")
    testing = report.get("deveco_testing", {})
    print(f"  DevEco Testing: {testing.get('available')} {testing.get('message') or ''}".rstrip())
    if report.get("warnings"):
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")


def main() -> int:
    configure_console()
    parser = argparse.ArgumentParser(description="探测 HarmonyOS / DevEco 环境")
    parser.add_argument("--project", help="工程路径；默认从当前目录向上查找")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--skip-devices", action="store_true", help="跳过设备与模拟器查询")
    parser.add_argument("--strict", action="store_true", help="存在核心警告时返回非零")
    args = parser.parse_args()

    report = build_report(args.project, args.skip_devices)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)

    if args.strict and any("unavailable" in w or "incomplete" in w for w in report["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())