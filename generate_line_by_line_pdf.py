# -*- coding: utf-8 -*-
"""MONOPOLY_LK_Code_Line_By_Line.pdf

Documentation sorted by .c / .h file (main topics), function by function
(sub topics). Each function shows its original source line number, the full
function pasted verbatim, then a LINE-BY-LINE explanation, the nested
functions to study, and the main purpose.

Two passes: the first pass measure page numbers of every heading, the second
pass renders the final document (cover + TOC + body) using those numbers.
Sub-index layouts are width-stable so both passes paginate identically.
"""

import math
import os
import re
from fpdf import FPDF

import code_docs_data as DATA
from extract_code import extract_by_module

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "MONOPOLY_LK_Code_Line_By_Line.pdf")
FONT_DIR = r"C:\Windows\Fonts"

NAVY = (16, 42, 92)
TEAL = (14, 116, 120)
INDIGO = (72, 61, 139)
SLATE = (31, 45, 61)
GRAY = (100, 116, 139)
CODE_BG = (250, 250, 252)
MUTED = (71, 85, 105)

A4W, A4H = 210, 297

FILE_OVERVIEW = {
    "types.h": "Shared header: every compile-time constant (#define), every enum "
               "and every struct used by all modules.",
    "functions.h": "Project API header: one prototype for every function, grouped "
                   "by the .c file that implements it.",
    "main.c": "Entry point. Creates the single GameState (array-of-one idiom) and "
              "starts the whole simulation.",
    "board.c": "Builds the 40-square Sri Lanka board: special squares, railways, "
               "utilities and the 22 colour-group properties.",
    "players.c": "The four AI strategies (Aggressive Investor, Risk Taker, "
                 "Opportunistic Trader, Conservative Banker) and every "
                 "'should / wants' decision.",
    "game.c": "The game engine: turn loop, dice, movement, jail, round flow, "
              "buying, mortgage decisions, building, selling, anti-speculation, "
              "winner detection.",
    "finance.c": "All money movement: buying, rent, taxes, mortgages, buildings, "
                 "net worth, selling, forced sales, the Anti-Speculation Act.",
    "bank.c": "Loans: borrowing, repayment, extension, refinancing, foreclosure, "
              "collateral, the Bank square visit.",
    "auction.c": "The auction engine (Rule-LK 19-23): starting price, bidding "
                 "rounds, withdrawal, forced-sale handling.",
    "events.c": "National Event Cards, economic events (every 15 rounds) and "
                "government regulations (every 20 rounds).",
    "economy.c": "Inflation, the timed-modifier economy, ageing/depreciation, "
                 "maintenance, repairs and the shared value math.",
    "insurance.c": "Insurance policies, disasters, compensation, repairs, policy "
                   "renewal and expiry.",
    "market.c": "Property market reviews (boom/decline every 10 rounds), cooldowns, "
                "Regional Development cards and the market display.",
}

MAIN_ORDER = [
    "types.h", "functions.h",
    "board.c", "players.c", "game.c", "finance.c", "bank.c", "auction.c",
    "events.c", "economy.c", "insurance.c", "market.c", "main.c",
]

# struct field meanings keyed by field name
_FIELD_MEANING = {}
for _s, _fields in DATA.STRUCTS.items():
    for _f, _t, _d in _fields:
        _FIELD_MEANING[_f] = _d

_FUNC_PURPOSE = {}
for _m in DATA.MODULES:
    for _f in _m[2]:
        _FUNC_PURPOSE[_f[0]] = _f[2]


def _purpose_of(funcname):
    return _FUNC_PURPOSE.get(funcname, "")


def find_nested_calls(code):
    known = set(_FUNC_PURPOSE)
    out, seen = [], set()
    for m in re.finditer(r"(?<![\w.])([A-Za-z_]\w*)\s*\(", code):
        nm = m.group(1)
        if nm in known and nm not in seen:
            seen.add(nm)
            out.append(nm)
    return out


