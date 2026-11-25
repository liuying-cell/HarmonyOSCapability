#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汇总 HarmonyOS 工程配置，输出 text / JSON。"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SKIP_DIRS = {"oh_modules", "node_modules", ".hvigor", "build", ".git", "dist"}
ROOT_FILES = [
    "build-profile.json5",
    "oh-package.json5",
    "AppScope/app.json5",
    "app.json5",
    "hvigor/hvigor-config.json5",
]


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def strip_json5(text: str) -> str:
    """轻量 JSON5 降级转换：去注释、尾逗号，引用裸键。"""
    out: list[str] = []
    i = 0
    quote: str | None = None
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ('"', "'"):
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(text) and text[i : i + 2] != "*/":
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    cleaned = "".join(out)
    cleaned = re.sub(r"([\{,]\s*)([A-Za-z_$][\w$-]*)(\s*:)", r'\1"\2"\3', cleaned)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def load_json5(path: Path) -> tuple[Any | None, str | None]:
    try:
        text = read_text(path)
        try:
            return json.loads(text), None
        except Exception:
            pass
        try:
            import json5  # type: ignore
            return json5.loads(text), None
        except Exception:
            pass
        return json.loads(strip_json5(text)), None
    except Exception as exc:
        return None, f"{path}: {exc}"


def find_project_root(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / "build-profile.json5").is_file() or (
            candidate / "oh-package.json5"
        ).is_file():
            return candidate
    return None


def summarize_package(path: Path, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"path": str(path), "error": "root is not an object"}
    return {
        "path": str(path),
        "modelVersion": data.get("modelVersion"),
        "name": data.get("name"),
        "version": data.get("version"),
        "description": data.get("description"),
        "dependencies": data.get("dependencies", {}),
        "devDependencies": data.get("devDependencies", {}),
    }


def summarize_app_config(path: Path, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"path": str(path), "error": "root is not an object"}
    app = data.get("app", {}) if isinstance(data.get("app"), dict) else {}
    return {
        "path": str(path),
        "bundleName": app.get("bundleName"),
        "vendor": app.get("vendor"),
        "versionCode": app.get("versionCode"),
        "versionName": app.get("versionName"),
        "minAPIVersion": app.get("minAPIVersion"),
        "targetAPIVersion": app.get("targetAPIVersion"),
        "apiReleaseType": app.get("apiReleaseType"),
        "label": app.get("label"),
        "icon": app.get("icon"),
    }


def summarize_build_profile(path: Path, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"path": str(path), "error": "root is not an object"}
    app = data.get("app", {}) if isinstance(data.get("app"), dict) else {}
    modules = data.get("modules", []) if isinstance(data.get("modules"), list) else []
    products = []
    for item in app.get("products", []) if isinstance(app.get("products"), list) else []:
        if isinstance(item, dict):
            products.append(
                {
                    "name": item.get("name"),
                    "signingConfig": item.get("signingConfig"),
                    "compatibleSdkVersion": item.get("compatibleSdkVersion"),
                    "targetSdkVersion": item.get("targetSdkVersion"),
                    "compileSdkVersion": item.get("compileSdkVersion"),
                    "runtimeOS": item.get("runtimeOS"),
                }
            )
    return {
        "path": str(path),
        "products": products,
        "buildModes": [x.get("name") for x in app.get("buildModeSet", []) if isinstance(x, dict)],
        "signingConfigs": [
            x.get("name")
            for x in app.get("signingConfigs", [])
            if isinstance(x, dict) and x.get("name")
        ],
        "modules": [
            {
                "name": x.get("name"),
                "srcPath": x.get("srcPath"),
                "targets": x.get("targets", []),
            }
            for x in modules
            if isinstance(x, dict)
        ],
    }


def summarize_module(path: Path, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"path": str(path), "error": "root is not an object"}
    module = data.get("module", {}) if isinstance(data.get("module"), dict) else {}
    abilities = []
    for item in module.get("abilities", []) if isinstance(module.get("abilities"), list) else []:
        if isinstance(item, dict):
            abilities.append(
                {
                    "name": item.get("name"),
                    "srcEntry": item.get("srcEntry"),
                    "exported": item.get("exported"),
                    "skills": item.get("skills", []),
                }
            )
    extension_abilities = [
        {
            "name": item.get("name"),
            "srcEntry": item.get("srcEntry"),
            "type": item.get("type"),
            "exported": item.get("exported"),
        }
        for item in (module.get("extensionAbilities", []) if isinstance(module.get("extensionAbilities"), list) else [])
        if isinstance(item, dict)
    ]
    permissions = [
        item.get("name")
        for item in (module.get("requestPermissions", []) if isinstance(module.get("requestPermissions"), list) else [])
        if isinstance(item, dict) and item.get("name")
    ]
    return {
        "path": str(path),
        "name": module.get("name"),
        "type": module.get("type"),
        "mainElement": module.get("mainElement"),
        "deviceTypes": module.get("deviceTypes", []),
        "pages": module.get("pages"),
        "abilities": abilities,
        "extensionAbilities": extension_abilities,
        "requestPermissions": permissions,
    }


