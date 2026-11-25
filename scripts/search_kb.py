#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HarmonyOS 离线知识库检索工具。

在 DevEco CLI 生态分发的离线知识库中检索鸿蒙（ArkTS / ArkUI / HarmonyOS NEXT）
相关文档：
  - docs.zip  : Markdown 文档（开发指南 / FAQ / API 参考 ...）
  - index.zip : search.db（SQLite 全文索引）+ 鸿蒙专有词表 + 中英同义词表

纯标准库实现，无第三方依赖。

默认路径自动探测 DevEco CLI 生态中的资源，依次查：
  环境变量 DEVECO_CLI_DOCS / DEVECO_CLI_INDEX → DEVECO_CLI_ROOT → 常见 npm 安装根目录。
也可显式传 --docs-path / --index-path 覆盖。

用法:
    python search_kb.py --keyword "RelationalStore"
    python search_kb.py -k "页面" "Page" --mode both --max-files 20
    python search_kb.py -k "ArkTS" --docs-path "D:/path/docs.zip" --index-path "D:/path/index.zip"
"""
import argparse
import functools
import glob
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from contextlib import closing


@functools.lru_cache(maxsize=1)
def _candidate_roots():
    """npm 全局/本地包根目录候选（按优先级，去重）。"""
    roots = []
    env_root = os.environ.get("DEVECO_CLI_ROOT")
    if env_root:
        roots.append(env_root)
    node_path = os.environ.get("NODE_PATH")
    if node_path:
        roots.extend(node_path.split(os.pathsep))
    for executable in ("devecocli", "deveco"):
        executable_path = shutil.which(executable)
        if not executable_path:
            continue
        bin_dir = os.path.dirname(os.path.abspath(executable_path))
        roots.append(os.path.join(bin_dir, "node_modules"))
        roots.append(os.path.join(os.path.dirname(bin_dir), "lib", "node_modules"))
    try:
        result = subprocess.run(
            ["npm", "root", "-g"],
            capture_output=True,
            check=True,
            text=True,
            timeout=10,
        )
        if result.stdout.strip():
            roots.append(result.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    appdata = os.environ.get("APPDATA")
    if appdata:
        roots.append(os.path.join(appdata, "npm", "node_modules"))
    roots += [
        os.path.join(os.environ.get("ProgramFiles", ""), "nodejs", "node_modules"),
        os.path.expanduser("~/.npm-global/lib/node_modules"),
        "/opt/homebrew/lib/node_modules",
        "/usr/local/lib/node_modules",
        "/usr/lib/node_modules",
    ]
    roots += glob.glob(os.path.expanduser("~/.nvm/versions/node/*/lib/node_modules"))
    roots += glob.glob(os.path.expanduser(
        "~/.volta/tools/image/node/*/lib/node_modules"))
    here = os.path.dirname(os.path.abspath(__file__))
    roots += [os.path.join(here, "node_modules"),
              os.path.join(os.getcwd(), "node_modules")]
    seen, out = set(), []
    for r in roots:
        if r and r not in seen:
            seen.add(r)
            out.append(r)
    return out


def _resolve_resource(filename, env_name):
    """定位知识库资源；找不到时返回 None。"""
    env_path = os.environ.get(env_name)
    if env_path and os.path.isfile(env_path):
        return env_path
    for root in _candidate_roots():
        # 顺序即优先级。新版（cli ≥1.3.x）将知识库拆为独立包：
        #   - @deveco/deveco-cli-knowledgebase （顶层 cli 1.3.12，schema 含 FTS5，两模式均可用）
        #   - @deveco/deveco-cli-common        （deveco-code 钉死的 cli 1.3.4，index.zip schema 不含 FTS5，sqlite 模式零输出）
        # 故 knowledgebase 优先；旧布局（随包 docs.zip）作为再兜底。
        for pattern in (
            os.path.join(root, filename),
            os.path.join(root, "@deveco", "deveco-cli-knowledgebase", filename),
            os.path.join(root, "@deveco", "deveco-cli", "node_modules",
                         "@deveco", "deveco-cli-knowledgebase", filename),
            os.path.join(root, "@deveco", "deveco-cli", filename),
            os.path.join(root, "@deveco", "deveco-code", "node_modules",
                         "@deveco", "deveco-cli-common", filename),
            os.path.join(root, "@deveco", "deveco-code", "node_modules",
                         "@deveco", "deveco-cli", filename),
        ):
            hits = glob.glob(pattern)
            if hits:
                return hits[0]
    return None


def _decode(b):
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", errors="replace")


def _fix_name(name):
    """zip 未置 UTF-8 标志时，zipfile 用 cp437 解码中文文件名会乱码。
    cp437 与字节 1:1 可逆，先还原字节再按 utf-8/gbk 解出正确中文名。
    仅用于展示；读取条目仍用原始 name 作为 key。"""
    try:
        raw = name.encode("cp437")
    except UnicodeError:
        return name
    return _decode(raw)


def search_zip(docs_path, keywords, limit, max_files, context, as_json=False):
    result = {"source": "zip", "docs_path": docs_path, "keywords": keywords,
              "result_count": 0, "results": []}
    if not docs_path or not os.path.isfile(docs_path):
        return search_error(result, "未找到 docs.zip。请设置 DEVECO_CLI_DOCS 或传入 --docs-path。", as_json)
    hits = []  # (relpath, [(lineno, snippet), ...])
    # 注：zip 未置 UTF-8 标志，Python 默认用 cp437 解码中文文件名会产生乱码
    # （如 "APIσÅéΦÇâ"）。cp437 是字节到字符的 1:1 映射，可逆；
    # 先把名按 cp437 还原为原始字节，再按 utf-8 / gbk 解码得到正确中文名。
    with zipfile.ZipFile(docs_path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".md")]
        pats = [re.compile(re.escape(k), re.IGNORECASE) for k in keywords]
        for name in names:
            try:
                data = _decode(zf.read(name))
            except Exception:
                continue
            lines = data.splitlines()
            matched = []
            for i, line in enumerate(lines):
                if any(p.search(line) for p in pats):
                    lo = max(0, i - context)
                    hi = min(len(lines), i + context + 1)
                    snippet = " | ".join(lines[lo:hi])
                    matched.append((i + 1, snippet))
            if matched:
                hits.append((_fix_name(name), matched))
    hits.sort(key=lambda x: len(x[1]), reverse=True)
    result["result_count"] = len(hits)
    result["results"] = [
        {"path": name, "match_count": len(matched),
         "matches": [{"line": line, "snippet": snippet[:300]} for line, snippet in matched[:limit]]}
        for name, matched in hits[:max_files]
    ]
    if not as_json:
        print("\n===== ZIP 检索：%d 个文件命中（关键词: %s）=====" %
              (len(hits), ", ".join(keywords)))
        for item in result["results"]:
            print("\n■ %s  (命中 %d 处)" % (item["path"], item["match_count"]))
            for match in item["matches"]:
                print("   L%d: %s" % (match["line"], match["snippet"]))
    return result


def search_error(result, message, as_json):
    result["error"] = message
    if not as_json:
        print(f"[{result['source']}] {message}")
    return result


def _extract_db(index_path, tmpdir):
    if not os.path.isfile(index_path):
        return None
    with zipfile.ZipFile(index_path) as zf:
        for n in zf.namelist():
            if n.lower().endswith(".db"):
                dest = os.path.join(tmpdir, os.path.basename(n))
                with open(dest, "wb") as f:
                    f.write(zf.read(n))
                return dest
    return None


def _text_columns(cur, tname):
    """探测表的文本列：按 PRAGMA 声明类型，排除纯 ID 列。

    不再依赖硬编码列名白名单——真实 schema（documents.doc_title /
    segments.lead_text,search_text,section_title）与旧白名单无一匹配。
    """
    try:
        cur.execute("PRAGMA table_info('%s')" % tname)
    except Exception:
        return []
    cols = []
    for r in cur.fetchall():
        name = r[1]
        decl = (r[2] or "").upper()
        low = name.lower()
        if low in ("id", "rowid") or (low.endswith("_id") and low != "document_id"):
            continue
        if any(t in decl for t in ("CHAR", "CLOB", "TEXT")) or decl == "":
            cols.append(name)
    return cols


def _fts_hits(cur, keywords, limit):
    """如存在 FTS5 虚表，用 MATCH 检索，返回 {rowid: text}。失败时静默返回空。"""
    hits = {}
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        names = [r[0] for r in cur.fetchall()]
    except Exception:
        return hits
    for ft in names:
        low = ft.lower()
        if "_fts" not in low or low.endswith(("_data", "_idx", "_docsize",
                                              "_config", "_content")):
            continue
        try:
            cur.execute("PRAGMA table_info('%s')" % ft)
            fcols = [r[1] for r in cur.fetchall()]
        except Exception:
            continue
        for col in fcols[:1]:
            for kw in keywords:
                safe = kw.replace('"', '""')
                try:
                    cur.execute('SELECT rowid, "%s" FROM "%s" WHERE "%s" MATCH ? LIMIT ?' %
                                (col, ft, col), ('"%s"' % safe, limit))
                    for r in cur.fetchall():
                        hits.setdefault(r[0], r[1])
                except Exception:
                    pass
    return hits


def search_sqlite(index_path, keywords, max_files, limit, as_json=False):
    result = {"source": "sqlite", "index_path": index_path, "keywords": keywords,
              "result_count": 0, "results": []}
    if not index_path or not os.path.isfile(index_path):
        return search_error(result, "未找到 index.zip。请设置 DEVECO_CLI_INDEX 或传入 --index-path。", as_json)
    with tempfile.TemporaryDirectory(prefix="harmonyos_kb_") as tmp:
        db = _extract_db(index_path, tmp)
        if not db:
            return search_error(result, f"search.db not found in {index_path}", as_json)
        with closing(sqlite3.connect(db)) as conn:
            _search_sqlite(conn, result, keywords, max_files, limit, as_json)
    return result


def _search_sqlite(conn, result, keywords, max_files, limit, as_json):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")
    all_tables = [r[0] for r in cur.fetchall()]
    tables = [n for n in all_tables
              if not n.startswith("sqlite_")
              and not n.lower().endswith(("_data", "_idx", "_docsize",
                                          "_config", "_content"))]
    if not tables:
        return search_error(result, "未发现可查询表", as_json)
    if not as_json:
        print("\n===== SQLite 检索（关键词: %s）=====" % ", ".join(keywords))
    shown, cap = 0, max_files * limit
    emitted = set()

    def emit(tname, rowid, body, tag=""):
        nonlocal shown
        key = (tname, rowid)
        if key in emitted or shown >= cap:
            return
        emitted.add(key)
        result["results"].append({"table": tname, "rowid": rowid,
                                  "match_type": "FTS5" if tag else "LIKE", "snippet": body[:300]})
        if not as_json:
            print("  [%s%s#%s] %s" % (tname, tag, rowid, body[:300]))
        shown += 1

    fts = _fts_hits(cur, keywords, cap)
    for rowid, text in sorted(fts.items()):
        emit("segments_fts", rowid, text or "", " [FTS5]")

    for tname in tables:
        if tname.lower().endswith("_fts"):
            continue  # FTS 结果已单独输出，避免重复
        cols = _text_columns(cur, tname)
        if not cols:
            continue
        for kw in keywords:
            if shown >= cap:
                break
            safe = kw.replace("'", "''")
            like = " OR ".join("CAST(%s AS TEXT) LIKE '%%%s%%'" % (c, safe)
                               for c in cols)
            try:
                cur.execute("SELECT rowid, %s FROM '%s' WHERE %s LIMIT %d" %
                            (", ".join(cols), tname, like, limit))
                for r in cur.fetchall():
                    body = " | ".join(str(x) for x in r[1:] if x is not None)
                    emit(tname, r[0], body)
            except Exception as e:
                if not as_json:
                    print("  [sqlite] query %s err: %s" % (tname, e))
    result["result_count"] = shown
    if shown == 0 and not as_json:
        print("  （无命中）")


def main():
    # Windows 下子进程 stdout 默认 cp936，强制 UTF-8 避免中文乱码（不影响正常 shell）
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="HarmonyOS 离线知识库检索")
    ap.add_argument("-k", "--keyword", nargs="+", required=True, help="关键词（可多个）")
    ap.add_argument("--docs-path")
    ap.add_argument("--index-path")
    ap.add_argument("--mode", choices=["zip", "sqlite", "both"], default="zip")
    ap.add_argument("--limit", type=int, default=3, help="每文件命中行展示上限")
    ap.add_argument("--max-files", type=int, default=15, help="展示文件数上限")
    ap.add_argument("--context", type=int, default=1, help="命中行上下文行数")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    args = ap.parse_args()
    as_json = args.format == "json"
    searches = []
    if args.mode in ("zip", "both"):
        path = args.docs_path or _resolve_resource("docs.zip", "DEVECO_CLI_DOCS")
        searches.append(search_zip(path, args.keyword, args.limit, args.max_files, args.context, as_json=as_json))
    if args.mode in ("sqlite", "both"):
        path = args.index_path or _resolve_resource("index.zip", "DEVECO_CLI_INDEX")
        searches.append(search_sqlite(path, args.keyword, args.max_files, args.limit, as_json=as_json))
    if as_json:
        print(json.dumps({"keywords": args.keyword, "mode": args.mode, "searches": searches},
                         ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