# --------------------------------------------------------------------------
# line-by-line explanation engine
# --------------------------------------------------------------------------

def explain_statement(line):
    L = line.strip()
    if not L:
        return "Blank line."
    if re.match(r"^/\*", L) or L.startswith("*") or L.startswith("//"):
        return "Comment: " + L
    if L.startswith("#include"):
        return "Includes " + L.split()[1] + "."
    if L.startswith("#define"):
        m = re.match(r"#define\s+(\w+)\s+(.*)", L)
        if m:
            desc = ""
            for _n, _v, _c, _d in DATA.MACROS:
                if _n == m.group(1):
                    desc = "  (" + _d + ")"
                    break
            return "Defines macro %s = %s%s." % (m.group(1), m.group(2), desc)
        return "Preprocessor directive."
    if L.startswith("typedef"):
        return "Type definition (see the enum/struct tables in this section)."
    if L == "{":
        return "Opens a new block."
    if L == "}":
        return "Closes the current block."
    if L in ("else", "else {"):
        return "The alternative branch when the condition above is false."
    if re.match(r"^else\s+if", L):
        return "A further condition checked only if the previous one failed."
    if re.match(r"^case\s+[A-Za-z_]\w*\s*:", L):
        return "This case of the switch runs when its constant matches."
    if re.match(r"^default\s*:", L):
        return "The fallback switch branch when no case matched."
    if L in ("break;", "break"):
        return "Breaks out of the current loop or switch."
    if L in ("continue;", "continue"):
        return "Skips to the next loop iteration."
    if re.match(r"^return\b", L):
        expr = L[6:].rstrip(";").strip()
        return "Returns " + _expr_text(expr) + " immediately."
    if re.match(r"^printf\s*\(", L):
        m = re.match(r'^printf\s*\(\s*"(.*?)"(.*)$', L, re.S)
        if m:
            outer = "Prints the message \"%s\"." % m.group(1)[:60]
            fm = re.search(r"formatLKR\s*\(([^)]+)\)", m.group(2))
            if fm:
                outer = outer[:-1] + "  (formats %s as comma-separated LKR)." % fm.group(1).strip()
            return outer
        return "Prints a formatted message."
    if re.match(r"^puts\s*\(", L):
        return "Prints a plain string followed by a newline."
    if re.match(r"^if\s*\(", L) or re.match(r"^else\s+if\s*\(", L):
        cond = _paren_inner(L)
        return "Condition: %s  ->  run the next block if true." % _condition_text(cond)
    if re.match(r"^for\s*\(", L):
        c = _paren_inner(L)
        parts = [p.strip() for p in c.split(";")]
        while len(parts) < 3:
            parts.append("")
        s = "Loop over all entries: init %s; run while %s; every loop %s." % (
            parts[0], parts[1], parts[2])
        return s
    if re.match(r"^while\s*\(", L):
        c = _paren_inner(L)
        return "Loop: repeat while %s is true." % _condition_text(c)
    if re.match(r"^switch\s*\(", L):
        c = _paren_inner(L)
        return "Chooses a branch based on the value of %s." % _condition_text(c)
    m = re.match(r"^(\w+(?:\[[^]]+\])?(?:\.\w+(?:\[[^]]+\])?)+)\s*(\+=|-=|\*=|/=|%=|=)\s*(.*?);?\s*$", L)
    if m:
        lhs, op, rhs = m.group(1), m.group(2), m.group(3).rstrip(";").strip()
        ld = _lhs_text(lhs)
        rv = _expr_text(rhs)
        if op == "=":
            return "Sets %s  =  %s." % (ld, rv)
        opword = {"+=": "increases it by", "-=": "decreases it by",
                  "*=": "multiplies it by", "/=": "divides it by",
                  "%=": "computes its remainder with"}.get(op, op)
        return "Updates %s: %s %s." % (ld, opword, rv)
    m = re.match(r"^([A-Za-z_]\w*)\s*\((.*)\)\s*;?$", L, re.S)
    if m:
        args = [a.strip() for a in m.group(2).split(",") if a.strip()]
        pur = _purpose_of(m.group(1))
        base = "Calls %s(%s)." % (m.group(1), ", ".join(args))
        if pur:
            return base + "  (%s)" % pur.split(".")[0]
        return base
    # plain declaration
    if re.match(r"^(int|double|float|char|long|unsigned|short)", L) and L.endswith(";"):
        return "Declares %s." % L.rstrip(";").strip()
    return L


