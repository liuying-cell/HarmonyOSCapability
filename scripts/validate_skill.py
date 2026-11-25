#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UTF-8 安全的 HarmonyOS skill 结构与链接校验。"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, str, list[str]]:
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text, ["SKILL.md must start with YAML frontmatter"]
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text, ["frontmatter closing --- not found"]

    fm: dict[str, Any] = {}
    i = 1
    while i < end:
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        match = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if not match:
            errors.append(f"invalid frontmatter line {i + 1}: {line}")
            i += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if key == "metadata":
            meta: dict[str, str] = {}
            i += 1
            while i < end and (lines[i].startswith(" ") or not lines[i].strip()):
                nested = re.match(r"^\s+([A-Za-z][\w-]*):\s*(.*)$", lines[i])
                if nested:
                    meta[nested.group(1)] = nested.group(2).strip().strip('"\'')
                i += 1
            fm[key] = meta
            continue
        if value in (">-", ">", "|", "|-"):
            block: list[str] = []
            i += 1
            while i < end and (lines[i].startswith(" ") or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            fm[key] = " ".join(x for x in block if x).strip()
            continue
        fm[key] = value.strip().strip('"\'')
        i += 1

    body = "\n".join(lines[end + 1 :])
    return fm, body, errors


def validate_links(skill_dir: Path, body: str) -> list[str]:
    errors: list[str] = []
    for target in LINK_RE.findall(body):
        target = target.strip().split()[0].strip("<>")
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (skill_dir / path_part).resolve()
        try:
            resolved.relative_to(skill_dir.resolve())
        except ValueError:
            errors.append(f"link escapes skill directory: {target}")
            continue
        if not resolved.exists():
            errors.append(f"broken link: {target}")
    return errors


def validate_large_refs(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    refs = skill_dir / "references"
    if not refs.is_dir():
        return errors
    for path in refs.rglob("*.md"):
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        if len(lines) <= 100:
            continue
        has_toc = any(re.match(r"^#{1,3}\s+(目录|Contents|Table of Contents)\s*$", x, re.I) for x in lines[:30])
        if not has_toc:
            rel = path.relative_to(skill_dir)
            errors.append(f"reference exceeds 100 lines without TOC: {rel}")
    return errors


def validate_evals(skill_dir: Path) -> list[str]:
    path = skill_dir / "evals" / "cases.json"
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"evals/cases.json is invalid: {exc}"]
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list) or not cases:
        return ["evals/cases.json must contain a non-empty cases array"]
    errors: list[str] = []
    seen: set[str] = set()
    for index, case in enumerate(cases, 1):
        if not isinstance(case, dict):
            errors.append(f"eval case {index} is not an object")
            continue
        case_id = case.get("id")
        if not case_id:
            errors.append(f"eval case {index} has no id")
        elif case_id in seen:
            errors.append(f"duplicate eval id: {case_id}")
        else:
            seen.add(case_id)
        for key in ("user_request", "must_do", "must_not_do"):
            if key not in case:
                errors.append(f"eval case {case_id or index} missing {key}")
    return errors

def validate_openai_yaml(skill_dir: Path) -> list[str]:
    path = skill_dir / "agents" / "openai.yaml"
    if not path.is_file():
        return ["agents/openai.yaml is missing"]
    text = path.read_text(encoding="utf-8-sig")
    errors: list[str] = []
    for key in ("display_name", "short_description", "default_prompt"):
        if not re.search(rf"(?m)^\s*{re.escape(key)}:\s*\S", text):
            errors.append(f"agents/openai.yaml missing {key}")
    short = re.search(r"(?m)^\s*short_description:\s*[\"']?(.*?)[\"']?\s*$", text)
    if short and not (1 <= len(short.group(1)) <= 64):
        errors.append("short_description must be 1-64 characters")
    return errors


def validate(skill_dir: Path) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"
    errors: list[str] = []
    warnings: list[str] = []
    if not skill_md.is_file():
        return {"valid": False, "errors": ["SKILL.md is missing"], "warnings": []}
    try:
        text = skill_md.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        return {"valid": False, "errors": [f"SKILL.md is not valid UTF-8: {exc}"], "warnings": []}

    fm, body, fm_errors = parse_frontmatter(text)
    errors.extend(fm_errors)
    if fm is None:
        return {"valid": False, "errors": errors, "warnings": warnings}

    unknown = set(fm) - ALLOWED_KEYS
    if unknown:
        errors.append(f"unsupported frontmatter keys: {', '.join(sorted(unknown))}")
    if "metadata" in fm and not isinstance(fm["metadata"], dict):
        errors.append("metadata must be a YAML mapping")
    name = fm.get("name")
    description = fm.get("description")
    if not name or not isinstance(name, str):
        errors.append("frontmatter name is required")
    else:
        if len(name) > 64 or not NAME_RE.fullmatch(name):
            errors.append("name must be hyphen-case with at most 64 characters")
        if skill_dir.name != name:
            warnings.append("skill folder name differs from frontmatter name")
    if not description or not isinstance(description, str):
        errors.append("frontmatter description is required")
    elif len(description) > 1024:
        errors.append(f"description is too long: {len(description)} > 1024")
    if "TODO" in text or "PLACEHOLDER" in text.upper():
        errors.append("SKILL.md contains unfinished TODO/PLACEHOLDER text")

    errors.extend(validate_links(skill_dir, body))
    errors.extend(validate_openai_yaml(skill_dir))
    errors.extend(validate_large_refs(skill_dir))
    errors.extend(validate_evals(skill_dir))

    return {
        "valid": not errors,
        "skill": str(skill_dir),
        "name": name,
        "description_chars": len(description) if isinstance(description, str) else None,
        "body_lines": len(body.splitlines()),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    configure_console()
    parser = argparse.ArgumentParser(description="校验 HarmonyOS skill")
    parser.add_argument("skill", nargs="?", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    result = validate(Path(args.skill))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Skill: {result.get('skill', args.skill)}")
        print(f"Name: {result.get('name')}")
        print(f"Description chars: {result.get('description_chars')}")
        print(f"Body lines: {result.get('body_lines')}")
        for warning in result.get("warnings", []):
            print(f"WARNING: {warning}")
        for error in result.get("errors", []):
            print(f"ERROR: {error}")
        print("Skill is valid!" if result.get("valid") else "Skill validation failed.")
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())