def find_module_files(root: Path, build_profile: dict[str, Any] | None) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    if build_profile:
        for item in build_profile.get("modules", []):
            src_path = item.get("srcPath")
            if not src_path:
                continue
            candidates = [
                root / src_path / "src/main/module.json5",
                root / src_path / "src/main/module.json",
            ]
            for candidate in candidates:
                if candidate.is_file() and candidate.resolve() not in seen:
                    seen.add(candidate.resolve())
                    files.append(candidate.resolve())
    for candidate in root.rglob("module.json5"):
        if any(part in SKIP_DIRS for part in candidate.parts):
            continue
        relative_parts = candidate.relative_to(root).parts
        if "ohosTest" in relative_parts or "test" in relative_parts:
            continue
        if candidate.resolve() not in seen:
            seen.add(candidate.resolve())
            files.append(candidate.resolve())
    return sorted(files, key=lambda p: str(p).lower())


def build_snapshot(root: Path) -> dict[str, Any]:
    warnings: list[str] = []
    files: dict[str, str | None] = {}
    parsed: dict[str, Any] = {}

    for rel in ROOT_FILES:
        path = root / rel
        if path.is_file():
            files[rel] = str(path)
            data, error = load_json5(path)
            if error:
                warnings.append(error)
            parsed[rel] = data
        else:
            files[rel] = None

    build_profile_data = parsed.get("build-profile.json5")
    build_profile = summarize_build_profile(root / "build-profile.json5", build_profile_data)
    app_rel = "AppScope/app.json5" if files.get("AppScope/app.json5") else "app.json5"
    app_config = summarize_app_config(root / app_rel, parsed.get(app_rel))
    packages = []
    for rel in ("oh-package.json5", "hvigor/hvigor-config.json5"):
        if files.get(rel):
            packages.append(summarize_package(root / rel, parsed.get(rel)))

    modules = []
    for path in find_module_files(root, build_profile if isinstance(build_profile, dict) else None):
        data, error = load_json5(path)
        if error:
            warnings.append(error)
            modules.append({"path": str(path), "error": error})
        else:
            modules.append(summarize_module(path, data))

    if not files.get("build-profile.json5"):
        warnings.append("build-profile.json5 not found")
    if not modules:
        warnings.append("module.json5 not found")

    return {
        "project_root": str(root),
        "files": files,
        "app": app_config,
        "build_profile": build_profile,
        "packages": packages,
        "modules": modules,
        "warnings": warnings,
    }


def print_text(snapshot: dict[str, Any]) -> None:
    print(f"Project: {snapshot['project_root']}")
    app = snapshot.get("app") or {}
    print(f"Bundle: {app.get('bundleName')}")
    bp = snapshot.get("build_profile") or {}
    print("Products:")
    for product in bp.get("products", []):
        print(
            "  - {name} compatible={compatibleSdkVersion} target={targetSdkVersion} "
            "signing={signingConfig}".format(**{k: product.get(k) for k in ('name', 'compatibleSdkVersion', 'targetSdkVersion', 'signingConfig')})
        )
    print("Build modes:", ", ".join(str(x) for x in bp.get("buildModes", [])) or "none")
    print("Modules:")
    for module in snapshot.get("modules", []):
        if module.get("error"):
            print(f"  - {module['path']}: {module['error']}")
            continue
        print(
            f"  - {module.get('name')} ({module.get('type')}) "
            f"main={module.get('mainElement')} devices={','.join(module.get('deviceTypes') or [])}"
        )
        for ability in module.get("abilities", []):
            print(f"      ability: {ability.get('name')} exported={ability.get('exported')}")
    if snapshot.get("warnings"):
        print("Warnings:")
        for warning in snapshot["warnings"]:
            print(f"  - {warning}")


def main() -> int:
    configure_console()
    parser = argparse.ArgumentParser(description="汇总 HarmonyOS 工程配置")
    parser.add_argument("--project", default=".", help="工程路径")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    root = find_project_root(Path(args.project))
    if root is None:
        print(f"Error: no HarmonyOS project found from {Path(args.project).resolve()}", file=sys.stderr)
        return 1
    snapshot = build_snapshot(root)
    if args.format == "json":
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    else:
        print_text(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())