def _paren_inner(L):
    idx1 = L.find("(")
    idx2 = L.rfind(")")
    if idx1 > -1 and idx2 > idx1:
        return L[idx1 + 1:idx2]
    return ""


def _expr_text(e):
    e = (e or "").strip()
    if not e:
        return "the computed value"
    return e


def _condition_text(c):
    c = (c or "").strip()
    subs = (
        ("game[0].players[playerIndex]", "the current player"),
        ("game[0].players[highBidder]", "the highest current bidder"),
        ("game[0].players[winner]", "the winner"),
        ("game[0].players[i]", "player i"),
        ("game[0].board[propIndex]", "this property"),
        ("game[0].board[index]", "this square"),
        ("game[0].board[i]", "square i"),
        ("game[0].economy.inflationRate", "current inflation"),
    )
    for _f, _r in subs:
        c = c.replace(_f, _r)
    return c[:90]


def _lhs_text(lhs):
    field = None
    for tok in re.findall(r"\.([A-Za-z_]\w*)", lhs):
        if tok in _FIELD_MEANING:
            field = tok
    if field and field != "name":
        loc = ""
        if "players" in lhs:
            loc = " of the player"
        elif "board" in lhs and ".property" in lhs:
            loc = " of the property on the board"
        elif "board" in lhs:
            loc = " of the square on the board"
        elif "economy" in lhs:
            loc = " of the shared economy"
        elif ".loan" in lhs:
            loc = " of the player's loan"
        return "the field %s%s (i.e. %s)" % (field, loc, _FIELD_MEANING[field][:80])
    return "the value at " + lhs[:60]


# --------------------------------------------------------------------------
# PDF machinery
# --------------------------------------------------------------------------

