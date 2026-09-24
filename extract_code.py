# -*- coding: utf-8 -*-
"""Splits each C file into top-level functions so the PDF can show the
actual source code next to every explanation."""

import re

import code_docs_data as D

# A function definition starts at depth 0, at column 0, and reads like:
#   <return-type> <name>(   optionally spanning several lines.
# It is followed by a brace body. Calls/prototypes end with ';' and are skipped.
FUNC_START = re.compile(
    r"^(?:void|int|double|float|char|bool|const|long|unsigned|short|static)"
    r"\b[^;{}]*\([^;]*(?:\n[^;{}]*)*$"
)


def _starts_function(line):
    if not line or line[0] == "#" or line[0].isspace() or line[0] == "{":
        return False
    stripped = line.lstrip()
    if stripped.startswith(("//", "/*", "*", "typedef", "#include", "#define",
                            "enum", "struct", "return", "if", "else", "for", "while", "switch", "case")):
        return False
    # must look like "sometype name(...)" and not end with ';'
    m = re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s+[A-Za-z_][A-Za-z0-9_]*\s*\(", stripped)
    if not m:
        return False
    if ";" in line:
        return False
    if "=" in line and "(" not in line.split("=")[0]:
        return False
    return True


def split_functions(src):
    """Return (preamble, [ (name, code) ... ]).

    Comments immediately preceding a function are attached to that
    function's code block; only the true file header (includes and
    stray trailing comments) lands in the preamble."""
    depth = 0
    in_func = False
    func_buf = []
    preamble = []
    funcs = []
    current_name = None
    pending = []
    in_block_comment = False

    def is_comment_line(line):
        nonlocal in_block_comment
        stripped = line.strip()
        if not stripped:
            return False
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            return True
        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block_comment = True
            return True
        if stripped.startswith(("//", "*")):
            return True
        return False

    def flush_pending():
        while pending and not pending[-1].strip():
            pending.pop()
        return pending

    for raw in src.split("\n"):
        line = raw.rstrip()
        if not in_func:
            if _starts_function(line):
                in_func = True
                func_buf = flush_pending() + [line]
                pending = []
                depth += line.count("{") - line.count("}")
                m = re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line.lstrip())
                current_name = m.group(1) if m else None
                if "{" not in line:
                    continue
            else:
                if is_comment_line(line) or not line.strip():
                    pending.append(line)
                else:
                    if pending:
                        preamble.extend(pending)
                        pending = []
                    preamble.append(line)
                continue
        else:
            func_buf.append(line)
            depth += line.count("{") - line.count("}")
        if in_func and depth == 0 and "{" in "".join(func_buf):
            funcs.append((current_name, "\n".join(func_buf)))
            in_func = False
            depth = 0
            func_buf = []
            current_name = None
    if pending:
        preamble.extend(pending)
    return preamble, funcs


def _union(lines, keep_blank_floor=0):
    merged = []
    blank = 0
    for ln in lines:
        if not ln.strip():
            blank += 1
            if blank <= keep_blank_floor:
                merged.append(ln)
            continue
        blank = 0
        merged.append(ln)
    return "\n".join(merged)


def extract_by_module():
    """-> { 'board.c': (preamble, {name: code}) , ... }"""
    out = {}
    for module in D.MODULES:
        fname = module[0]
        with open(fname, encoding="utf-8-sig", errors="replace") as f:
            src = f.read()
        preamble, funcs = split_functions(src)
        by_name = {}
        for name, code in funcs:
            if name:
                by_name.setdefault(name, []).append(code)
        out[fname] = (preamble, {k: "\n".join(v) for k, v in by_name.items()})
    return out


if __name__ == "__main__":
    data = extract_by_module()
    fmap = {m[0]: m[2] for m in D.MODULES}
    for fname, (pre, by_name) in data.items():
        doc_names = [fn[0] for fn in fmap[fname]]
        missing = [n for n in doc_names if n not in by_name]
        extra = sorted(n for n in by_name if n not in doc_names)
        print("%-12s found=%d doc=%d pre-lines=%d  MISSING=%s EXTRAS=%s" % (
            fname, len(by_name), len(doc_names), len(pre), missing, extra))