class LineByLine(FPDF):
    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.toc_entries = []
        self.reg = {}
        self.l_margin = 14
        self.r_margin = 14
        self.t_margin = 16
        self.b_margin = 16
        self.set_margins(self.l_margin, self.t_margin, self.r_margin)
        self.set_auto_page_break(True, self.b_margin)
        self.add_font("Arial", "", os.path.join(FONT_DIR, "arial.ttf"))
        self.add_font("Arial", "B", os.path.join(FONT_DIR, "arialbd.ttf"))
        self.add_font("Arial", "I", os.path.join(FONT_DIR, "ariali.ttf"))
        self.add_font("Arial", "BI", os.path.join(FONT_DIR, "arialbi.ttf"))

    def footer(self):
        self.set_y(-14)
        self.set_font("Arial", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 8, "MONOPOLY.LK  |  Line-by-Line Code Explanation  |  Page %d" %
                  self.page_no(), align="C")

    def h1(self, num, text):
        self.add_page()
        self.set_fill_color(*NAVY)
        self.rect(0, 0, A4W, 21, "F")
        self.set_font("Arial", "B", 15)
        self.set_text_color(255, 255, 255)
        self.set_y(6.2)
        self.cell(0, 8, "%s    %s" % (num, text))
        self.set_y(25)
        self.set_text_color(15, 23, 42)
        self.toc_entries.append((text, 0, self.page_no()))

    def h2(self, title, record=True, key=None):
        if self.get_y() > self.h - self.b_margin - 20:
            self.add_page()
        self.ln(1)
        self.set_font("Arial", "B", 12)
        self.set_text_color(*TEAL)
        self.cell(0, 7, title)
        self.ln(7)
        self.set_text_color(15, 23, 42)
        if key:
            self.reg[key] = self.page_no()
        if record:
            self.toc_entries.append((title, 1, self.page_no()))

    def h3(self, title):
        if self.get_y() > self.h - self.b_margin - 16:
            self.add_page()
        self.ln(1)
        self.set_font("Arial", "B", 10.5)
        self.set_text_color(*INDIGO)
        self.cell(0, 6, title)
        self.ln(6)
        self.set_text_color(15, 23, 42)

    def para(self, text, size=9.2):
        self.set_font("Arial", "", size)
        self.multi_cell(self.w - self.l_margin - self.r_margin, 4.9, text, align="J")
        self.ln(1)

    def note(self, text):
        self.set_font("Arial", "I", 8.3)
        self.set_text_color(*MUTED)
        self.multi_cell(self.w - self.l_margin - self.r_margin, 4.3, text, align="J")
        self.set_text_color(15, 23, 42)
        self.ln(1)

    def sig_banner(self, text):
        cw = self.w - self.l_margin - self.r_margin
        rows = []
        for raw in text.split("\n"):
            while self.get_string_width(raw) > cw - 6:
                cut = len(raw) - 1
                while cut > 0 and self.get_string_width(raw[:cut]) > cw - 6:
                    cut -= 1
                rows.append(raw[:cut])
                raw = raw[cut:]
            rows.append(raw)
        h = len(rows) * 4.8 + 3
        if self.get_y() + h > self.h - self.b_margin:
            self.add_page()
        y0 = self.get_y()
        self.set_fill_color(*CODE_BG)
        self.set_draw_color(*SLATE)
        self.rect(self.l_margin, y0, cw, h, "DF")
        self.set_font("Courier", "", 8.4)
        self.set_text_color(*NAVY)
        y = y0 + 1.5
        for ln in rows:
            self.set_xy(self.l_margin + 3, y)
            self.cell(cw - 6, 4.8, ln)
            y += 4.8
        self.set_y(y + 0.6)

    def code_lines(self, code, start_line, title=""):
        cw = self.w - self.l_margin - self.r_margin
        if title:
            self.set_font("Arial", "B", 8.6)
            self.set_text_color(*TEAL)
            self.cell(0, 5.4, title)
            self.ln(5.6)
            self.set_text_color(15, 23, 42)
        gutter = 11
        pad = 3
        self.set_font("Courier", "", 7.0)
        lh = 3.8
        view = []
        lines = code.split("\n")
        for i, raw in enumerate(lines):
            lineno = start_line + i
            if raw.strip() == "":
                view.append((None, ""))
                continue
            t = raw.replace("\t", "    ")
            while self.get_string_width(t) > cw - gutter - 2 * pad:
                cut = len(t) - 1
                while cut > 0 and self.get_string_width(t[:cut]) > cw - gutter - 2 * pad:
                    cut -= 1
                view.append((lineno, t[:cut]))
                t = t[cut:]
            view.append((lineno, t))
        i = 0
        while i < len(view):
            if self.get_y() > self.h - self.b_margin - 2:
                self.add_page()
            y0 = self.get_y()
            avail = self.h - self.b_margin - y0 - 1
            fit = int(avail // lh)
            if fit <= 0:
                self.add_page()
                continue
            chunk = view[i:i + fit]
            h = len(chunk) * lh + 1.2
            self.set_fill_color(*CODE_BG)
            self.set_draw_color(203, 213, 225)
            self.rect(self.l_margin, y0, cw, h, "DF")
            y = y0 + 0.8
            for lineno, txt in chunk:
                self.set_font("Courier", "", 6.4)
                self.set_text_color(*GRAY)
                self.set_xy(self.l_margin + pad, y)
                self.cell(gutter, lh, str(lineno) if lineno else "")
                self.set_font("Courier", "", 7.0)
                self.set_text_color(*SLATE)
                self.cell(cw - gutter - 2 * pad, lh, txt)
                y += lh
            self.set_y(y + 0.8)
            i += fit

    def _wrap_fit(self, text, font, style, size, width):
        lines = []
        for chunk in str(text).split("\n"):
            cur = ""
            for word in chunk.split(" "):
                if not word:
                    continue
                guest = (cur + " " + word).strip() if cur else word
                if self.get_string_width(guest) <= width:
                    cur = guest
                    continue
                if cur:
                    lines.append(cur)
                    cur = ""
                w = word
                while w and self.get_string_width(w) > width:
                    cut = len(w) - 1
                    while cut > 0 and self.get_string_width(w[:cut]) > width:
                        cut -= 1
                    if cut <= 0:
                        cut = 1
                    lines.append(w[:cut])
                    w = w[cut:]
                cur = w
            lines.append(cur)
        if not lines:
            lines.append("")
        return lines

    def table_row(self, x0, cols, texts, lh=4.5):
        wraps = []
        n = 1
        for (w, (font, style, size, align)), txt in zip(cols, texts):
            content = txt if txt else ""
            if align == "L":
                content = (" " + content) if content else content
            self.set_font(font, style, size)
            ls = self._wrap_fit(content, font, style, size, w - 2 * self.c_margin)
            wraps.append((align, ls))
            n = max(n, len(ls))
        hgt = lh * n
        y0 = self.get_y()
        if y0 + hgt > self.h - self.b_margin:
            self.add_page()
            y0 = self.get_y()
        x = x0
        tw = 0
        for w, _c in cols:
            tw += w
        for (w, (font, style, size, align)), (align2, ls) in zip(cols, wraps):
            self.set_font(font, style, size)
            k = 0
            for line in ls:
                if k >= n:
                    break
                self.set_xy(x, y0 + k * lh)
                self.cell(w, lh, line, 0, 0, align2, False)
                k += 1
            x += w
        self.set_xy(x0, y0 + hgt + 0.1)
        return hgt

    def explain_table(self, rows):
        cw = self.w - self.l_margin - self.r_margin
        colw = [11, 78, cw - 89]
        cols = [(colw[0], ("Arial", "B", 8.0, "C")),
                (colw[1], ("Courier", "", 6.8, "L")),
                (colw[2], ("Arial", "", 7.8, "L"))]
        self.set_font("Arial", "B", 8.0)
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        self.cell(colw[0], 5.6, "Line", 0, 0, "C", True)
        self.cell(colw[1], 5.6, "  Code", 0, 0, "L", True)
        self.cell(colw[2], 5.6, "Explanation", 0, 0, "L", True)
        self.ln(5.6)
        self.set_text_color(20, 20, 20)
        for i, (lineno, code, expl) in enumerate(rows):
            self.table_row(self.l_margin, cols, [str(lineno), code, expl])
        self.ln(2)

    def purpose_box(self, text):
        cw = self.w - self.l_margin - self.r_margin
        if self.get_y() > self.h - self.b_margin - 16:
            self.add_page()
        y0 = self.get_y()
        rows = []
        for raw in text.split("\n"):
            while self.get_string_width(raw) > cw - 8:
                cut = len(raw) - 1
                while cut > 0 and self.get_string_width(raw[:cut]) > cw - 8:
                    cut -= 1
                rows.append(raw[:cut])
                raw = raw[cut:]
            rows.append(raw)
        h = len(rows) * 4.4 + 3
        self.set_fill_color(240, 253, 244)
        self.set_draw_color(22, 130, 84)
        self.rect(self.l_margin, y0, cw, h, "DF")
        self.set_font("Arial", "B", 8.8)
        self.set_text_color(6, 78, 52)
        self.set_xy(self.l_margin + 3, y0 + 1.2)
        self.cell(cw - 6, 4.4, "MAIN PURPOSE")
        self.set_font("Arial", "", 8.6)
        y = y0 + 1.2 + 4.6
        for ln in rows:
            self.set_xy(self.l_margin + 3, y)
            self.cell(cw - 6, 4.4, ln)
            y += 4.4
        self.set_y(y + 0.8)


# --------------------------------------------------------------------------
# renderers
# --------------------------------------------------------------------------

def render_header_file(pdf, fname):
    pdf.para(FILE_OVERVIEW[fname])
    if fname == "types.h":
        render_types(pdf)
    else:
        render_function_prototypes(pdf)


def render_types(pdf):
    pdf.h2("What is inside types.h", key=("types.h", "overview"))
    pdf.para("Everything here is shared state. The #define values are the rule "
             "numbers made concrete, the enums give readable names to numbers, "
             "and the structs are the actual variables the game mutates. Read the "
             "structs carefully: every function in every .c file works by reading "
             "and writing exactly these fields.")
    pdf.h2("A.  The #define constants", key=("types.h", "defines"))
    pdf.para("Every compile-time constant used across the game, with its meaning "
             "and the rule it belongs to. These values are what the viva examiner "
             "will pick from: know why each number exists.")
    rows = []
    with open("types.h", encoding="utf-8-sig") as f:
        for i, raw in enumerate(f, 1):
            if raw.strip().startswith("#define"):
                rows.append((i, raw.strip(), explain_statement(raw)))
    pdf.explain_table(rows)
    pdf.h2("B.  The enums", key=("types.h", "enums"))
    for ename, vals in DATA.ENUMS.items():
        pdf.h3("enum %s" % ename)
        src = _enum_source(ename)
        pdf.code_lines(src, _enum_source_line(ename), title="Original code:")
        cw = pdf.w - pdf.l_margin - pdf.r_margin
        pdf.set_font("Arial", "B", 8.2)
        pdf.cell(cw * 0.30, 5.4, "  Value", fill=True)
        pdf.cell(cw * 0.70, 5.4, "  Meaning", fill=True)
        pdf.ln(5.4)
        for i, (v, d) in enumerate(vals):
            if pdf.get_y() > pdf.h - pdf.b_margin - 9:
                pdf.add_page()
            fill = i % 2 == 0
            pdf.set_font("Courier", "B", 8.0)
            pdf.cell(cw * 0.30, 4.6, "  " + v, fill=fill)
            pdf.set_font("Arial", "", 8.0)
            pdf.cell(cw * 0.70, 4.6, "  " + d, fill=fill)
            pdf.ln(4.6)
        pdf.ln(1)
    pdf.h2("C.  The structs", key=("types.h", "structs"))
    for sname, fields in DATA.STRUCTS.items():
        pdf.h3("struct %s" % sname)
        src = _struct_source(sname)
        pdf.code_lines(src, _struct_source_line(sname), title="Original code:")
        cw = pdf.w - pdf.l_margin - pdf.r_margin
        colw = [44, 24, cw - 72]
        cols = [(colw[0], ("Courier", "B", 7.8, "L")),
                (colw[1], ("Courier", "", 7.8, "L")),
                (colw[2], ("Arial", "", 7.8, "L"))]
        pdf.set_font("Arial", "B", 8.2)
        pdf.cell(colw[0], 5.4, "  Field", fill=True)
        pdf.cell(colw[1], 5.4, "  Type", fill=True)
        pdf.cell(colw[2], 5.4, "  Purpose", fill=True)
        pdf.ln(5.4)
        for f, t, d in fields:
            pdf.table_row(pdf.l_margin, cols, [f, t, d], lh=4.6)
        pdf.ln(1)


def render_function_prototypes(pdf):
    pdf.h2("Function prototypes grouped by implementation file",
           key=("functions.h", "overview"))
    pdf.para("functions.h declares the API. Each block below is one source file. "
             "Read the grouping to see the module boundaries of the project - "
             "this is exactly the structure the sections of this document follow.")
    rows = []
    group = "general"
    with open("functions.h", encoding="utf-8-sig") as f:
        for i, raw in enumerate(f, 1):
            s = raw.strip()
            if s.startswith("/*") and "*/" in s:
                g = s.replace("/*", "").replace("*/", "").strip()
                if g:
                    group = g
            if s and not s.startswith(("#", "/*", "*", )):
                rows.append((i, s if s.endswith(";") else s.rstrip(),
                             "Declared in functions.h; implemented in %s.c - see that section." % group))
    pdf.explain_table(rows)


def render_c_file(pdf, fname, source_map, offset):
    module = None
    for m in DATA.MODULES:
        if m[0] == fname:
            module = m
            break
    funcs = module[2]
    pre, by_name = source_map[fname]

    pdf.para(FILE_OVERVIEW[fname])
    pdf.para("The sub-topics below are the %d functions implemented in %s. "
             "Each one is shown with its original source line number, the exact "
             "code, a line-by-line explanation, the nested functions to study and "
             "its main purpose." % (len(funcs), fname))

    # ---- index of topics & sub-topics BEFORE the sub-topics ----
    pdf.h2("Index of sub-topics in %s" % fname, record=False)
    for idx, fn in enumerate(funcs, 1):
        name = fn[0]
        start = _func_start(fname, name, source_map)
        page = pdf.reg.get((fname, name), 0) + offset
        line = "%d.%d   %s()   (source line %d)" % (MAIN_ORDER.index(fname) + 1, idx,
                                                    name, start)
        pdf.set_font("Courier", "", 8.4)
        pdf.set_text_color(*SLATE)
        avail = 96 - len(" ....  p. %d" % page)
        if len(line) > avail:
            line = line[:avail - 2] + ".."
        pdf.cell(0, 5, line + " " * max(1, avail - len(line)) + "p. %d" % page)
        pdf.ln(5)
        pdf.set_text_color(15, 23, 42)
    pdf.ln(1)

    # ---- sub-topics ----
    for idx, fn in enumerate(funcs, 1):
        name, sig, purpose, params, ret, locals_, logic = fn
        start = _func_start(fname, name, source_map)
        pdf.h2("%d.%d   %s()" % (MAIN_ORDER.index(fname) + 1, idx, name),
               key=(fname, name))
        pdf.sig_banner(sig)
        pdf.note("Parameters: " + (", ".join(p[0] for p in params) if params else "none")
                 + "     |     Returns: " + ret)
        code = by_name.get(name, "")
        pdf.h3("The function, verbatim from the source (starts at line %d)" % start)
        pdf.code_lines(code, start)
        pdf.h3("Line-by-line explanation")
        rows = [(start + i, raw, explain_statement(raw))
                for i, raw in enumerate(code.split("\n"))]
        pdf.explain_table(rows)
        calls = find_nested_calls(code)
        if calls:
            pdf.h3("Nested functions inside %s()  -  study these" % name)
            for c in calls:
                pdf.set_font("Arial", "", 8.6)
                pdf.set_text_color(*INDIGO)
                pdf.cell(0, 5, "  -  %s()   (%s)" % (c, _purpose_of(c)[:90]))
                pdf.ln(5)
                pdf.set_text_color(15, 23, 42)
            pdf.ln(1)
        pdf.purpose_box(purpose)
        pdf.ln(2)


def render_toc(pdf, entries, offset):
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 9, "Table of Contents")
    pdf.ln(11)
    pdf.set_text_color(15, 23, 42)
    for title, lvl, page in entries:
        disp = page + offset
        indent = "        " if lvl else ""
        pdf.set_font("Courier", "B", 9 if not lvl else 8.4)
        core = indent + title
        pstr = str(disp)
        avail = 93 - len(pstr) - 2
        if len(core) > avail:
            core = core[:avail - 2] + ".."
        line = core + "." * max(0, avail - len(core))
        if pdf.get_y() > pdf.h - pdf.b_margin - 8:
            pdf.add_page()
        pdf.cell(0, 5, line + "  " + pstr)
        pdf.ln(5)


# --------------------------------------------------------------------------
# helpers for types.h enums/structs source lines
# --------------------------------------------------------------------------

_ENUM_SRC = {}
_STRUCT_SRC = {}


def _load_types_source():
    with open("types.h", encoding="utf-8-sig") as f:
        lines = f.readlines()
    i = 0
    n = len(lines)
    while i < n:
        L = lines[i]
        if L.strip().startswith("typedef enum") or L.strip().startswith("enum "):
            j = i
            depth = 0
            buf = []
            while j < n:
                buf.append(lines[j].rstrip("\n"))
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0 and "}" in lines[j]:
                    break
                j += 1
            name = re.search(r"}\s*(\w+)\s*;", "".join(buf))
            if name:
                _ENUM_SRC[name.group(1)] = (i + 1, "\n".join(buf))
            i = j + 1
            continue
        if lines[i].strip().startswith("typedef struct"):
            j = i
            depth = 0
            buf = []
            while j < n:
                buf.append(lines[j].rstrip("\n"))
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0 and "}" in lines[j]:
                    break
                j += 1
            name = re.search(r"}\s*(\w+)\s*;", "".join(buf))
            if name:
                _STRUCT_SRC[name.group(1)] = (i + 1, "\n".join(buf))
            i = j + 1
            continue
        i += 1


_load_types_source()


def _enum_source(ename):
    return _ENUM_SRC.get(ename, (0, ""))[1]


def _enum_source_line(ename):
    return _ENUM_SRC.get(ename, (0, ""))[0]


def _struct_source(sname):
    return _STRUCT_SRC.get(sname, (0, ""))[1]


def _struct_source_line(sname):
    return _STRUCT_SRC.get(sname, (0, ""))[0]


def _func_start(fname, name, source_map):
    pre, by_name = source_map[fname]
    code = by_name.get(name, "")
    if not code:
        return 0
    with open(fname, encoding="utf-8-sig", errors="replace") as f:
        full = f.read()
    idx = full.find(code)
    if idx > -1:
        return full[:idx].count("\n") + 1
    return 0


# --------------------------------------------------------------------------
# main / two-pass driver
# --------------------------------------------------------------------------

def render_body(pdf, source_map, offset=0):
    for i, fname in enumerate(MAIN_ORDER, 1):
        pdf.h1("Part %d" % i, fname)
        if fname == "types.h" or fname == "functions.h":
            render_header_file(pdf, fname)
        else:
            render_c_file(pdf, fname, source_map, offset)


def main():
    source_map = extract_by_module()

    # pass 1: measure page numbers
    measure = LineByLine()
    render_body(measure, source_map, offset=0)
    entries = list(measure.toc_entries)
    reg = dict(measure.reg)

    # probe the exact cover + TOC length (index lines are width-stable, so the
    # TOC always paginates identically regardless of the numbers it carries)
    toc_probe = LineByLine()
    render_cover(toc_probe)
    render_toc(toc_probe, entries, offset=0)
    offset = toc_probe.page_no()  # cover + TOC pages = body page shift
    toc_pages = max(0, offset - 1)

    # pass 2: final render
    final = LineByLine()
    final.reg = reg
    render_cover(final)
    render_toc(final, entries, offset=offset)
    render_body(final, source_map, offset=offset)
    final.output(OUT)
    print("PDF written: %s" % OUT)
    print("Pages: %d (TOC pages: %d)" % (final.page_no(), toc_pages))


def render_cover(pdf):
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, A4W, A4H, "F")
    pdf.set_text_color(245, 248, 255)
    pdf.set_font("Arial", "B", 28)
    pdf.set_y(64)
    pdf.cell(0, 12, "MONOPOLY.LK", align="C")
    pdf.ln(14)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 7, "A Sri Lanka themed Monopoly simulation in C", align="C")
    pdf.ln(16)
    pdf.set_font("Arial", "B", 17)
    pdf.set_text_color(125, 211, 252)
    pdf.cell(0, 9, "Line-by-Line Code Explanation", align="C")
    pdf.ln(7)
    pdf.set_font("Arial", "", 10.5)
    pdf.set_text_color(203, 213, 225)
    pdf.cell(0, 6, "Every function from every source file, explained line by line", align="C")
    pdf.ln(12)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 6, "Generated from the actual source code, with original line numbers", align="C")


if __name__ == "__main__":
    main()