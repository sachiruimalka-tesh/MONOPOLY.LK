#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the MONOPOLY.LK viva-preparation PDF study guide.

Reads the actual source files when building the appendix, so every code
listing in the PDF is guaranteed to match the current project.

Requirements:  pip install fpdf2
Run:           python generate_viva_pdf.py
Output:        MONOPOLY_LK_Viva_Guide.pdf
"""

import io
import math
import os
import re

from fpdf import FPDF

ROOT = os.path.dirname(os.path.abspath(__file__))

FONT_DIR = r"C:\Windows\Fonts"
ARIAL = os.path.join(FONT_DIR, "arial.ttf")
ARIAL_B = os.path.join(FONT_DIR, "arialbd.ttf")
ARIAL_I = os.path.join(FONT_DIR, "ariali.ttf")
ARIAL_BI = os.path.join(FONT_DIR, "arialbi.ttf")
NIRMALA = os.path.join(FONT_DIR, "Nirmala.ttc")

TOC_MAX_CHARS = 88          # monospace chars per TOC line (Courier 9pt)
CODE_COLS = 100             # max code chars per display line (Courier 7.5pt -> ~117 fit)
CODE_LH = 3.4               # line height mm for 7.5pt Courier

NAVY = (16, 48, 96)
LIGHT_FILL = (233, 239, 249)
ACCENT = (216, 228, 244)
HINT_FILL = (244, 240, 220)
GRAY = (100, 100, 100)

TOKEN_RE = re.compile(
    r"""
    ( //.*$                                  # line comment
    | \b\d+(?:\.\d+)?\b                      # number
    | "(?:[^"\\]|\\.)*"                      # string literal
    | '(?:[^'\\]|\\.)'                       # char literal
    | \b(?:int|void|char|if|else|return|for|while|do|switch|case|break|
          continue|default|struct|enum|typedef|static|const|unsigned|signed|
          long|short|extern|volatile|sizeof|union|double|float)\b
    )
    """,
    re.VERBOSE,
)

KEYWORD_GREEN = (0, 128, 0)
STRING_RED = (150, 43, 43)
NUMBER_BLUE = (60, 60, 160)
KEYWORD_NAVY = (24, 24, 130)
PREPROC_GRAY = (140, 140, 140)
CODE_BLACK = (30, 30, 30)

# -- callout boxes (WHY / WHAT / LOGIC) -----------------------------------
EXPLAIN_WHY_FILL = (215, 228, 245)
EXPLAIN_WHY_EDGE = (40, 90, 160)
EXPLAIN_WHY_LBL = (20, 60, 130)
EXPLAIN_WHAT_FILL = (222, 240, 222)
EXPLAIN_WHAT_EDGE = (50, 130, 70)
EXPLAIN_WHAT_LBL = (20, 90, 45)
EXPLAIN_LOGIC_FILL = (250, 242, 212)
EXPLAIN_LOGIC_EDGE = (170, 120, 30)
EXPLAIN_LOGIC_LBL = (120, 80, 10)

# -- colour palette for the code tree diagram -----------------------------
TREE_NAVY = (16, 48, 96)
TREE_TEAL = (0, 116, 128)
TREE_GREEN = (34, 120, 70)
TREE_ORANGE = (168, 100, 20)
TREE_PURPLE = (110, 70, 150)
TREE_FILL_T = (224, 240, 242)
TREE_FILL_G = (226, 240, 228)
TREE_FILL_O = (246, 236, 222)
TREE_FILL_P = (238, 230, 246)
TREE_DARK_T = (10, 70, 78)
TREE_DARK_G = (16, 70, 36)
TREE_DARK_O = (100, 58, 8)
TREE_DARK_P = (70, 38, 100)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def wrap_code(line, limit=CODE_COLS):
    """Split a code line into display lines of at most `limit` chars,
    preferring to break on spaces."""
    if len(line) <= limit:
        return [line]
    parts = []
    while len(line) > limit:
        chunk = line[:limit]
        cut = chunk.rfind(" ")
        if cut > limit // 2:
            parts.append(line[:cut].rstrip())
            line = line[cut + 1:]
        else:
            parts.append(line[:limit])
            line = line[limit:]
    parts.append(line)
    return parts


def read_file(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8-sig", errors="replace") as f:
        return f.read()


# --------------------------------------------------------------------------
# PDF subclass
# --------------------------------------------------------------------------

class Guide(FPDF):
    def __init__(self, **kw):
        super().__init__(orientation="P", unit="mm", format="A4", **kw)
        self.add_font("Arial", "", ARIAL)
        self.add_font("Arial", "B", ARIAL_B)
        self.add_font("Arial", "I", ARIAL_I)
        self.add_font("Arial", "BI", ARIAL_BI)
        self.add_font("Nirmala", "", NIRMALA)
        self.recording = False
        self.toc_entries = []
        self.set_margins(13, 16, 13)
        self.set_auto_page_break(auto=True, margin=16)
        self.tsize = 10          # current table font size, set by table()

    def footer(self):
        if self.page_no() <= 1:
            return
        self.set_y(-13)
        self.set_font("Arial", "", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 6, "MONOPOLY.LK  |  Viva Preparation Guide  |  Page %d"
                  % self.page_no(), align="C")

    # -- structure ---------------------------------------------------------

    def h1(self, num, title):
        self.add_page()
        self.set_font("Arial", "B", 15)
        self.set_text_color(*NAVY)
        self.cell(0, 8, "%s   %s" % (num, title), new_x="RIGHT", new_y="NEXT")
        self.ln(2.5)
        self.set_draw_color(*NAVY)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)
        self.set_text_color(25, 25, 25)
        if self.recording:
            self.toc_entries.append(("%s   %s" % (num, title), 0, self.page_no()))

    def h2(self, title, lvl=1, record=True):
        self.ln(1)
        self.set_font("Arial", "B", 12)
        self.set_text_color(*NAVY)
        self.multi_cell(0, 5.4, title, align="L")
        self.set_text_color(25, 25, 25)
        self.ln(1.2)
        if self.recording and record:
            self.toc_entries.append((title, lvl, self.page_no()))

    def h3(self, title):
        self.ln(0.5)
        self.set_font("Arial", "BI", 10.5)
        self.set_text_color(60, 60, 90)
        self.multi_cell(0, 5, title, align="L")
        self.set_text_color(25, 25, 25)
        self.ln(0.8)

    # -- text --------------------------------------------------------------

    def p(self, text, size=9.8):
        self.set_font("Arial", "", size)
        self.multi_cell(0, 5.2, text, align="J", new_x="LEFT", new_y="NEXT")
        self.ln(1.4)

    def hint(self, text):
        """A short Sinhala explanation band."""
        self.set_fill_color(*HINT_FILL)
        self.set_font("Nirmala", "", 9.3)
        self.set_text_color(70, 55, 5)
        self.multi_cell(0, 5.1, text, align="L", fill=True, new_x="LEFT", new_y="NEXT")
        self.set_text_color(25, 25, 25)
        self.ln(1.6)

    def bullets(self, items, size=9.8):
        self.set_font("Arial", "", size)
        for it in items:
            if isinstance(it, tuple):
                head, rest = it
                self.set_font("Arial", "B", size)
                self.multi_cell(0, 5.2, "  \u2022  %s" % head, align="J",
                                new_x="LEFT", new_y="NEXT")
                self.set_font("Arial", "", size)
                self.multi_cell(0, 5.2, rest, align="J", new_x="LEFT", new_y="NEXT")
            else:
                self.multi_cell(0, 5.2, "  \u2022  %s" % it, align="J",
                                new_x="LEFT", new_y="NEXT")
        self.ln(1.6)

    def numbered(self, items, size=9.8):
        self.set_font("Arial", "", size)
        for i, it in enumerate(items, 1):
            self.multi_cell(0, 5.2, "%2d.  %s" % (i, it), align="J",
                            new_x="LEFT", new_y="NEXT")
        self.ln(1.6)

    def kv(self, key, val, size=9.8):
        self.set_font("Arial", "B", size)
        self.multi_cell(0, 5.2, key, align="L", new_x="LEFT", new_y="NEXT")
        self.set_font("Arial", "", size)
        self.multi_cell(0, 5.2, val, align="L", new_x="LEFT", new_y="NEXT")
        self.ln(0.6)

    def note(self, text):
        self.set_font("Arial", "I", 9)
        self.set_text_color(*GRAY)
        self.multi_cell(0, 4.9, "[Note] " + text, align="L", new_x="LEFT", new_y="NEXT")
        self.set_text_color(25, 25, 25)
        self.ln(1.2)

    def callout(self, label, text, fill, edge, label_col, size=9.2):
        """A rounded filled box: a small bold label on top + justified body.
        Used for the WHY / WHAT / LOGIC explanation boxes after code."""
        pad = 1.8
        width = self.w - self.l_margin - self.r_margin
        w_in = width - 2 * pad
        self.set_font("Arial", "", size)
        lines = self.lines_in(text, w_in - 2, size)
        h = 4.6 + lines * (size * 0.55) + 2 * pad + 1.2
        if self.get_y() + h > self.h - self.b_margin:
            self.add_page()
        y0 = self.get_y()
        x0 = self.l_margin
        self.set_fill_color(*fill)
        self.set_draw_color(*edge)
        self.set_line_width(0.4)
        self.rect(x0, y0, width, h, "DF", round_corners=True, corner_radius=1.2)
        self.set_xy(x0 + pad, y0 + pad)
        self.set_font("Arial", "B", size - 1.0)
        self.set_text_color(*label_col)
        self.multi_cell(w_in, 4.2, label, align="L", new_x="LEFT", new_y="NEXT")
        self.set_x(x0 + pad)
        self.set_font("Arial", "", size)
        self.set_text_color(40, 40, 40)
        self.multi_cell(w_in, size * 0.55, text, align="J", new_x="LEFT", new_y="NEXT")
        self.set_y(y0 + h)
        self.ln(1.6)

    def explain(self, why, what, logic):
        """Three callout boxes: why this code exists / what each part does /
        the logic thinking behind it."""
        self.callout("WHY  this code is included", why,
                     EXPLAIN_WHY_FILL, EXPLAIN_WHY_EDGE, EXPLAIN_WHY_LBL)
        self.callout("WHAT  each part of the code does", what,
                     EXPLAIN_WHAT_FILL, EXPLAIN_WHAT_EDGE, EXPLAIN_WHAT_LBL)
        self.callout("LOGIC  the thinking behind the design", logic,
                     EXPLAIN_LOGIC_FILL, EXPLAIN_LOGIC_EDGE, EXPLAIN_LOGIC_LBL)
        self.ln(1)

    # -- code --------------------------------------------------------------

    def code_plain(self, s, style, color):
        self.set_font("Courier", style, 7.5)
        self.set_text_color(*color)
        if s:
            self.write(h=CODE_LH, text=s)
        self.ln(CODE_LH)

    def code_tokens(self, s):
        pos = 0
        for m in TOKEN_RE.finditer(s):
            if m.start() > pos:
                self.set_font("Courier", "", 7.5)
                self.set_text_color(*CODE_BLACK)
                self.write(h=CODE_LH, text=s[pos:m.start()])
            tok = m.group(1)
            if tok.startswith("//") or tok.startswith("/*"):
                self.set_font("Courier", "I", 7.5)
                self.set_text_color(*KEYWORD_GREEN)
            elif tok.startswith(("\"", "'")):
                self.set_font("Courier", "", 7.5)
                self.set_text_color(*STRING_RED)
            elif tok[0].isdigit():
                self.set_font("Courier", "", 7.5)
                self.set_text_color(*NUMBER_BLUE)
            else:
                self.set_font("Courier", "B", 7.5)
                self.set_text_color(*KEYWORD_NAVY)
            self.write(h=CODE_LH, text=tok)
            pos = m.end()
        if pos < len(s):
            self.set_font("Courier", "", 7.5)
            self.set_text_color(*CODE_BLACK)
            self.write(h=CODE_LH, text=s[pos:])
        self.ln(CODE_LH)

    def code_block(self, text, title=None):
        """A code listing always starts on a fresh page so two listings never
        share (or overwrite) a page. Title, when given, becomes a banner."""
        self.add_page()
        if title:
            self.set_fill_color(*NAVY)
            self.set_draw_color(*NAVY)
            self.set_line_width(0.5)
            self.set_font("Arial", "B", 9.5)
            self.set_text_color(255, 255, 255)
            y0 = self.get_y()
            self.set_xy(self.l_margin, y0)
            self.multi_cell(self.w - self.l_margin - self.r_margin, 5.6,
                            "  " + title, align="L")
            self.set_text_color(25, 25, 25)
            self.ln(1.2)
            if self.recording:
                self.toc_entries.append((title, 1, self.page_no()))
        else:
            self.set_line_width(0.5)
        in_comment = False
        for raw in text.splitlines():
            line = "".join(ch if ord(ch) < 256 else "?" for ch in raw)
            line = line.expandtabs(4)
            if not line:
                self.ln(CODE_LH)
                continue
            for disp in wrap_code(line):
                if in_comment:
                    end = disp.find("*/")
                    if end == -1:
                        self.code_plain(disp, "I", KEYWORD_GREEN)
                    else:
                        self.code_plain(disp[:end + 2], "I", KEYWORD_GREEN)
                        tail = disp[end + 2:]
                        if tail.strip():
                            self.code_tokens(tail)
                        else:
                            in_comment = False
                    if end != -1:
                        in_comment = False
                    continue
                if disp.lstrip().startswith("#"):
                    self.code_plain(disp, "", PREPROC_GRAY)
                    continue
                if disp.count("/*") > disp.count("*/"):
                    idx = disp.find("/*")
                    if idx > 0:
                        self.code_tokens(disp[:idx])
                    self.code_plain(disp[idx:], "I", KEYWORD_GREEN)
                    in_comment = not ("*/" in disp[idx + 2:])
                    continue
                self.code_tokens(disp)
        self.ln(2)

    # -- colourful tree diagram -------------------------------------------

    def tree_text(self, cx, cy, text, style, size, color):
        """Draw a single line of text centred horizontally at (cx, cy)."""
        self.set_font("Arial", style, size)
        self.set_text_color(*color)
        tw = self.get_string_width(text)
        self.set_xy(max(self.l_margin, cx - tw / 2), cy - size * 0.28)
        self.cell(min(tw, self.w - self.l_margin - self.r_margin),
                  size * 0.55, text, align="C")

    def tree_box(self, cx, cy, w, h, fill, edge):
        """A rounded, filled box centred at (cx, cy)."""
        self.set_fill_color(*fill)
        self.set_draw_color(*edge)
        self.set_line_width(0.4)
        self.rect(cx - w / 2, cy - h / 2, w, h, "DF",
                  round_corners=True, corner_radius=1.1)

    def code_tree(self):
        """Colourful, read-as-a-tree diagram of the whole project structure."""
        meta = [
            ("Data model", TREE_TEAL, TREE_FILL_T, TREE_DARK_T, [
                ("types.h", "361 lines - ALL constants, enums & structs"),
                ("functions.h", "184 lines - prototypes of every function"),
            ]),
            ("Core engine", TREE_GREEN, TREE_FILL_G, TREE_DARK_G, [
                ("main.c", "17 lines - entry point, creates GameState"),
                ("game.c", "640 lines - turns, rounds, dice, jail, winner"),
                ("board.c", "205 lines - builds the 40-square board"),
                ("players.c", "405 lines - the 4 AI strategies"),
            ]),
            ("Economy & rules", TREE_ORANGE, TREE_FILL_O, TREE_DARK_O, [
                ("finance.c", "1076 - money, rent, buying, mortgage"),
                ("bank.c", "394 - loans, collateral, foreclosure"),
                ("auction.c", "178 - the auction engine"),
                ("events.c", "402 - event cards & regulations"),
                ("economy.c", "503 - inflation, modifiers, ageing"),
                ("insurance.c", "392 - policies & disasters"),
                ("market.c", "430 - boom/decline & regional cards"),
            ]),
            ("Tooling & data", TREE_PURPLE, TREE_FILL_P, TREE_DARK_P, [
                ("verify_analysis.py", "1458 - the verification analyzer"),
                ("generate_viva_pdf.py", "this script - makes this guide"),
                ("Rent.csv", "23 lines - price/rent data table"),
                ("output/", "verification report"),
                ("run*.txt / test.txt", "saved game logs"),
                ("monopoly.exe", "the compiled Windows binary"),
                ("monopoly_final.zip", "the submission archive"),
            ]),
        ]
        ncols = len(meta)
        gw = (self.w - self.l_margin - self.r_margin) / ncols
        gx = [self.l_margin + gw * i + gw / 2 for i in range(ncols)]

        root_cy, root_h = 15.0, 9.0
        self.tree_box(105, root_cy, 96, root_h, TREE_NAVY, TREE_NAVY)
        self.tree_text(105, root_cy - 2.0, "MONOPOLY.LK", "B", 11, (255, 255, 255))
        self.tree_text(105, root_cy + 2.2, "Sri Lanka themed Monopoly simulation in C",
                       "", 6.6, (210, 220, 240))

        spine_y = root_cy + root_h / 2 + 4.2
        cat_cy, cat_h = spine_y + 3.2, 8.0

        self.set_draw_color(*TREE_NAVY)
        self.set_line_width(0.55)
        self.line(105, root_cy + root_h / 2, 105, spine_y)
        self.line(gx[0], spine_y, gx[-1], spine_y)
        for i in range(ncols):
            self.line(gx[i], spine_y, gx[i], cat_cy - cat_h / 2)

        max_file_rows = max(len(files) for *_a, files in meta)
        pitch = 11.4
        first_file_y = cat_cy + cat_h / 2 + pitch / 2 + 2.5

        for gi, (head, edge, fill, dark, files) in enumerate(meta):
            cx = gx[gi]
            self.tree_box(cx, cat_cy, gw - 4, cat_h, edge, edge)
            self.tree_text(cx, cat_cy, head, "B", 8.2, (255, 255, 255))
            self.set_draw_color(*edge)
            self.set_line_width(0.45)
            last_bottom = first_file_y + (len(files) - 1) * pitch + pitch / 2 - 0.5
            self.line(cx, cat_cy + cat_h / 2, cx, last_bottom)
            for fi, (fname, desc) in enumerate(files):
                fy = first_file_y + fi * pitch
                fw = gw - 8
                x0 = cx - fw / 2
                self.line(cx, fy, x0 + 2, fy)
                self.set_draw_color(*edge)
                self.set_line_width(0.35)
                self.tree_box(cx, fy, fw, pitch - 1.4, fill, edge)
                self.tree_text(cx, fy - 2.0, fname, "B", 7.6, dark)
                self.tree_text(cx, fy + 1.9, desc, "", 5.7, (80, 80, 80))

        legend_y = max(first_file_y + max_file_rows * pitch,
                       cat_cy + cat_h / 2 + 5) + 6
        self.tree_text(105, legend_y,
                       "Colour = responsibility:  teal data model  |  green core engine  |  "
                       "orange economy & rules  |  purple tooling & data",
                       "", 6.8, (60, 60, 60))
        self.set_y(legend_y + 4)
        self.ln(2)

    # -- tables ------------------------------------------------------------

    def table(self, headers, rows, widths=None, font_size=8.3, header_fill=NAVY):
        self.tsize = font_size
        n = len(headers)
        if widths is None:
            widths = [1.0 / n] * n
        total = self.w - self.l_margin - self.r_margin
        w = [wd * total for wd in widths]

        # header
        self.set_fill_color(*header_fill)
        self.set_draw_color(90, 90, 90)
        self.set_font("Arial", "B", font_size)
        self.set_text_color(255, 255, 255)
        max_lines = 1
        for i, h in enumerate(headers):
            lin = self.lines_in(h, w[i], font_size)
            max_lines = max(max_lines, lin)
        hh = max_lines * 4.6 + 1.4
        self.check_page_break(hh)
        ytop = self.get_y()
        for i, h in enumerate(headers):
            self.set_xy(self.l_margin + sum(w[:i]), ytop)
            self.multi_cell(w[i], 4.6, h, border=1, fill=True,
                            align="C", new_x="RIGHT", new_y="TOP")
        self.set_y(ytop + hh)

        self.set_font("Arial", "", font_size)
        self.set_text_color(25, 25, 25)
        for ridx, r in enumerate(rows):
            max_lines = 1
            for i, val in enumerate(r):
                lin = self.lines_in(str(val), w[i], font_size)
                max_lines = max(max_lines, lin)
            row_h = max_lines * 4.5 + 1.6
            self.check_page_break(row_h)
            ytop = self.get_y()
            self.set_fill_color(255, 255, 255 if ridx % 2 == 0 else 242)
            for i, val in enumerate(r):
                cell_lines = self.lines_in(str(val), w[i], font_size)
                pad = (max_lines - cell_lines) * 4.5 / 2.0
                self.set_xy(self.l_margin + sum(w[:i]), ytop + pad)
                self.multi_cell(w[i], 4.5, str(val), border=1, fill=True,
                                align="L", new_x="RIGHT", new_y="TOP")
            self.set_y(ytop + row_h)
        self.ln(2.4)

    def lines_in(self, text, width, size):
        self.set_font("Arial", "", size)
        text = str(text)
        if not text:
            return 1
        sw = self.get_string_width(text)
        if sw <= width or sw == 0:
            return 1
        char_w = sw / len(text)
        cols = max(int(width // char_w), 1)
        return math.ceil(len(text) / cols)

    def check_page_break(self, h):
        if self.get_y() + h > self.h - self.b_margin:
            self.add_page()


# --------------------------------------------------------------------------
# the content
# --------------------------------------------------------------------------

def section_overview(pdf):
    pdf.h1("1", "About This Guide")
    pdf.p("This guide explains every part of the MONOPOLY.LK project so you can "
          "answer viva questions confidently. It was written directly from the "
          "source code, so every description, function name and code snippet "
          "matches the actual project.")
    pdf.bullets([
        "Section 2  - what the project is, what technology it uses, and why it was designed that way.",
        "Section 3  - how to build and run the program.",
        "Section 4  - the complete code tree (file structure).",
        "Section 5  - how the program flows: startup, one turn, one round, and how modules connect.",
        "Section 6  - the data model: every constant, enum and struct in types.h.",
        "Section 7  - a deep dive into each code file, function by function.",
        "Section 8  - every game rule of MONOPOLY.LK as a quick reference.",
        "Section 9  - the tricky algorithms explained step by step.",
        "Section 10 - verification and the 6 bugs that were found and fixed.",
        "Section 11 - likely viva questions with model answers.",
        "Section 12 - a full index of every function in the project.",
        "Section 13 - the complete source code of every file (appendix).",
    ])
    pdf.hint("මෙම මාර්ගෝපදේශය ප්\u0dbbශ්ණ විස\u0dcaත\u0dbb \u0d9a\u0dd2\u0dbb\u0dd3\u0db8\u0da7 "
             "\u0d85\u0dc0\u0dc1\u0dca\u200d\u0dba \u0dc3\u0dd2\u0dba\u0dbd\u0dd4 \u0dc0\u0dd2\u0dc3\u0dca\u0dad\u0dbb "
             "\u0d85\u0da9\u0d82\u0d9c\u0dd4 \u0d9a\u0dbb\u0dba\u0dd2 - \u0d9a\u0dda\u0dad\u0dd4 \u0d85\u0d82\u0dc1\u0dba "
             "\u0dad\u0dd4\u0dc5 \u0dad\u0dd2\u0dba\u0dd9\u0db1 \u0dc3\u0dd2\u0d82\u0dc4\u0dbd \u0d89\u0d9f\u0dd2 "
             "\u0d94\u0db6\u0da7 \u0dc3\u0d82\u0d9a\u0dbd\u0dca\u0db4 \u0db8\u0dad\u0d9a \u0dad\u0db6\u0dcf "
             "\u0d9c\u0dd0\u0db1\u0dd3\u0db8\u0da7 \u0d8b\u0db4\u0d9a\u0dcf\u0dbb\u0dd3 \u0dc0\u0dda.")

    pdf.h1("2", "Project Overview")
    pdf.h2("2.1  What is MONOPOLY.LK?")
    pdf.p("MONOPOLY.LK is a completely text-based computer simulation of a "
          "Sri Lanka themed Monopoly board game. There are no humans - the four "
          "seats are filled by four computer-controlled players, each with a "
          "different investment personality (an AI strategy). The program runs "
          "an entire game from start to finish and prints every action as text, "
          "like a narrated game log.")
    pdf.p("Beyond the classic Monopoly rules, the assignment adds many economic "
          "extensions that are modelled in code: bank loans with interest and "
          "collateral, mortgages and redemption, insurance policies, natural "
          "disasters, inflation, property market booms and declines, regional "
          "development cards, national event cards, government regulations, "
          "property ageing and depreciation, building maintenance and even an "
          "anti-speculation act.")
    pdf.hint("\u0db8\u0dd9\u0dba \u0dc3\u0dca\u0da7\u0dd2\u0d9a\u0dca \u0dc0\u0dd2\u0dba\u0dbb\u0dca\u0dad\u0dca\u0db8 "
             "\u0d9a\u0dca\u200d\u0dbb\u0dd2\u0da9\u0dcf\u0dc0\u0d9a\u0dd2 (\u0dc3\u0dca\u0da7\u0dd2\u0d9a\u0dca "
             "\u0d9a\u0ddc\u0dc3\u0dbb\u0dd4), \u0db4\u0dcf\u0dbd\u0db1\u0dba \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab "
             "\u0dba\u0dd9\u0db1\u0dca\u0db8 AI \u0d9a\u0dca\u200d\u0dbb\u0dd3\u0da9\u0d9a\u0dba\u0dd2\u0db1\u0dca "
             "4 \u0daf\u0dd9\u0db1\u0dd9\u0d9a\u0dd4 \u0d85\u0dad\u0dbb \u0dc3\u0dd2\u0daf\u0dd4 \u0dc0\u0dda.")

    pdf.h2("2.2  Technology used")
    pdf.bullets([
        ("Language   ", "C, written in an old-school, disciplined style (declarations at the top "
                        "of every block, no fancy shortcuts)."),
        ("Libraries  ", "Only the C standard library: stdio.h, stdlib.h, string.h, time.h. "
                        "There is no third-party code, no graphics, no database."),
        ("Compiler   ", "gcc 16.1.0 (MSYS2). The whole program builds with one command: "
                        "gcc *.c -o monopoly"),
        ("Verification", "A Python 3 script (verify_analysis.py) that replays the printed "
                         "game log and checks every money transaction for bugs."),
        ("Platform   ", "A Windows console application (monopoly.exe)."),
    ])

    pdf.h2("2.3  The three design rules of this codebase")
    pdf.p("Looking at the git history you will see three rules the author "
          "followed on purpose. In a viva, explaining these shows you understand "
          "why the code looks the way it does:")
    pdf.numbered([
        "No pointer parameters - every function receives the game state and reads and writes it through "
        "array syntax. That is why nearly every function looks like foo(GameState game[], ...).",
        "No ternary operators - no  x = a ? b : c ;. Everything is written with plain if/else so the "
        "logic is easy to read and check.",
        "No global variables - all state lives inside one GameState struct created in main() and passed "
        "down through the whole program.",
    ])
    pdf.h2("2.4  The GameState game[1] idiom")
    pdf.p("The most important design decision is the shared state object:")
    pdf.code_block(
        "/* main.c - the only place a GameState is ever created */\n"
        "GameState game[1] = {0};   /* a one-element array, all fields zeroed */\n"
        "\n"
        "startGame(game);            /* passed as array, read/written as game[0].xxx */"
    )
    pdf.explain(
        "This tiny snippet is the backbone of the entire project. Every single "
        "function in the codebase receives this same GameState and reads/writes it. "
        "It is included on its own because, in a viva, examiners love to ask 'how "
        "do all those files share data without global variables?' - this is the "
        "answer. Without it the whole architecture would fall apart.",
        "GameState game[1] = {0}  creates ONE struct but writes it as a one-element "
        "array, and {0} zero-fills every field so nothing starts as garbage. "
        "startGame(game) then hands that single object to the game engine. Inside "
        "every other function you see game[0].field - the [0] reminds you it is an "
        "array, never a pointer, but the effect is the same as passing a pointer.",
        "The design rule was 'no explicit pointers anywhere'. In C, when you pass an "
        "array to a function it silently decays to a pointer - so writing game[0].x "
        "inside any function changes the ORIGINAL object in main(), not a copy. The "
        "programmer therefore gets pointer-like sharing without ever typing an "
        "asterisk, and every module can see the same board, players and economy "
        "without using a global variable.")
    pdf.p("GameState contains everything the game needs to remember: the 40-square "
          "board, the 4 players, and the economy. Because pointers were not allowed, "
          "it is declared as a one-element array. In C, passing an array to a function "
          "and writing game[0].field silently changes the original object - the array "
          "parameter is (behind the scenes) a pointer, but the source code never has "
          "to say so. This gives every function read/write access to all state without "
          "a single explicit pointer.")
    pdf.hint("\u0dc3\u0dd1\u0db8 function \u0d91\u0d9a GameState game[] \u0dbd\u0db6\u0dcf\u0d9c\u0dd9\u0db1 "
             "game[0] \u0dc4\u0dbb\u0dc4\u0dcf \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab "
             "\u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba (state) \u0d9a\u0dd2\u0dba\u0dc0\u0db1/\u0dbd\u0dd2\u0dba\u0db1 "
             "\u0d9a\u0dbb\u0dba\u0dd2.")

    pdf.h2("2.5  How the modules divide the work")
    pdf.table(
        ["File", "Side-effect / responsibilities", "More details in"],
        [
            ["main.c", "Entry point; creates GameState; calls startGame().", "7.1"],
            ["types.h", "All constants, enums and structs (the data model).", "6"],
            ["functions.h", "Prototypes of every function in the project.", "7.12"],
            ["board.c", "Builds the 40-square Sri Lanka board.", "7.2"],
            ["players.c", "The 4 AI strategies (all the decisions).", "7.3"],
            ["game.c", "Turn loop, rounds, dice, jail, winner.", "7.4"],
            ["finance.c", "Money, rent, buying, mortgage, building, bankruptcy.", "7.5"],
            ["bank.c", "Loans, collateral, foreclosure, Bank visits.", "7.6"],
            ["auction.c", "The auction engine for unclaimed/forced sales.", "7.7"],
            ["events.c", "Event cards, economic events, regulations.", "7.8"],
            ["economy.c", "Inflation, modifiers, ageing, maintenance, LKR formatting.", "7.9"],
            ["insurance.c", "Insurance policies, disasters, repairs.", "7.10"],
            ["market.c", "Market boom/decline, regional cards, condition display.", "7.11"],
            ["verify_analysis.py", "Python verification harness (test tool, not the game).", "10"],
        ],
        widths=[0.16, 0.64, 0.20],
    )


def section_build(pdf):
    pdf.h1("3", "How to Build and Run")
    pdf.p("Everything is plain C, so any gcc works. From the project folder:")
    pdf.code_block(
        "gcc *.c -o monopoly        # compile all .c files into monopoly.exe\n"
        "monopoly.exe               # run the game (prints the whole game to screen)\n"
        "monopoly.exe > run.txt     # capture the game log for verification"
    )
    pdf.explain(
        "These three commands are the complete build-and-run workflow. They are "
        "included because examiners ask 'how do I run your project?' more than any "
        "other factual question, and this is the exact answer they expect.",
        "gcc *.c -o monopoly  tells the compiler to take EVERY .c file in the folder "
        "and link them into one executable called monopoly. Each file includes the "
        "shared headers, so the compiler sees the whole program. Running "
        "monopoly.exe prints the entire narrated game to the screen, and the third "
        "line shows how to save that printed log to a file for the verifier.",
        "Using *.c instead of listing files avoids mistakes - the compiler itself "
        "collects all modules, so no file can be forgotten. Capturing the log to a "
        "text file is the bridge to verification: the game and the verifier never "
        "share code, they only share this printed log.")
    pdf.note("`gcc *.c -o monopoly` produces a clean build with zero warnings or errors. "
             "Each .c file #includes types.h and functions.h, and main.c + game.c are the only "
             "places that need the whole picture.")
    pdf.p("To run the automatic verifier on a saved log:")
    pdf.code_block(
        "python verify_analysis.py run.txt   # replays the log and reports [BUG]/[REVIEW] items"
    )
    pdf.explain(
        "The verifier is a separate Python program that reads the game log. It is "
        "included here so you can show the examiner the evidence that the project "
        "was tested - not just compiled.",
        "python verify_analysis.py run.txt  runs the Python script with run.txt as "
        "its input. The script literally replays every printed transaction and "
        "compares it with what the rules say should happen, then prints [BUG] or "
        "[REVIEW] lines for anything wrong.",
        "The thinking: testing a simulation is hard (it is random), so instead the "
        "team records what happened and checks the recording afterwards. Because the "
        "log is a complete play-by-play, any rule violation leaves a trace that the "
        "script can find automatically.")
    pdf.hint("\u0d9a\u0dca\u200d\u0dbb\u0dd3\u0da9\u0dcf\u0dc0 \u0d9a\u0dca\u200d\u0dbb\u0dd2\u0dba\u0dcf\u0dad\u0dca\u0db8\u0d9a "
             "\u0d9a\u0dd2\u0dbb\u0dd3\u0db8\u0da7 \u0db8\u0ddb\u0dad\u0dca\u200d\u0dbb\u0dd3 \u0d85\u0dc0\u0dc1\u0dca\u200d\u0dba "
             "\u0db1\u0dd0\u0dad.")


def section_tree(pdf):
    pdf.h1("4", "The Code Tree (File Structure)")
    pdf.p("Here is the whole project laid out as a colourful tree. Each branch is "
          "one responsibility area, each leaf is a file with its size and a "
          "one-line description. Memorising this diagram (data model -> core "
          "engine -> economy & rules -> tooling) helps you describe the whole "
          "architecture in a viva in one breath.")
    pdf.code_tree()
    pdf.h2("4.1  The same tree in plain text (line counts)")
    pdf.p("If you prefer to learn the exact file list, this is the identical "
          "structure in a compact text form - easier to memorise line by line.")
    pdf.code_block(
        "MONOPOLY.LK/\n"
        "|\n"
        "|-- types.h            (361 lines)  ALL constants, enums, structs - the data model\n"
        "|-- functions.h        (184 lines)  prototypes of every function, grouped by module\n"
        "|\n"
        "|-- main.c             (17 lines)   entry point - creates GameState, calls startGame\n"
        "|-- game.c            (640 lines)   main loop, turns, dice, jail, rounds, winner\n"
        "|-- board.c           (205 lines)   the 40-square Sri Lanka board\n"
        "|-- players.c         (405 lines)   the 4 AI strategies / decision functions\n"
        "|-- finance.c        (1076 lines)   money, rent, buying, mortgage, buildings, taxes\n"
        "|-- bank.c            (394 lines)   loans, collateral, foreclosure, Bank visits\n"
        "|-- auction.c         (178 lines)   the auction engine\n"
        "|-- events.c          (402 lines)   event cards, economic events, regulations\n"
        "|-- economy.c         (503 lines)   inflation, modifiers, ageing, maintenance, LKR format\n"
        "|-- insurance.c       (392 lines)   insurance policies, disasters, repairs\n"
        "|-- market.c          (430 lines)   market boom/decline, regional cards, conditions\n"
        "|\n"
        "|-- verify_analysis.py (1458 lines) Python log-replay verification analyzer\n"
        "|-- Rent.csv           (23 lines)   property price/rent table (data export)\n"
        "|\n"
        "|-- output/\n"
        "|   `-- verification_report.txt     reported bugs + the 6 confirmed fixes\n"
        "|\n"
        "|-- run.txt / run2.txt / run3.txt / run4.txt / test.txt   game logs (verification)\n"
        "|-- monopoly.exe      the compiled Windows binary\n"
        "|-- monopoly_final.zip the submission archive\n"
        "|\n"
        "`-- generate_viva_pdf.py   THIS script - produces the study guide PDF"
    )
    pdf.explain(
        "The tree exists so you can describe the whole project without opening any "
        "file. An examiner often asks 'how is the project organised?' and expects a "
        "structured answer - this diagram is that answer. Every file is included "
        "because it plays one role: types.h and functions.h define the shared "
        "vocabulary, the .c files implement it, verify_analysis.py proves it works.",
        "Data model (teal) = the shared definitions every .c file #includes. "
        "Core engine (green) = main.c (entry point), game.c (the turn/round loops), "
        "board.c (the 40 squares), players.c (the AI decisions). "
        "Economy & rules (orange) = finance.c, bank.c, auction.c, events.c, economy.c, "
        "insurance.c and market.c - all the money and rules that make the game "
        "behave like an economy. Tooling & data (purple) = the Python verifier, the "
        "Rent.csv data table, output/, saved game logs and the submission archive.",
        "The tree is drawn like a real tree (root -> branches -> leaves) because the "
        "dependency flow is one-directional: a file can only depend on the files "
        "above it. types.h sits at the root because everything else depends on it. "
        "That ordering (data -> flow -> economy -> tools) is the same order you "
        "should present the modules in a viva.")
    pdf.p("Roughly half the code is 'game logic' (finance.c, economy.c, bank.c, "
          "insurance.c, market.c, auction.c, events.c) and the other half is "
          "'control flow and decisions' (game.c, board.c, players.c, main.c).")
    pdf.hint("\u0db4\u0dd4\u0daf\u0dca\u0d9c\u0dbd\u0dba\u0dd9\u0d9a\u0dca \u0da2\u0dba\u0d9c\u0dca\u200d\u0dbb\u0dc4\u0dab\u0dba "
             "\u0d9a\u0dbb\u0db1\u0dca\u0db1\u0dda game.c \u0d87\u0dad\u0dd4\u0dc5\u0dd4 \u0db4\u0dca\u200d\u0dbb\u0db0\u0dcf\u0db1 "
             "\u0db4\u0dd4\u0d82\u0d9b\u0ddd\u0dbd\u0dd2\u0dba \u0dc4\u0dbb\u0dc4\u0dcf\u0dba.")


def section_architecture(pdf):
    pdf.h1("5", "Architecture and Execution Flow")
    pdf.h2("5.1  Program start")
    pdf.code_block(
        "main.c  main()\n"
        "  |  creates  GameState game[1] = {0}\n"
        "  v\n"
        "game.c  startGame(game)\n"
        "  |  srand(time(NULL))                     -> random seed so each game differs\n"
        "  |  initializeBoard(game)     (board.c)   -> fills board[0..39]\n"
        "  |  initializePlayers(game)   (players.c) -> 4 AI players, 30,000 LKR each\n"
        "  |  initEconomy(game)         (economy.c) -> interest rate, tax rate, modifiers[0]\n"
        "  |  initMarket(game)          (market.c)  -> group cooldowns cleared\n"
        "  |  determineTurnOrder(game)  (game.c)    -> recursive dice roll-off for who starts\n"
        "  |  playGame(game, order)                 -> the whole game\n"
        "  `  displayFinalResults(game)             -> winner + final standings"
    )
    pdf.explain(
        "This is the startup sequence - the exact journey a program takes from the "
        "first line of main() to the first turn. It is included because 'walk me "
        "through what happens when the program runs' is one of the most common "
        "opening viva questions, and this treeline is the ideal memory hook.",
        "main() is deliberately tiny: it creates the single GameState and calls "
        "startGame(). startGame then lays every foundation - seed the random "
        "generator with time so each game differs, build the 40 squares, create the "
        "4 AI players with cash, set up the economy (interest, tax, modifier list), "
        "clear market cooldowns, roll to decide who plays first, run the whole "
        "game, and finally print the winner and standings.",
        "The logic is separation of concerns: main() must not know HOW the game "
        "works, it only must create state and kick off the engine. Each init_* step "
        "belongs to the module that owns that data (board.c initialises the board, "
        "players.c initialises players...) so no module reaches into another's "
        "responsibility. srand(time(NULL)) is the one call that makes every run "
        "unique.")
    pdf.h2("5.2  A single turn (playTurn)")
    pdf.p("This is the heart of the game. One AI player's whole turn, in order:")
    pdf.code_block(
        "playTurn(game, playerIndex)\n"
        "  1. tryAutoRepair / performMaintenance / renovateStructuralDamage\n"
        "     -> fix any damaged, worn or neglected buildings first\n"
        "  2. handleJail  -> if in jail: doubles frees you / pay bail / forced after 3 turns\n"
        "                   (if jail handling ran, the turn ENDS - no movement)\n"
        "  3. rollDice()  -> two d6 summed (2..12)\n"
        "  4. movePlayer  -> pos = (pos + dice) % 40 ; if it wrapped, collect LKR 2000 (GO)\n"
        "  5. resolve landing by square type:\n"
        "       PROPERTY/RAILWAY/UTILITY -> payRent then buyProperty (else -> auction)\n"
        "       EVENT    -> executeEvent   (national event card)\n"
        "       TAX      -> payTax         (15% of net worth, market-scaled)\n"
        "       COMMUNITY_FUND -> payCommunityFundTax  (10% of property value)\n"
        "       GO_TO_JAIL -> teleport to square 10, marked in jail\n"
        "       BANK     -> handleBankVisit (loans)\n"
        "       INSURANCE-> handleInsuranceVisit\n"
        "       GO / JAIL(visiting) / FREE_PARKING -> nothing\n"
        "  6. constructBuildings -> keep building while affordable (even development)\n"
        "  7. sellDecliningProperties -> Opportunistic Trader dumps declining properties\n"
        "  8. handleMortgageDecisions -> redeem a mortgage, then maybe raise a new one"
    )
    pdf.explain(
        "playTurn is the heart of the game - it defines EVERYTHING one AI player "
        "does on one go. It is included in its own page because 'what happens "
        "during a turn?' is the single most likely viva question, and this ordered "
        "list is the complete answer.",
        "Step 1 fixes broken buildings so the property earns again. Step 2 handles "
        "jail (and if that ran, the turn stops - a jailed player does NOT move). "
        "Steps 3-4 roll two dice and move, paying 2000 when passing GO. Step 5 is "
        "the big if/else that dispatches on the square type: rent-and-buy for "
        "properties (else auction), event cards, taxes, bank and insurance visits. "
        "Steps 6-8 are the end-of-turn economy actions: build, sell garbage, and "
        "manage mortgages.",
        "The ordering is logical, not random: repairs come first so the machinery "
        "works before you calculate anything; the landing resolution (step 5) "
        "changes cash, so building decisions (step 6) must come AFTER it, never "
        "before; sell/mortgage come last as 'tidy up' actions. Remembering this "
        "order also tells the examiner you understand cause and effect in the game.")
    pdf.h2("5.3  What does a 'round' mean here?")
    pdf.p("This is an unusual and important detail. In a normal board game a round "
          "is 'everyone takes one turn'. Here a round only ends when EVERY solvent "
          "player has passed GO at least once. Because players move different "
          "distances each turn, finishing the round usually takes several turns per "
          "player. playGame keeps cycling the turn order until allPassed becomes true.")
    pdf.code_block(
        "while round <= 500:\n"
        "    take next player's turn          (skip bankrupt players)\n"
        "    if that player passed GO then flag them\n"
        "    if EVERY non-bankrupt player has passed GO this round:\n"
        "        -> round-end bookkeeping (5.4) and start a new round"
    )
    pdf.explain(
        "This loop is the skeleton of the whole simulation. It is the answer to "
        "'how do you structure the game?' - the top-level while keeps going until "
        "500 rounds or a winner appears.",
        "Each iteration runs one player's turn. Bankrupt players are skipped. "
        "Whenever someone passes GO a flag marks them for the current round, and "
        "the moment EVERY surviving player has passed GO, the round is finished so "
        "the round-end bookkeeping from 5.4 runs and a new round begins.",
        "The key idea: a 'round' is NOT four turns here, it is 'everyone crossed "
        "GO once'. Because players move different distances the flag system is the "
        "only fair way to know a round is done. The 500 cap guarantees the loop "
        "always terminates, which is why the game can never hang.")
    pdf.h2("5.4  Round-end bookkeeping (playGame, one round)")
    pdf.code_block(
        "processLoans(game)            (bank.c)     interest added to principal; foreclose at 0 rounds\n"
        "processInsuranceExpiry(game)  (insurance.c) policies count down, expire at 0\n"
        "ageProperties(game)           (economy.c)  age +1; past 50 -> depreciation +5% per 5 rounds\n"
        "ageBuildings(game)            (economy.c)  condition -2; neglect > 20 -> structural damage\n"
        "decrementEventTimers(game)    (events.c)   construction suspension / closed property\n"
        "decrementModifiers(game)      (economy.c)  all timed effects tick down and are removed\n"
        "enforceAntiSpeculation(game)  (finance.c)  force-sell undeveloped surplus if triggered\n"
        "\n"
        "every 10 rounds:  triggerDisaster + applyInflation + reviewPropertyMarket\n"
        "every 15 rounds:  triggerEconomicEvent + drawRegionalCard\n"
        "every 20 rounds:  triggerGovernmentRegulation\n"
        "\n"
        "displayRoundSummary(game)  +  displayMarketConditions(game)"
    )
    pdf.explain(
        "This block is the 'world ticks forward' moment - the economic heartbeat "
        "between rounds. It is on its own page because an examiner may ask 'where "
        "do loans, ageing and events happen?' and the answer is: right here, once "
        "per round.",
        "The first six lines make the ongoing state evolve: loans grow with "
        "interest (and default at zero rounds), insurance policies expire, "
        "properties age, buildings degrade, event timers tick down, modifiers are "
        "removed when their time is up, and the anti-speculation act force-sells "
        "excess undeveloped property. The middle block schedules the periodic "
        "headline events every 10, 15 and 20 rounds. The last line prints the "
        "summary and market conditions for the log.",
        "Why this grouping? Putting ALL timed effects in one place means the turn "
        "loop never has to remember them - they happen exactly once per round by "
        "construction. The cadence numbers (10/15/20) are constants, so the timing "
        "is easy to change and easy to explain.")
    pdf.h2("5.5  How the modules talk to each other")
    pdf.code_block(
        "                        +----------------------+\n"
        "                        v                      |\n"
        "   main.c -> startGame -> playGame -> playTurn +-> playTurn(next player)...\n"
        "                                 |\n"
        "              landing / decisions call down into:\n"
        "   finance.c  payRent->calculateRent -> modifierMultiplier(economy.c)\n"
        "              buyProperty->shouldBuyProperty(players.c) / runAuction(auction.c)\n"
        "   economy.c  currentMarketValue  <- used by finance, bank, insurance, auction\n"
        "   players.c  every should*/wants* decision funnels through strategy switch\n"
        "   bank.c     obtainLoan -> totalEligibleCollateral -> modifierMultiplier\n"
        "   events.c   executeEvent -> addModifier(economy.c) / triggerDisaster(insurance.c)\n"
        "   market.c   reviewPropertyMarket -> addSourcedModifier(economy.c)\n"
        "   insurance.c triggerDisaster -> payCompensation / mark damaged\n"
        "                                 |\n"
        "   every function reads/writes the SAME GameState passed as game[]"
    )
    pdf.explain(
        "This diagram is the architecture map - it shows which module calls which. "
        "It is included because 'how do your modules communicate?' is a guaranteed "
        "viva question, and it shows the dependency direction at a glance.",
        "main.c -> startGame -> playGame -> playTurn is the call chain of the "
        "whole game. From playTurn, each landing or decision drops INTO a helper "
        "module: rent goes through finance.c's payRent->calculateRent which itself "
        "asks economy.c for multipliers; buying asks players.c whether the AI likes "
        "the deal, else auction.c; loans and events fan out to bank.c, events.c, "
        "insurance.c and market.c.",
        "The single organising principle is that control flows DOWN the diagram and "
        "data flows UP through the shared GameState. Modules never call each other "
        "sideways for money - they all disagree-proof their numbers by reading "
        "currentMarketValue from economy.c, the one source of truth. That is why "
        "no two modules can compute different prices.")
    pdf.hint("\u0db8\u0ddc\u0dab\u0ddc\u0db4\u0ddc\u0dbd\u0dd2 \u0d9a\u0dca\u200d\u0dbb\u0dd3\u0da9\u0dcf\u0dc0\u0dda "
             "\u0da2\u0dd3\u0dc0\u0db1 \u0da0\u0d9a\u0dca\u200d\u0dbb\u0dba: \u0d85\u0dc0\u0dbb\u0dd4\u0dbd\u0dda "
             "\u0db4\u0dd4\u0dc0\u0dbb\u0dd4\u0dc0\u0dda \u0d9c\u0db8\u0db1\u0dca -> \u0d9a\u0dd4\u0dbd\u0dd2/\u0db8\u0dd2\u0dbd\u0daf\u0dd3 "
             "\u0d9c\u0dd0\u0db1\u0dd3\u0db8 -> \u0d9c\u0ddc\u0da9\u0db1\u0dd0\u0d9c\u0dd2\u0dbd\u0dca\u0dbd - \u0dc3\u0dd1\u0db8 "
             "\u0dc0\u0da7\u0dba\u0d9a\u0db8 \u0db8\u0dd9\u0db8 \u0dbb\u0da7\u0dd2\u0dba\u0dba\u0dd2.")


def section_data_model(pdf):
    pdf.h1("6", "The Data Model (types.h)")
    pdf.p("types.h defines the whole vocabulary of the game. It has four kinds of "
          "things: #define constants (numbers), typedef enums (named lists), "
          "typedef structs (shapes of data), and the GameState bundle that joins "
          "everything. Because every source file #includes types.h, the numbers all "
          "have one single source of truth.")

    pdf.h3("6.1  Game constants")
    pdf.table(
        ["Constant", "Value", "Meaning"],
        [
            ["MAX_PLAYERS", "4", "exactly four AI players"],
            ["BOARD_SIZE", "40", "squares on the board"],
            ["MAX_ROUNDS", "500", "hard cap; game ends here"],
            ["START_MONEY", "30000", "each player's starting cash (LKR)"],
            ["GO_MONEY", "2000", "collected when passing GO"],
            ["JAIL_BAIL", "300", "bail fee"],
            ["JAIL_SQUARE / JAIL_MAX_TURNS", "10 / 3", "jail location / forced-bail after 3 turns"],
            ["INCOME_TAX_RATE", "15", "base income tax % (drifts with market)"],
            ["COMMUNITY_FUND_TAX_RATE", "10", "base community fund tax %"],
            ["MAX_HOUSES / MAX_HOTELS", "4 / 1", "buildings allowed per property"],
            ["LOAN_DURATION_ROUNDS", "20", "borrowed money must be repaid in ... rounds"],
            ["LOAN_INTEREST_RATE", "8", "starting interest %"],
            ["LOAN_COLLATERAL_PERCENT", "75", "max loan = 75% of collateral (Rule-LK 2)"],
            ["LOAN_EXTEND_ROUNDS", "10", "extending a loan adds 10 rounds"],
            ["MORTGAGE_REPAY_PERCENT", "110", "redeeming a mortgage costs 110%"],
            ["LOAN_INTEREST_MIN/MAX/STEP", "1/25/2", "interest limits + step size"],
            ["TAX_RATE_MAX", "25", "income tax never exceeds 25%"],
            ["RAILWAY_RENT_1..4", "250/500/1000/2000", "rent by number of railways owned"],
            ["UTILITY_RENT_ONE/TWO", "4x / 10x", "utility rent = dice multiplier"],
            ["AUCTION_OPENING_DIVISOR / BID_INCREMENT", "2 / 250", "auction start = value/2, bid +250"],
            ["MARKET_REVIEW_EVERY / COOLDOWN", "10 / 30", "market boom/decline cadence"],
            ["PROPERTY_AGE_LIMIT / DEPRECIATION_STEP / MAX", "50 / 5 / 30", "ageing rules"],
            ["RENOVATION_COST_PERCENT / RENT_BOOST", "10 / 5", "renovation cost / +5% rent"],
            ["NEGLECT_ROUNDS", "20", "no maintenance this long = structural damage"],
            ["STRUCTURAL_VALUE/RENT_LOSS, REPAIR_MULT", "15 / 25 / 150", "structural damage effects"],
            ["REPAIR_COST_PERCENT", "30", "disaster repair = 30% of value"],
            ["PREMIUM_BASIC/COMPREHENSIVE/BI", "5/10/15", "insurance premium % of value"],
            ["INSURANCE_DURATION / RENEW_AT / WARNING", "20 / 10 / 3", "policy lifecycle"],
            ["DISASTER_WEIGHT / BOOST", "20 / 30", "weighted disaster picker"],
            ["ANTI_SPEC max undeveloped / trigger", "3 / 5", "Anti-Speculation Act rules"],
            ["EVENT/ECON/REG/REGIONAL card counts", "20/8/8/12", "deck sizes"],
            ["ECONOMY/EVENT/REGULATION CYCLE", "10/15/20", "rounds between periodic events"],
            ["MIN_CASH_SAFETY", "1000", "common strategy cash reserve"],
        ],
        widths=[0.52, 0.18, 0.30],
        font_size=7.6,
    )

    pdf.h3("6.2  Enumerations (named lists)")
    pdf.table(
        ["Enum", "Values", "Role"],
        [
            ["SquareType", "GO, PROPERTY, RAILWAY, UTILITY, TAX, COMMUNITY_FUND, EVENT, BANK, INSURANCE, JAIL, FREE_PARKING, GO_TO_JAIL",
             "what each of the 40 squares does"],
            ["PropertyGroup", "BROWN ... DARK_BLUE, NO_GROUP", "the 8 colour groups (+sentinel)"],
            ["PlayerType", "AGGRESSIVE_INVESTOR, CONSERVATIVE_BANKER, RISK_TAKER, OPPORTUNISTIC_TRADER", "the 4 AI personalities"],
            ["InsuranceType", "NO, BASIC, COMPREHENSIVE, BUSINESS_INTERRUPTION", "policy types"],
            ["DisasterType", "FIRE, FLOOD, RIOT, BUILDING_COLLAPSE, ELECTRICAL_FAILURE", "disasters"],
            ["ModifierType", "MOD_VALUE_GLOBAL ... 18 kinds", "every kind of temporary effect"],
            ["ModifierSource", "SRC_GENERAL, SRC_BOOM, SRC_DECLINE, SRC_REGIONAL", "where an effect came from (for the report)"],
        ],
        widths=[0.20, 0.50, 0.30],
        font_size=7.6,
    )

    pdf.h3("6.3  Structs - the shape of the data")
    pdf.p("The structs are nested: GameState contains Economy, Player[4], Square[40]; "
          "each Square contains a Property; each Player contains a Loan.")
    pdf.code_block(
        "GameState\n"
        "  +-- Square board[40]        the 40 squares\n"
        "  +-- Player players[4]       the 4 AI players\n"
        "  `-- Economy economy         interests, tax, modifiers, event timers\n"
        "\n"
        "Square\n"
        "  +-- int     index           0..39\n"
        "  +-- SquareType type         what kind of square\n"
        "  +-- char    name[50]\n"
        "  `-- Property property       the buyable data (used for ALL squares)\n"
        "\n"
        "Property (one per square)\n"
        "  +-- name / group / purchasePrice / baseRent\n"
        "  +-- mortgageValue / houseCost / hotelCost\n"
        "  +-- owner (-1 = nobody)  houses  hotel\n"
        "  +-- mortgaged  loanLocked (pledged as collateral)\n"
        "  +-- insurance (type)  insuranceRoundsLeft\n"
        "  +-- damaged  repairCostOwed  lostIncomeRoundsLeft\n"
        "  +-- age  depreciation         (value ageing)\n"
        "  +-- condition  roundsSinceMaintenance  structurallyDamaged\n"
        "  +-- preDamagePurchasePrice  preDamageBaseRent  maintenanceCostMultiplierPercent\n"
        "\n"
        "Player\n"
        "  +-- name  strategy  position  cash\n"
        "  +-- inJail  jailTurns  bankrupt\n"
        "  +-- propertiesOwned  railwaysOwned  utilitiesOwned\n"
        "  +-- Loan loan   (active / amount / interestRate / remainingRounds)\n"
        "  +-- sufferedLoss   (Risk Taker insures only after a loss)\n"
        "  `-- antiSpecRounds (consecutive rounds above 3 undeveloped props)\n"
        "\n"
        "Economy\n"
        "  +-- inflationRate  loanInterestRate  incomeTaxRate\n"
        "  +-- constructionSuspendedRoundsLeft  closedPropertyIndex/RoundsLeft\n"
        "  +-- antiSpeculationActive  currentCardIndex\n"
        "  +-- groupCooldownUntilRound[8]  lastBoomGroup  lastDeclineGroup\n"
        "  `-- ActiveModifier modifiers[48] + modifierCount"
    )
    pdf.explain(
        "This block shows the SHAPE of every piece of data the game remembers. It "
        "is included because 'where is X stored?' is a favourite examiner question, "
        "and this diagram is the complete inventory of where every fact lives.",
        "GameState is the root that holds three big pieces: the board (40 Squares), "
        "the players (4), and the economy. Each Square has a type and a Property "
        "(even special squares hold a Property struct so every square can be "
        "treated uniformly). Player holds one Loan and some counters. Economy holds "
        "the rates plus up to 48 temporary ActiveModifier effects.",
        "The fields encode game rules as data: owner = -1 IS 'unowned', loanLocked "
        "IS 'cannot sell/mortgage', damaged IS 'earns no rent', condition IS 'how "
        "much rent a building earns'. Instead of one global rulebook, the game "
        "stores its state so that any rule can be checked by reading a single "
        "field - consistent and easy to verify.")
    pdf.p("Almost every invariant of the game is stored somewhere in these fields: "
          "owner == -1 means unowned, loanLocked means 'cannot be sold or mortgaged', "
          "damaged means 'earns no rent', condition drives how much rent a developed "
          "property collects, and depreciation drives the real market value.")
    pdf.note("MAX_MODIFIERS = 48 simply caps the number of simultaneous temporary effects; "
             "addModifier silently ignores new ones if the list is full (a safety guard).")
    pdf.hint("\u0dc3\u0dd1\u0db8 \u0daf\u0dd9\u0dba\u0d9a\u0dca \u0d91\u0d9a struct \u0d92\u0d9a\u0d9a "
             "\u0dad\u0dd4\u0dc5 \u0d9c\u0db6\u0da9\u0dcf: GameState = \u0db4\u0dd4\u0dc0\u0dbb\u0dd4\u0dc0 + "
             "\u0d9a\u0dca\u200d\u0dbb\u0dd3\u0da9\u0d9a\u0dba\u0ddd + \u0d86\u0dbb\u0dca\u0dae\u0dd2\u0d9a \u0dad\u0dd2\u0dad\u0dd4\u0dbb\u0dd4.")


# --------------------------------------------------------------------------
# module deep dives
# --------------------------------------------------------------------------

def module_main(pdf):
    pdf.h1("7", "Module Deep Dives")
    pdf.p("This is the main body of the guide. Each subsection covers one source "
          "file: what it is for, every function it defines, and the important logic "
          "explained step by step.")
    pdf.hint("\u0dc3\u0dd1\u0db8 file \u0d91\u0d9a: \u0d85\u0dbb\u0db8\u0dd4\u0dab, function \u0dbd\u0dd0\u0dba\u0dd2\u0dc3\u0dca\u0dad\u0dd4\u0dc0, \u0dc3\u0dc4 \u0dc4\u0daf\u0dbd\u0dcf \u0d87\u0dad\u0dd2 \u0dad\u0dbb\u0dca\u0d9a\u0dba.")

    # -- main.c ------------------------------------------------------------
    pdf.h2("7.1  main.c - the entry point")
    pdf.p("Absurdly simple on purpose. main() creates the one and only GameState "
          "object in the whole program, prints a banner, and hands control to "
          "startGame(). Nothing else happens here; all real setup lives in game.c.")
    pdf.code_block(
        "int main(void)\n"
        "{\n"
        "    /* the only place a GameState is ever created */\n"
        "    GameState game[1] = {0};\n"
        "\n"
        "    printf(\"===========...===========\\n\");\n"
        "    printf(\"        MONOPOLY-LK SIMULATION\\n\");\n"
        "    printf(\"===========...===========\\n\\n\");\n"
        "\n"
        "    startGame(game);\n"
        "    return 0;\n"
        "}",
        title="main.c (entire file, 17 lines)",
    )
    pdf.explain(
        "This is the very first file an examiner will look at. It is included in "
        "full because it proves a design point: the entry point is ALLOWED to be "
        "tiny. Every line here has a job, and none of it is 'spare'.",
        "The comment tells the reader this is the ONLY GameState created. {} "
        "zero-initialises every field of the struct so nothing holds garbage. The "
        "three printf lines print the game banner, and startGame(game) starts the "
        "whole simulation. return 0 signals a clean exit to the operating system.",
        "The design thinking is 'thin entry point': main() has only two duties - "
        "create the shared state and hand over to the engine. Every real setup "
        "(board, players, economy) is delegated to startGame and its init_* "
        "helpers, so everything that could go wrong is testable and nothing is "
        "buried in main(). This directly answers 'why is main.c so short?'.")
    pdf.p("Why {0}? It zero-initialises every field. Without it, uninitialised data "
          "would contain garbage, and fields the board builders forget to set "
          "(e.g. owner) would look wrong. You will see board.c explicitly sets owner = -1 "
          "everywhere - that fix is the reason special squares are not 'owned' by player 0.")

    # -- board.c -----------------------------------------------------------
    pdf.h2("7.2  board.c - building the 40-square board")
    pdf.p("board.c turns a flat array of Square structs into the complete game board. "
          "There are four 'setter' functions that fill in common values, and one big "
          "initialiser that calls them 40 times.")
    pdf.table(
        ["Function", "Purpose"],
        [
            ["setProperty(...)", "fills a colour-group property: price, base rent, mortgage, house/hotel costs, and resets all ~20 runtime fields (owner=-1, condition=100, houses=0, ...)"],
            ["setRailway(...)", "a railway: price + mortgage = price/2; everything else zeroed (no buildings, no insurance)"],
            ["setUtility(...)", "the two utilities: same shape as a railway"],
            ["setSpecialSquare(...)", "non-buyable squares (GO, Jail, Tax, ...); critically sets owner = -1 so they never look owned"],
            ["initializeBoard(...)", "calls the setters 40 times with the Sri Lanka street data"],
        ],
        widths=[0.30, 0.70],
    )
    pdf.p("The board layout (index, name, group, price/rent). This is the standard "
          "Monopoly ring layout, indexed 0..39 going clockwise from GO.")
    pdf.code_block(
        " 0  GO                        20  Free Parking\n"
        " 1  Pettah (Brown  1500/100)  21  Kandy City (Red      5500/450)\n"
        " 2  Community Fund (tax 10%)  22  National Event Card\n"
        " 3  Maradana (Brown 1800/120) 23  Peradeniya (Red   5800/480)\n"
        " 4  Income Tax (tax 15%)      24  Katugastota (Red  6000/500)\n"
        " 5  Colombo Fort Railway      25  Galle Railway Station\n"
        " 6  Bambalapitiya (LB 2500/180) 26 Galle Fort (Yellow 6500/600)\n"
        " 7  National Event Card       27  Unawatuna (Yellow 6800/620)\n"
        " 8  Wellawatte (LB 2700/200)  28  Water Supply Board (utility)\n"
        " 9  Mount Lavinia (LB 3000/220) 29 Hikkaduwa (Yellow 7000/650)\n"
        " 10 Jail / Just Visiting      30  Go To Jail\n"
        " 11 Nugegoda (Pink 3500/260)  31  Jaffna Town (Green 8000/750)\n"
        " 12 Electricity Board (util)  32  Nallur (Green 8300/780)\n"
        " 13 Maharagama (Pink 3800/280) 33 Ceylinco Insurance\n"
        " 14 Kottawa (Pink 4000/300)   34  Trincomalee (Green 8500/800)\n"
        " 15 Kandy Railway Station     35  Jaffna Railway Station\n"
        " 16 Negombo (Orange 4500/350) 36  National Event Card\n"
        " 17 Sri Lanka Insurance       37  Nuwara Eliya (DkBlue 10000/1000)\n"
        " 18 Katunayake (Orange 4700/370) 38 Bank of Ceylon\n"
        " 19 Ja-Ela (Orange 5000/400)  39  Galle Face (DkBlue 12000/1200)"
    )
    pdf.explain(
        "This is the complete board layout - every square, its index, colour group "
        "and price/rent, all on one page. It is included because an examiner may "
        "point at any square and ask why that number is stored there, and you need "
        "the layout memorised to keep the numbers straight.",
        "Each line reads: index, Sri Lankan place name, colour group in brackets, "
        "then purchase price / basic rent. Special squares (GO, Community Fund, "
        "Income Tax, Event, Jail, Insurance, Bank, Free Parking, Go To Jail) have "
        "no price. There are 22 colour properties, 4 railways, 2 utilities and 12 "
        "special squares = 40.",
        "The layout mirrors the classic Monopoly ring indexed 0..39 clockwise. "
        "Keeping prices grouped by colour (Brown cheap -> Dark Blue expensive) "
        "reproduces the real game's balance. The index also IS the movement "
        "coordinate: after moving, position = (position + dice) % 40, and looking "
        "up board[pos] gives you every number for that square.")
    pdf.p("That makes 22 colour properties, 4 railways, 2 utilities, and 12 special "
          "squares (GO, Community Fund, Income Tax, 3 events, Jail, 2 insurance, "
          "Free Parking, Go To Jail, Bank) = 40 in total.")
    pdf.hint("\u0db4\u0dd4\u0dc0\u0dbb\u0dd4\u0dc0 \u0dad\u0db1\u0dad\u0db1\u0dca 40 \u0d9a\u0dd2; "
             "\u0dad\u0dcf\u0db1 \u0db4\u0dd9\u0dc5\u0dd9\u0dc4\u0dd2 \u0dbd\u0d9a\u0dd4\u0dab (index) \u0db8\u0d9c\u0dd2\u0db1\u0dca "
             "\u0d9c\u0db8\u0db1\u0dca \u0d9c\u0dab\u0db1\u0dca \u0d9a\u0dbb\u0dba\u0dd2.")

    # -- players.c ---------------------------------------------------------
    pdf.h2("7.3  players.c - the 4 AI strategies")
    pdf.p("This file is pure decision-making. It contains no money movement - it "
          "only answers questions like 'should I buy this?', 'do I want a loan?', "
          "'how much will I bid?'. Every decision function switches on the player's "
          "PlayerType, so changing a strategy just means editing one case.")

    pdf.table(
        ["Function", "Question it answers"],
        [
            ["initializePlayers", "sets names, strategies, position 0, 30,000 cash, zero counters"],
            ["shouldBuyProperty", "should I buy the square I just landed on?"],
            ["shouldConstruct", "should I spend on this house/hotel?"],
            ["wantsLoan", "do I want to borrow now?"],
            ["wantsToRepayLoan", "do I want to repay the loan?"],
            ["wantsIncreaseLoan", "borrow more against new collateral?"],
            ["wantsExtendLoan", "push the deadline back?"],
            ["wantsRefinance", "move to the current (lower) interest rate?"],
            ["desiredInsurance", "which policy (or none) do I want?"],
            ["shouldRenovateAgeDepreciation", "pay to fix age depreciation?"],
            ["shouldMaintain", "pay maintenance on a worn building?"],
            ["willingToBid", "bid this amount at auction?"],
            ["shouldMortgage", "mortgage a property to raise cash?"],
            ["shouldRedeemMortgage", "buy a mortgaged property back?"],
            ["shouldPayBail", "pay the 300-lkr bail instead of waiting?"],
        ],
        widths=[0.36, 0.64],
    )

    pdf.h3("The strategy decision matrix (memory aid)")
    pdf.table(
        ["Decision", "Aggressive Investor", "Conservative Banker", "Risk Taker", "Opportunistic Trader"],
        [
            ["Buy property", "always if it completes a monopoly; else keep >= 1000", "no props during recession; keep cash >= 2x price", "any cash >= price", "never into a declining group; price <= 40% cash"],
            ["Build (house/hotel)", "cash - cost >= 1000", "no hotels while a loan is active; keep >= 50% cash", "cash >= cost (any)", "subsidy -> keep 30%; inflation -> keep 60%; else 40%"],
            ["Want a loan", "always", "only near bankruptcy (cash < 1000)", "always", "cash < 5000"],
            ["Repay loan", "cash >= 2x loan", "cash >= loan", "rarely (cash >= 5x loan)", "cash >= 1.5x loan"],
            ["Extend loan", "never (prefers borrowing more)", "<= 5 rounds left and broke", "<= 10 rounds left", "<= 5 rounds left"],
            ["Refinance", "shared rule for all: only when current economy rate is lower"],
            ["Insurance", "hotel -> Comprehensive else Basic", "always Comprehensive", "none until a loss; then BI if hotel", "Comprehensive only if price >= 6000"],
            ["Bid at auction", "up to 120% of market value", "below 100% of market value", "always (if funded)", "up to 80% of market value"],
            ["Mortgage", "cash < 1000", "cash < 3000", "cash < 500", "cash < 1200"],
            ["Pay bail", "cash >= 5000", "cash >= 1500", "never", "cash >= 5000"],
            ["Maintain building", "keep 80% cash after cost", "keep 80% cash after cost", "only when condition < 25", "keep 80% cash after cost"],
            ["Renovate age depreciation", "when depreciation >= 20%", ">= 10%", ">= 20%", ">= 15%"],
        ],
        widths=[0.18, 0.21, 0.21, 0.19, 0.21],
        font_size=6.8,
    )
    pdf.note("The 'cash safety' numbers used here (1000 / 3000 / 500 / 5000 ...) are "
             "all named constants in types.h (MIN_CASH_SAFETY, COMFORTABLE_CASH, ...).")

    # -- game.c ------------------------------------------------------------
    pdf.h2("7.4  game.c - the game engine")
    pdf.p("game.c is the conductor. It performs the start-of-game setup, owns the "
          "turn/round loops, and decides who wins.")
    pdf.table(
        ["Function", "Purpose"],
        [
            ["rollDice", "two d6 summed -> 2..12 (movement and utility rent use the sum; jail uses the individual dice)"],
            ["movePlayer", "advances position by dice, wraps at 40; returns 1 (and pays LKR 2000) if GO was passed"],
            ["handleJail", "implements Rule 13: doubles release, bail release, or forced bail after 3 turns; returns 1 = turn ends without moving"],
            ["playTurn", "one whole turn: repair -> jail -> roll+move -> landing dispatch -> build -> sell -> mortgage"],
            ["resolveGroup / determineTurnOrder", "roll each player's dice; sort highest first; any tie re-rolls recursively until a strict order exists"],
            ["countHouses / countHotels", "totals a player's houses/hotels for the summary"],
            ["displayRoundSummary", "per-player cash, net worth, properties, railways, utilities, houses, hotels, loan, status"],
            ["countSolventPlayers", "how many players are not bankrupt"],
            ["playGame", "the main loop - cycles turns until every solvent player has passed GO, then does round-end bookkeeping; caps at 500 rounds"],
            ["determineWinner", "solvent player with the highest net worth; edge case: if everyone is bankrupt, still pick the highest net worth"],
            ["displayFinalResults", "winner block + final standings for all players"],
            ["startGame", "seed random - setup - determine turn order - playGame - results"],
        ],
        widths=[0.34, 0.66],
    )
    pdf.p("The recursive turn-order resolution is a nice talking point in a viva - "
          "it replaces a 'while loop until no ties' with clean recursion:")
    pdf.code_block(
        "resolveGroup(groupPlayers, n, output, startIndex)\n"
        "    roll for every player in group\n"
        "    sort the group by roll, highest first\n"
        "    walk the sorted list in runs:\n"
        "        run of 1  -> place that player directly in output\n"
        "        run of 2+ -> call resolveGroup on JUST those tied players\n"
        "    return how many players were placed"
    )
    pdf.explain(
        "This algorithm decides who plays first in a fair way. It is included "
        "because recursion is an exam-visible topic: 'show me something clever in "
        "your code' can be answered with exactly this.",
        "All players in the group roll a die. The group is sorted from highest to "
        "lowest roll. Walking down the sorted list, a player with a unique roll is "
        "placed straight into the output order; a run of players tied on the same "
        "roll is passed to resolveGroup AGAIN so only they re-roll. The function "
        "returns how many players it placed.",
        "The logic thinking: instead of a messy while(anyTie) loop, tying players "
        "are re-processed by the same routine - recursion mirrors the problem "
        "perfectly. Each recursive call reduces the group size, so the recursion "
        "always terminates, and the final order is strictly fair because ties are "
        "decided by fresh dice rolls.")

    # -- finance.c ---------------------------------------------------------
    pdf.h2("7.5  finance.c - money, rent, buying, buildings, taxes, bankruptcy")
    pdf.p("The biggest file (1076 lines) and the economic core. Almost every rule "
          "about moving money lives here.")
    pdf.table(
        ["Group", "Functions", "What it does"],
        [
            ["Ownership helpers", "stripOwnership, resetLoan, adjustOwnedCount, groupOf", "keeps owner -1 / counters / loan fields consistent everywhere"],
            ["Money", "receiveMoney, payMoney", "receive no-ops for bankrupts; payMoney triggers Risk Taker auto-sales and then bankruptcy+liquidation"],
            ["Taxes", "payTax, payCommunityFundTax", "Income Tax = rate x NET WORTH (clamped >= 0); Community Fund = rate x property value"],
            ["Mortgage", "findPropertyToMortgage, findMortgagedProperty, mortgageProperty, redeemMortgage, handleMortgageDecisions", "mortgage gives mortgageValue x market modifier; redeem costs 110%"],
            ["Rent", "calculateRent, calculateRailwayRent, calculateUtilityRent", "rent tables x modifiers x condition %"],
            ["Groups/buildings", "groupSize, ownsMonopoly, developGroup, constructBuildings", "even development (Rule 9), max 4 houses -> hotel"],
            ["Value/net worth", "calculatePropertyValue, calculateBuildingValue, calculateNetWorth", "net worth = cash + property + buildings - loan (Rule 15)"],
            ["Anti-speculation", "countUndevelopedProperties, sellUndevelopedPropertyToAuction, enforceAntiSpeculation", "force-auction surplus undeveloped property"],
            ["Strategy sales", "sellLowValueProperty, sellDecliningProperties", "Risk Taker survival sale; Trader dumps declining assets"],
            ["Buying", "buyProperty, wouldCompleteMonopoly", "market price, strategy decides, else auction (Rule 5)"],
            ["Rent payment", "payRent", "checks who owns, skips if mortgaged/closed/damaged/BI, transfers rent"],
        ],
        widths=[0.22, 0.38, 0.40],
        font_size=7.7,
    )

    pdf.h3("How rent is calculated (calculateRent)")
    pdf.code_block(
        "if hotel          -> rent = baseRent * 10\n"
        "else by houses:   0 -> *1, 1 -> *2, 2 -> *3, 3 -> *5, 4 -> *7\n"
        "\n"
        "rent = rent * group-rent-modifier / 100      (MOD_GROUP_RENT)\n"
        "rent = rent * global-rent-modifier / 100     (MOD_RENT_GLOBAL)\n"
        "if hotel: rent = rent * hotel-rent-mod / 100 (MOD_HOTEL_RENT)\n"
        "if developed: rent = rent * conditionPercent / 100   (Table 3)"
    )
    pdf.explain(
        "This is the exact formula for rent on a colour property - probably the "
        "most quoted formula in the whole viva. It is given its own page so you can "
        "point at each line while explaining.",
        "Base rent is multiplied by a houses/hotel table (0 houses = x1 up to "
        "hotel = x10). Then each active economy modifier is applied as a "
        "percentage: the colour group's rent modifier, the global rent modifier, "
        "and for hotels an extra hotel modifier. Finally, if there are buildings, "
        "rent is scaled by the building's condition percent, so a run-down building "
        "earns less.",
        "The logic is layered: first 'how many buildings' (the player's own "
        "investment), then 'what the economy is doing' (temporary modifiers), then "
        "'how well maintained' (the wear-and-tear system). Multiplication in "
        "percent form (/100) stacks bonuses the way the rules intend, and the "
        "condition stage connects building health directly to income.")
    pdf.p("Condition percent (rentConditionPercent in economy.c): condition >= 90 -> 100%, "
          ">= 75 -> 90%, >= 50 -> 75%, >= 25 -> 50%, below 25 -> 0% (closed).")
    pdf.p("Railway rent is 250/500/1000/2000 depending on how many railways the same "
          "owner holds (x2 rent modifiers). Utility rent is 4x the dice if one utility "
          "is owned, 10x the dice if both are owned (x2 utility/global rent modifiers).")

    pdf.h3("Buying -> if the buyer refuses, an auction runs (Rule 5)")
    pdf.code_block(
        "buyProperty(game, playerIndex)\n"
        "  price = currentMarketValue(pos)\n"
        "  if PROPERTY: price *= purchase-price-modifier (boom +15%)\n"
        "  wantsToBuy = shouldBuyProperty(...)\n"
        "  if cash < price: wantsToBuy = 0\n"
        "  if !wantsToBuy -> runAuction(pos, seller = -1)   // Rule 5\n"
        "  else -> payMoney, set owner, increment owned counter"
    )
    pdf.explain(
        "This is the 'buy or auction' decision (Rule 5). It is included as its own "
        "page because it explains a key rule twist: a player who refuses to buy "
        "does NOT leave the square unowned - an auction fixes that.",
        "The price comes from currentMarketValue so booms, declines and inflation "
        "are all reflected. Colour properties add a purchase-price modifier (a "
        "boom makes them 15% pricier). The strategy's shouldBuyProperty says yes "
        "or no; cash is the hard gate - you cannot buy what you cannot afford. "
        "Refusal or poverty sends the square to runAuction with no seller, and a "
        "winning buyer pays the market price and gets ownership recorded.",
        "The design keeps every buyable square flowing: wanted properties are "
        "bought, unwanted or unaffordable ones go under the hammer. This makes the "
        "board dynamic and also cleans up a classic oversight - otherwise a "
        "refused property would just sit forever unowned.")
    pdf.h3("payMoney and bankruptcy (the safety wrapper)")
    pdf.p("This is one function every payment goes through, so bankruptcy handling "
          "is centralised. If the Risk Taker goes below zero, they first try to sell "
          "their cheapest undeveloped property (Section 3.4). If cash is still "
          "negative, the player is declared bankrupt, all assets are liquidated and "
          "auctioned, and cash is clamped to zero.")
    pdf.code_block(
        "while (cash < 0 && !bankrupt && strategy == RISK_TAKER):\n"
        "    before = countUndevelopedProperties(...)\n"
        "    sellLowValueProperty(...)          // cheapest undeveloped prop\n"
        "    if countUndevelopedProperties() >= before: break   // nowhere left to sell\n"
        "\n"
        "if cash < 0 and not bankrupt:\n"
        "    bankrupt = 1\n"
        "    liquidateBankruptAssets(player)      // demolish, unown, auction each square\n"
"        cash = 0                             // remaining debt is written off"
    )
    pdf.explain(
        "This is the single choke point every payment flows through. It is central "
        "because bankruptcy must look identical no matter which payment caused it - "
        "an examiner may ask 'what happens when a player cannot pay?' and this is "
        "the one true answer.",
        "First, only a Risk Taker gets a lifeline: while cash is negative they sell "
        "their cheapest undeveloped property, and the loop breaks if nothing was "
        "sold (you cannot sell the same property forever). If cash is still "
        "negative, the player is marked bankrupt, liquidateBankruptAssets "
        "demolishes buildings and auctions off every square, and cash is clamped "
        "to zero so a bankrupt player never holds negative money.",
        "Putting bankruptcy in one function means no other module can get it wrong - "
        "there is no second place that declares bankruptcy. The Risk Taker's "
        "auto-sell is a strategy difference: that personality refuses to die "
        "silently, while the others simply go bankrupt. `if count >= before: break` "
        "is a guard that stops infinite loops when there is nothing left to sell.")
    pdf.h3("Even development (Rule 9) - developGroup")
    pdf.p("A group can only be built on if the player owns the monopoly. developGroup "
          "always builds on the property with the fewest houses, so development stays "
          "even. A member that is mortgaged, damaged or loan-locked cannot be built on, "
          "and (bug fix) a blocked member with fewer than 4 houses also blocks the whole "
          "group from raising a hotel.")
    pdf.code_block(
        "developGroup(game, playerIndex, group)\n"
        "  if !ownsMonopoly -> return 0\n"
        "  pick target = owned property with the fewest houses (minHouses)\n"
        "    skip mortgaged / damaged / loan-locked members\n"
        "    a skipped member with < 4 houses means: no hotel for the group\n"
        "  never build a 5th house on a target already at 4 houses\n"
        "  if all four houses everywhere -> upgrade target to a HOTEL (houses = 0)\n"
        "  else -> add one HOUSE to the target\n"
        "\n"
        "constructBuildings() repeats this in a do/while loop (max 20 safety steps)\n"
        "so a player can build SEVERAL houses in one turn - the loop stops when\n"
        "nothing more can be built (Strategy says no, cash runs out, or fully built)."
    )
    pdf.explain(
        "Rule 9 (even development) is the trickiest construction rule - and it was "
        "the subject of a real bug found by the verifier. Its own page lets you "
        "explain the whole rule and the fix in one sitting.",
        "developGroup refuses to work unless the group is a monopoly. It then finds "
        "the owned property with the fewest houses - that is what 'even' means. "
        "Blocked members (mortgaged, damaged, loan-locked) are skipped, but a "
        "skipped member with fewer than 4 houses also stops the whole group from "
        "building a hotel. The target never receives a fifth house; instead the "
        "four houses upgrade to one hotel. constructBuildings repeats this in a "
        "do/while loop (capped at 20) so one turn can build several houses.",
        "The thinking: 'build wherever is least developed' naturally keeps groups "
        "even without a complicated planner, and the blocked-member guard closes "
        "the loophole the verifier caught. The loop maximum is pure safety - a "
        "richer player must never loop forever just because cash allowed it.")
    pdf.h3("Net worth (Rule 15)")
    pdf.code_block(
        "netWorth = cash\n"
        "         + currentMarketValue of every owned property (railway/util included)\n"
        "         + (houses * houseCost)  or  hotelCost for hotels\n"
        "         - outstanding loan amount\n"
        "\n"
        "note: mortgaged properties contribute ZERO to net worth"
    )
    pdf.explain(
        "Net worth determines the winner (Rule 15), so this formula is the scoring "
        "system itself. It is on its own page because 'how do you decide who wins?' "
        "is a guaranteed viva question.",
        "Start with cash. Add the real (current, inflation-adjusted) market value "
        "of every owned square, railways and utilities included. Add the money sunk "
        "into buildings - houses valued at house cost, or hotel cost where a hotel "
        "stands. Subtract any outstanding loan amount. Mortgaged properties count "
        "as zero.",
        "Using current market value instead of purchase price means booms and "
        "declines genuinely change the standings. Buildings add their build cost "
        "(you ARE worth what you invested) and loans subtract what you owe (debt "
        "is money you do not really have). A mortgaged property counting zero "
        "mirrors reality: you have borrowed against it, so it is not an asset you "
        "own outright.")
    pdf.hint("\u0d9a\u0dd4\u0dbd\u0dd2\u0dba (rent) \u0d9c\u0dab\u0db1\u0dca \u0d9a\u0dbb\u0db1\u0dca\u0db1\u0dda "
             "\u0db4\u0dd9\u0dbd\u0dd9\u0db1\u0dca \u0d91\u0d9a\u0dd2\u0db1\u0dca \u0d91\u0d9a: base x houses "
             "\u0d9c\u0dd4\u0dab\u0d9a\u0dcf\u0dbb\u0dba x modifiers x \u0dad\u0dad\u0dca\u0dad\u0dca\u0dc0\u0dba%.")

    # -- bank.c ------------------------------------------------------------
    pdf.h2("7.6  bank.c - loans, collateral and foreclosure")
    pdf.p("The Bank of Ceylon square (index 38) offers loans. The loan system is a "
          "mini-economy of its own: you pledge owned property as collateral, the bank "
          "lends you 75% of its value, interest is added to the balance every round, "
          "and if you default the collateral is seized.")
    pdf.table(
        ["Function", "Purpose"],
        [
            ["groupBasePrice", "the basis value of a colour group (the first property's price) used ONLY for loan math"],
            ["totalEligibleCollateral", "sum of group base prices (or rail/util mortgage values) that are owned, unmortgaged, un-pledged, x market modifier"],
            ["calculateMaxLoan", "75% of eligible collateral (Rule-LK 2)"],
            ["obtainLoan", "one loan at a time; locks every eligible property as collateral; pays out; 20 rounds at the current interest"],
            ["repayLoan", "partial or full repayment; on full repayment all collateral is released"],
            ["handleBankVisit", "one transaction per Bank landing: repay full / increase / extend / refinance, or obtain a new loan"],
            ["increaseLoan", "borrow 75% of newly-acquired collateral and add it to the loan"],
            ["extendLoan", "+10 rounds to the repayment deadline"],
            ["refinanceLoan", "switch the loan to the economy's current (lower) rate"],
            ["demolishBuildingsOn", "zero out houses/hotel (used on seizure and bankruptcy)"],
            ["foreclose", "default: pledged properties are demolished, unowned and auctioned; player bankrupt if nothing left"],
            ["processLoans", "every round: interest = amount x rate% added to principal; count down; at 0 -> foreclose"],
        ],
        widths=[0.30, 0.70],
    )
    pdf.p("The interest that is added each round is compounding interest: it is "
          "added to the principal, so next round's interest is higher. That makes "
          "long unpaid loans grow very fast.")
    pdf.code_block(
        "processLoans(game)\n"
        "  for each player with an active loan:\n"
        "    interest   = loan.amount * loan.interestRate / 100\n"
        "    loan.amount += interest              // COMPOUNDED\n"
        "    loan.remainingRounds--\n"
        "    if remainingRounds <= 0: foreclose(player)"
    )
    pdf.explain(
        "This is the heartbeat of the loan system - it runs once per round and "
        "makes every loan grow or die. It has its own page because 'how does "
        "interest work in your project?' is answered by exactly these four lines.",
        "For every player with an active loan, interest is computed as "
        "amount x rate% and written straight back into amount - that is compound "
        "interest. Then remainingRounds drops by one, and the moment it hits zero "
        "the bank forecloses: pledged property is seized and auctioned.",
        "Compounding means interest is charged on previously added interest, so "
        "unpaid loans snowball - that is intentional pressure on the player. The "
        "foreclose at zero is the deadline made real; there is no hidden extension. "
        "This single routine guarantees interest is applied exactly once per round, "
        "consistently, for every player.")
    pdf.hint("\u0dab\u0dba\u0d9a\u0dca = \u0d87\u0db4 (collateral) \u0db8\u0dad \u0db4\u0daf\u0db1\u0db8\u0dca "
             "\u0dc0\u0dd6 lenders 75%; \u0db4\u0ddc\u0dbd\u0dd2\u0dba \u0dc3\u0dd1\u0db8 round \u0d91\u0d9a\u0dd2\u0db1\u0dca \u0d91\u0d9a "
             "\u0db8\u0dd4\u0daf\u0dbd\u0da7 \u0d91\u0d9a\u0dad\u0dd4 \u0dc0\u0dda (\u0da0\u0d9a\u0dca\u200d\u0dbb\u0dc0\u0dd8\u0dad\u0dca\u0dad\u0dd2 \u0db4\u0ddc\u0dbd\u0dd2).")

    # -- auction.c ---------------------------------------------------------
    pdf.h2("7.7  auction.c - the auction engine")
    pdf.p("When nobody buys a square directly, or a forced sale happens, runAuction "
          "sells it to the highest bidder among all solvent players.")
    pdf.table(
        ["Function", "Purpose"],
        [
            ["getAskingValue", "current market value x auction-price modifier (declining groups start -25%)"],
            ["runAuction", "opening = value/2; bids must rise by 250; a player who passes is out forever; seller never bids; winner pays; seller (if any) receives the money"],
        ],
        widths=[0.30, 0.70],
    )
    pdf.code_block(
        "runAuction(propIndex, sellerIndex)\n"
        "  openingBid = askingValue / 2\n"
        "  active = all solvent players except the forced seller (seller excluded - bug fix)\n"
        "  while activeCount > 1 (max 200 safety rounds):\n"
        "      each active player:\n"
        "          candidate = currentBid + 250\n"
        "          willingToBid()?  -> bids, become highBidder\n"
        "          else             -> out of the auction for good\n"
        "  special cases: single remaining bidder gets one final chance;\n"
        "  if no one bid, the property stays with the Bank\n"
        "  winner pays currentBid; sellerIndex >= 0 receives it; ownership transferred"
    )
    pdf.explain(
        "This is the auction engine - used both when someone refuses to buy and "
        "when the Anti-Speculation Act forces a sale. It has its own page because "
        "'what happens at an auction?' often turns into a follow-up question.",
        "The bidding starts at half the asking value, and every bid must beat the "
        "current one by at least 250 LKR. Each active player gets a chance to bid "
        "and, once they pass, they are out for good. The loop ends when one bidder "
        "remains (capped at 200 rounds as a safety net), the last bidder gets one "
        "final chance, and a property nobody bids on stays with the Bank. The "
        "winner pays their bid and, if it was a forced sale, the original seller "
        "receives the money.",
        "The crucial logic is the seller exclusion - that is the verbatim bug fix "
        "an examiner may ask about. Starting at half value encourages bidding, the "
        "250 rise keeps maths simple (no decimals, always integers), and permanently "
        "dropping passers prevents stalls. The 200-round cap means even a silly "
        "auction terminates.")
    pdf.note("Why exclude the seller? Without that bug fix, a forced seller could bid on "
             "their own property, win it, and 'pay' themselves - a net-zero transfer that "
             "defeats the Anti-Speculation Act. Paying the bid to yourself is exactly neutral, "
             "so the forced sale would never actually change ownership.")

    # -- events.c ----------------------------------------------------------
    pdf.h2("7.8  events.c - cards, economic events and regulations")
    pdf.p("Three kinds of 'shocks' to the economy come from this file. Almost every "
          "effect is implemented by adding a timed modifier to the economy - it never "
          "permanently changes a base price.")
    pdf.table(
        ["Function", "Purpose"],
        [
            ["clampLoanInterest / adjustLoanInterest", "keep the economy interest rate in [1, 25] and move it by a step"],
            ["executeEvent", "20 national event cards, drawn from a cycling deck (0..19); effects include rent boosts, disasters, interest changes, tax amnesty, grants..."],
            ["triggerEconomicEvent", "1 of 8 random economy-wide events every 15 rounds"],
            ["triggerGovernmentRegulation", "1 of 8 random regulations every 20 rounds (tax rise, luxury tax, subsidies, Anti-Speculation Act...)"],
            ["decrementEventTimers", "count down non-modifier timers (construction suspension, closed property)"],
        ],
        widths=[0.38, 0.62],
    )
    pdf.p("The 20 national cards (Appendix A of the assignment) map to cases 0-19:")
    pdf.code_block(
        " 0 Tourism Hype        hotel rent x2          (5 rounds)\n"
        " 1 Fuel Shortage       railway rent x2        (5 rounds)\n"
        " 2 Heavy Floods        random property damaged (disaster)\n"
        " 3 Political Rally     one owned property closed for 2 rounds\n"
        " 4 Stock Market Rise   all values +10%        (15 rounds)\n"
        " 5 Economic Downturn   all values -15%        (15 rounds)\n"
        " 6 Housing Subsidy     construction -30%      (15 rounds)\n"
        " 7/8 Interest Cut/Rise interest +/- 2 points\n"
        " 9 Tax Amnesty         everyone +2000\n"
        " 10 Power Failure      utility rent /2        (3 rounds)\n"
        " 11 Foreign Funding    Orange group +15%      (15 rounds)\n"
        " 12 Port Expansion     railway values +20%    (15 rounds)\n"
        " 13 Festival Season    hotel rent +50%        (5 rounds)\n"
        " 14 Labour Strike      construction suspended (2 rounds)\n"
        " 15 Insurance Discount premiums -20%          (10 rounds)\n"
        " 16 Property Revaluation random group +15%    (15 rounds)\n"
        " 17 Currency Deprecia. construction +10%      (15 rounds)\n"
        " 18 Government Grant   5000 to a random SOLVENT player (bug fix: not bankrupt)\n"
        " 19 National Disaster  random developed property damaged (disaster)"
    )
    pdf.explain(
        "These are the 20 national event cards that can fire when a player lands on "
        "an EVENT square. The list is included because an examiner may name a card "
        "and ask you to explain how it is implemented - knowing the mapping makes "
        "that trivial.",
        "Each case 0..19 maps to one effect: rent boosts and cuts, disasters, "
        "interest-rate changes, tax amnesty, subsidies, a government grant and a "
        "national disaster. Some change prices (implemented as timed modifiers), "
        "some change interest rates, some directly hit property (damage).",
        "The deck is implemented as a running counter (0..19 then wrap) instead of "
        "a real shuffled deck, so every card is eventually drawn in a fixed cycle "
        "with no shuffle code needed. Economic events and regulations use rand() % 8 "
        "because they are meant to be random. Card 18 was fixed so the grant goes "
        "only to a solvent player, and card 3's luxury tax prints per property - "
        "two real bug fixes.")
    pdf.p("The deck is a simple counter: currentCardIndex rises 0 -> 19 then wraps to 0. "
          "That is equivalent to 'draw the top card, put it at the bottom of the deck' "
          "without needing a real deck data structure.")
    pdf.p("The 8 economic events and 8 government regulations are chosen randomly with "
          "rand() % 8. Regulation case 7 activates the Anti-Speculation Act, and "
          "regulation case 3 charges a 25% luxury tax on every hotel (printed per "
          "player/property - bug fix).")

    # -- economy.c ---------------------------------------------------------
    pdf.h2("7.9  economy.c - inflation, modifiers, ageing, maintenance")
    pdf.p("The modifier system is the cleverest part of the project. Instead of "
          "permanently changing prices when events happen, every effect is stored as "
          "an ActiveModifier with a fixed % and a countdown. All matching modifiers "
          "multiply together, so two +25% bonuses are not +50% but roughly +56% "
          "(that is Rule-LK 34 - they are cumulative).")
    pdf.table(
        ["Function", "Purpose"],
        [
            ["initEconomy", "zero modifiers, base interest/tax, card index 0"],
            ["applyRate", "Old x (1 + rate/100), never below 1"],
            ["addModifier / addSourcedModifier", "append a timed effect (source = general/boom/decline/regional)"],
            ["modifierMultiplier", "multiply every matching modifier's % together; 100 = no effect"],
            ["isModifierActive", "is at least one matching modifier running? (flag effects)"],
            ["decrementModifiers", "tick each countdown down; remove (compact the array) expired ones"],
            ["formatLKR", "30000 -> \"30,000\" (thousands separators)"],
            ["applyInflation", "every 10 rounds a random rate from {-3,0,2,5,8,12}% is permanently applied to price/rent/mortgage/house/hotel costs of every buyable square"],
            ["currentMarketValue", "the single truth for 'real price': purchasePrice x (1 - depreciation) x all value modifiers"],
            ["currentTaxRatePercent", "base tax rate x global value modifier"],
            ["ageProperties", "age +1 per round; past 50, +5% depreciation per 5 rounds, capped at 30%"],
            ["tryRenovateAgeDepreciation", "landing on your own aged property: pay 10% -> age/depreciation reset, baseRent +5%"],
            ["rentConditionPercent", "Table 3 mapping condition -> rent %"],
            ["ageBuildings", "condition -2 per round; 20+ rounds of neglect -> structural damage (-15% value, -25% rent, x150% repair)"],
            ["performMaintenance", "restore condition to 100: hotel -> 8% of hotel cost, house -> 5% of house cost"],
            ["renovateStructuralDamage", "pay 150% of replacement value to undo structural damage and restore pre-damage price/rent"],
        ],
        widths=[0.34, 0.66],
    )
    pdf.code_block(
        "currentMarketValue(pos)\n"
        "  price = purchasePrice\n"
        "  price -= price * depreciation / 100         // age depreciation\n"
        "  mult  = MOD_VALUE_GLOBAL (all values)\n"
        "  mult *= MOD_GROUP_VALUE (this colour group)  if property\n"
        "  mult *= MOD_RAIL_VALUE  if railway\n"
        "  mult *= MOD_INDEX_VALUE (this exact square)\n"
        "  return price * mult / 100"
    )
    pdf.explain(
        "This is the single 'real price' formula of the whole game. It is on its "
        "own page because it is the mechanism behind booms, declines, inflation and "
        "renovation - and the reason no two modules can disagree on a price.",
        "Start from the stored purchasePrice. Subtract age depreciation (a percent "
        "of the price). Build a multiplier by multiplying every matching modifier "
        "together: the global value modifier applies to everything, the colour "
        "group's modifier applies to properties, the railway modifier to railways, "
        "and a per-square index modifier to that exact square. Return "
        "price x multiplier / 100.",
        "The thinking is that events NEVER change base prices permanently - they "
        "only stack temporary multipliers, so values drip back to normal when "
        "timers expire. buy price, insurance, auction, net worth all call this one "
        "function, so the game can never silently disagree with itself. Combining "
        "modifiers by multiplication (not addition) is Rule-LK 34.")
    pdf.p("Because buyPrice, insurance premiums/repairs, renovation, net worth and "
          "auction values ALL call currentMarketValue, every part of the game always "
          "sees the same 'real price' - no numbers can disagree.")
    pdf.hint("\u0db8\u0dd9\u0dba stage \u0d91\u0d9a\u0dba\u0dd2: \u0dc3\u0dd2\u0daf\u0dd4\u0dc0\u0dd3\u0db8\u0dca "
             "\u0db8\u0dd6\u0dbd\u0dd2\u0d9a \u0db8\u0dd2\u0dbd \u0dc0\u0dd9\u0db1\u0dc3\u0dca \u0db1\u0ddc\u0d9a\u0dbb\u0dba\u0dd2 - "
             "\u0daf\u0dd2\u0dba\u0dd4\u0dab\u0dd4 / \u0db4\u0dc4\u0dad \u0d9a\u0dd2\u0dbb\u0dd3\u0db8 "
             "modifiers \u0dc0\u0dbd\u0dd2\u0db1\u0dca \u0d9a\u0dbd\u0dca \u0db4\u0db8\u0dab\u0d9a\u0dca.")

    # -- insurance.c -------------------------------------------------------
    pdf.h2("7.10  insurance.c - policies, disasters, repairs")
    pdf.p("Every 10 rounds (or via event cards 2/19) one random developed property "
          "may be hit by a disaster. Insurance softens the blow.")
    pdf.table(
        ["Function", "Purpose"],
        [
            ["propertyValue / repairCost", "value = currentMarketValue; repair cost = 30% of value"],
            ["isCovered", "Basic covers only Fire + Flood; Comprehensive and Business Interruption cover everything"],
            ["compensationPercent", "Basic 80%, Comprehensive/BI 100%"],
            ["pickDisaster", "weighted random: 5 types at weight 20 each; Heavy Monsoon boosts flood by +30, Political Unrest boosts riot by +30"],
            ["purchaseInsurance", "premium = value x (5/10/15)% x insurance modifier; 20 rounds"],
            ["findPropertyToInsure / findPropertyToRenew", "which property to buy a first policy / renew near expiry (<= 10 rounds)"],
            ["handleInsuranceVisit", "renew first, otherwise buy a new policy per the strategy"],
            ["tryAutoRepair", "start of turn: if the owner can afford repairCostOwed, repair it (prints the cost - bug fix) and rent resumes"],
            ["payCompensation", "pays the owner; Business Interruption also (a) gets 5 rounds of lost income, (b) claims are x150% during political unrest"],
            ["triggerDisaster", "pick a random developed property, pick a disaster, compute repair cost; insured -> compensation; uninsured -> owner marked sufferedLoss; remainder owed = damaged and earns no rent"],
            ["processInsuranceExpiry", "count down policies; warn at 3 rounds; expire at 0 -> no insurance"],
        ],
        widths=[0.34, 0.66],
    )
    pdf.code_block(
        "triggerDisaster(game)\n"
        "  collect all developed properties (houses > 0 or hotel)\n"
        "  if none exist -> nothing happens\n"
        "  chosen  = a random developed property\n"
        "  disaster = pickDisaster (weighted by flood/riot risks)\n"
        "  cost    = 30% of current market value\n"
        "  if covered:\n"
        "      compensation = cost x 80%/100%\n"
        "      BI policies also set lostIncomeRoundsLeft = 5\n"
        "      repairCostOwed = cost - compensation  (usually 0 for full cover)\n"
        "  else:\n"
        "      owner.sufferedLoss = 1   (Risk Taker now wants insurance!)\n"
        "      repairCostOwed = cost\n"
        "  if repairCostOwed > 0: damaged = 1   // no rent until repaired"
    )
    pdf.explain(
        "This is the disaster engine - the reason insurance exists in the game. It "
        "is on its own page because it answers 'how does damage work?' and 'why do "
        "players buy insurance?' in one flow.",
        "Every 10 rounds (or via event cards) the game collects all developed "
        "properties; if none exist nothing happens. One random developed property "
        "is chosen and a disaster type is picked (weights favour flood or riot when "
        "the related events are active). Repair cost is 30% of market value. If "
        "insured, compensation covers 80%/100% and Business Interruption policies "
        "protect 5 rounds of income; otherwise the owner is marked sufferedLoss. "
        "Whatever is still owed marks the property damaged = no rent until paid.",
        "Insurance changes a total loss into a manageable one - that is the "
        "motivation for the insurance square. Uninsured losses set sufferedLoss, "
        "which is exactly what flips the Risk Taker strategy to 'now I want "
        "insurance'. `damaged = 1` ties damage directly to income: a broken "
        "property earns nothing until repaired, which drives the repair loop at "
        "the start of each turn.")

    # -- market.c ----------------------------------------------------------
    pdf.h2("7.11  market.c - market review, regional cards, report")
    pdf.p("The property market behaves like a real economy: colour groups boom and "
          "decline on a cycle, and regional development cards give location-specific "
          "bonuses.")
    pdf.table(
        ["Function", "Purpose"],
        [
            ["initMarket", "clear group cooldowns and last boom/decline groups"],
            ["groupName", "enum -> text (Brown, Light Blue, ...)"],
            ["pickEligibleGroup", "random group not on cooldown and not one of the excluded ones"],
            ["reviewPropertyMarket", "every 10 rounds: boom group (+20% value, +25% rent, +15% mortgage/purchase, +10% construction) and decline group (-15% value, -20% rent, -10% mortgage, auction -25%); each for 10 rounds; 30-round cooldown"],
            ["drawRegionalCard", "1 of 12 Sri Lanka themed regional cards, 15 rounds each"],
            ["displayMarketConditions", "Rule-LK 36 report: boom/decline/regional/other active effects + inflation + interest + tax rate"],
        ],
        widths=[0.34, 0.66],
    )
    pdf.p("All these effects are added as sourced modifiers (SRC_BOOM / SRC_DECLINE / "
          "SRC_REGIONAL), which lets the end-of-round report group them into the "
          "correct sections.")

    pdf.h2("7.12  functions.h - the project's 'API'")
    pdf.p("functions.h is a header file that only declares functions - it contains no "
          "logic. It has two protective lines (#ifndef ... #define ... #endif) so it "
          "can be included many times without error. It is organised by module with "
          "comment banners (board.c, players.c, finance.c, ...), which makes it a great "
          "map of the whole project: read it and you have seen every function that exists.")
    pdf.p("In a viva you can use functions.h as your index: point at the section "
          "comment and explain what that module is responsible for.")


# --------------------------------------------------------------------------
# rules quick reference
# --------------------------------------------------------------------------

def section_rules(pdf):
    pdf.h1("8", "Game Rules - Quick Reference")
    for head, body in [
        ("Money", [
            "Everyone starts with LKR 30,000.",
            "Passing (or landing on) GO gives LKR 2,000.",
            "All amounts print in LKR with thousands separators (formatLKR).",
        ]),
        ("Board", [
            "40 squares, indices 0..39 (board.c). Rent/price values are set once and only permanently change via inflation.",
            "22 colour properties in 8 groups, 4 railways, 2 utilities, 12 special squares.",
        ]),
        ("Turn order", [
            "Decided by recursive dice roll-off - ties re-roll until a strict order exists.",
        ]),
        ("Rent (Table 6)", [
            "0 houses: x1, 1: x2, 2: x3, 3: x5, 4: x7, hotel: x10 of base rent.",
            "Railways: 250/500/1000/2000 depending on how many the owner holds (Table 7).",
            "Utilities: 4x dice (one owned) or 10x dice (both owned) (Table 8).",
            "Every rent is then scaled by active rent modifiers and, for developed properties, by condition % (Table 3).",
            "No rent if the square is mortgaged, politically closed, disaster-damaged, or in BI lost-income.",
        ]),
        ("Buying", [
            "Price = currentMarketValue (x purchase-price modifier for colour groups).",
            "If the landing player refuses (or cannot pay), an auction runs (Rule 5).",
        ]),
        ("Building (Rule 9)", [
            "Only with a full monopoly of the colour group.",
            "Build on the property with the fewest houses (even development).",
            "Max 4 houses per property; the 4th house becomes a hotel.",
            "Blocked member (mortgaged/damaged/loaned) with < 4 houses blocks hotels for the group.",
            "Construction can be suspended by events or made cheaper/expensive by modifiers.",
        ]),
        ("Mortgage", [
            "Only undeveloped, un-pledged properties can be mortgaged.",
            "Payout = mortgageValue x market modifier; redemption costs 110%.",
            "Mortgaged properties earn no rent and count zero in net worth.",
        ]),
        ("Bank loans (Rule-LK 2-7)", [
            "One loan at a time; 75% of eligible collateral; interest per round added to the balance (compounding); 20-round term.",
            "Collateral = colour groups by their base price, rail/utils by mortgage value.",
            "Extend +10 rounds, refinance to current rate, increase against new collateral.",
            "Default -> foreclosure: pledged property seized and auctioned.",
        ]),
        ("Jail (Rule 13)", [
            "Go To Jail teleports to square 10 and marks the player.",
            "Doubles releases (no move that turn); bail 300; forced bail after 3 turns.",
        ]),
        ("Tax", [
            "Income Tax = market-scaled rate (base 15%, cap 25%) x net worth, clamped >= 0.",
            "Community Fund = 10% x property value.",
            "Luxury Property Tax (regulation) = 25% of each hotel's value, printed per owner.",
        ]),
        ("Insurance", [
            "Basic 5% (fire/flood, 80%), Comprehensive 10% (all, 100%), Business Interruption 15% (all, 100%, + protects 5 rounds of income).",
            "Premium = current value x % x insurance modifiers; 20 rounds.",
            "Heavy Monsoon boosts floods; Political Unrest boosts riots and BI claims.",
        ]),
        ("Disasters", [
            "Every 10 rounds one random developed property is hit.",
            "Repair cost = 30% of value. Uninsured owners carry repairCostOwed and earn nothing until repaired.",
            "Insured owners receive compensation; loss sets the Risk Taker's sufferedLoss flag.",
        ]),
        ("Ageing & maintenance", [
            "Properties age +1 per round; past 50, +5% depreciation per 5 rounds (max 30%).",
            "Renovation (10% of value) on your own square resets age and boosts base rent +5%.",
            "Developed buildings lose 2 condition per round; maintenance returns it to 100.",
            "20+ rounds of neglect = structural damage (value -15%, rent -25%, repair x150%).",
        ]),
        ("Market review (Rule-LK 30-34)", [
            "Every 10 rounds: one group booms, a different one declines, for 10 rounds; 30-round cooldown.",
            "All market effects are temporary modifiers - never permanent price changes.",
        ]),
        ("Cards & events", [
            "20 national cards (cycling deck) when landing on EVENT squares.",
            "1 of 8 economic events every 15 rounds; 1 of 12 regional cards every 15 rounds;",
            "1 of 8 government regulations every 20 rounds.",
        ]),
        ("Anti-Speculation Act (Rule-LK 8)", [
            "Max 3 undeveloped properties. After 5 consecutive rounds over the limit, the excess is force-auctioned and the seller cannot bid.",
        ]),
        ("Bankruptcy", [
            "Risk Taker first tries to sell its cheapest undeveloped property.",
            "Otherwise: buildings demolished, every property auctioned, cash zeroed, player removed.",
            "Bankrupt players take no further part (receiveMoney no-ops).",
        ]),
        ("Winning", [
            "Last solvent player wins; if several remain after 500 rounds, highest net worth wins.",
        ]),
    ]:
        pdf.h2("8.%d  %s" % (list(["Money", "Board", "Turn order", "Rent (Table 6)", "Buying", "Building (Rule 9)", "Mortgage", "Bank loans (Rule-LK 2-7)", "Jail (Rule 13)", "Tax", "Insurance", "Disasters", "Ageing & maintenance", "Market review (Rule-LK 30-34)", "Cards & events", "Anti-Speculation Act (Rule-LK 8)", "Bankruptcy", "Winning"]).index(head) + 1, head))
        pdf.bullets(body)


# --------------------------------------------------------------------------
# key algorithms
# --------------------------------------------------------------------------

def section_algorithms(pdf):
    pdf.h1("9", "Key Algorithms Explained")
    pdf.h2("9.1  Even development (Rule 9)")
    pdf.p("Goal: never pile houses on one property while a group-mate stays bare. "
          "developGroup scans the group, skips blocked members, and picks the property "
          "with the fewest houses. It returns 1 when something was built so that "
          "constructBuildings can immediately call it again - which is how a player "
          "raises several houses in a single turn.")
    pdf.h2("9.2  The modifier multiplication (Rule-LK 34)")
    pdf.p("Every temporary effect is a percent stored in Economy.modifiers. "
          "modifierMultiplier multiplies all matching percents together. A group whose "
          "value had +20% (boom) and +15% (event) is worth x1.20 x1.15 = x1.38, not "
          "x1.35 - that is 'cumulative', the rule's intention. 100 means 'no change', "
          "so the maths is always %/100.")
    pdf.h2("9.3  Compounding loan interest")
    pdf.p("Each round the interest is computed from the CURRENT balance and added to "
          "it. The balance therefore grows exponentially. Refinancing, repaying and "
          "extending are all tools to fight that growth.")
    pdf.h2("9.4  The real definition of a round")
    pdf.p("A round ends when every solvent player has passed GO at least once "
          "(tracked in passedGoThisRound[]). This is why playGame cycles turns and "
          "checks allPassed after every single turn, not after every 4 turns.")
    pdf.h2("9.5  Weighted disaster selection")
    pdf.p("5 disasters each start at weight 20. Extra flood/riot risk (from the Heavy "
          "Monsoon or Political Unrest events) adds +30 to that type. pickDisaster "
          "builds a total, rolls rand() % total, and walks the weights - a standard "
          "weighted-random draw.")
    pdf.h2("9.6  Recursive turn-order resolution")
    pdf.p("resolveGroup bubblesorts a group by dice roll and walks the sorted list. "
          "Runs of equal rolls are handed back to resolveGroup recursively. Each "
          "recursion reduces the tied group, so the recursion always terminates and "
          "produces a strict, fair order.")
    pdf.h2("9.7  Inflation model")
    pdf.p("Every 10 rounds one of {-3, 0, 2, 5, 8, 12}% is chosen. applyRate "
          "permanently changes purchasePrice, mortgageValue, baseRent, houseCost and "
          "hotelCost of every square (plus the loan interest rate). This is the ONLY "
          "place base values can permanently change - everything else is a temporary "
          "modifier on top.")


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------

def section_verification(pdf):
    pdf.h1("10", "Verification and Testing")
    pdf.p("The project is verified by generate-a-log-then-replay-it. The game prints "
          "every transaction to stdout; that log is saved; verify_analysis.py parses "
          "it line by line and checks it against a Python mirror of the rules.")
    pdf.h2("10.1  How verify_analysis.py works")
    pdf.bullets([
        "It mirrors the board constants (prices, rents, groups, players, inflation set) at the top of the file.",
        "An Analyzer object keeps live state: for every square - owner, mortgaged, houses/hotel, insurance, price, age, damaged - and for every player - position, cash, bankrupt, loan.",
        "Regex handlers match each log line type (rounds, dice+moves, GO payments, purchases, rent, construction, mortgages, loans, bankruptcy, auctions, insurance, taxes, disasters, market reviews, game-over arithmetic, final standings).",
        "It asserts the same invariants a human grader would check: dice in [2,12], (from+dice)%40 == to, rent payer != owner, no double loans, auction bidder pays, net worth = cash + property - loans, bankrupt players have 0 cash.",
        "Each mismatch is printed as [BUG] (invariant broken) or [REVIEW] (needs human judgement).",
    ])
    pdf.code_block(
        "python verify_analysis.py run.txt     # -> 0 confirmed bugs\n"
        "python verify_analysis.py run2.txt    # -> 0 confirmed bugs\n"
        "python verify_analysis.py test.txt    # <- the pre-fix log: shows the bugs"
    )
    pdf.explain(
        "This shows the verification workflow in action - three log files, three "
        "identical commands, three results. It is included because 'how did you "
        "test this?' is a viva staple, and this is concrete, repeatable evidence.",
        "run.txt and run2.txt are fresh post-fix game logs; running the verifier "
        "on them reports zero confirmed bugs. test.txt is a pre-fix log kept on "
        "purpose, so running the same tool over it still reproduces the six "
        "original bugs - proof that the tool actually detects them.",
        "The thinking: keep broken logs as test fixtures. A verifier that can "
        "prove it finds the old bugs is credible when it says the new logs are "
        "clean. Re-running is one command, so the whole regression check is "
        "reproducible by an examiner on the spot.")
    pdf.h2("10.2  The 6 confirmed bugs that were found and fixed")
    pdf.table(
        ["#", "Bug", "Where", "Root cause / fix"],
        [
            ["1", "Government Grant could go to a bankrupt player", "events.c (case 18)", "random player chosen without a solvent check; fix: scan forward to the first non-bankrupt player"],
            ["2", "Anti-Speculation forced seller could re-buy their own property", "auction.c runAuction", "seller could bid and 'pay themselves' (net-zero); fix: exclude the seller from bidding"],
            ["3", "Luxury Property Tax charged without printing", "events.c", "tax paid with no printf; fix: print owner, property and amount before paying"],
            ["4", "Disaster repair cost charged silently", "insurance.c tryAutoRepair", "repairs paid but never logged -> apparent cash gaps; fix: print 'Repair Cost : LKR N.'"],
            ["5", "Income Tax could pay a player (negative net worth)", "finance.c payTax", "13% x negative net worth = negative tax = cash gain; fix: clamp the amount to zero"],
            ["6", "Rule 9 even-development violated when a group member was blocked", "finance.c developGroup", "blocked member never cleared allFourHouses; fix: clear it, and guard against building a 5th house"],
        ],
        widths=[0.06, 0.30, 0.24, 0.40],
        font_size=7.7,
    )
    pdf.h2("10.3  What the analyzer's REVIEW items really mean")
    pdf.p("A few REVIEW lines are known model approximations, not bugs: the analyzer's "
          "value model does not perfectly simulate inflation/ageing timing, auction "
          "winners' receiving rent is printed after the payer's bankruptcy line (log "
          "ordering), and small residual net-worth diffs appear. The report's "
          "conclusion: 0 confirmed bugs on three fresh post-fix games.")
    pdf.hint("\u0db4\u0dbb\u0dd3\u0d9a\u0dca\u0dc2\u0dab \u0d9a\u0dca\u200d\u0dbb\u0db8\u0dba: \u0d9a\u0dca\u200d\u0dbb\u0dd3\u0da9\u0dcf\u0dc0 "
             "\u0db4\u0dd2\u0da7\u0dad\u0dd4 \u0d9a\u0dbb\u0db1 log \u0d91\u0d9a "
             "\u0db1\u0dd0\u0dc0\u0dad \u0d9a\u0dd2\u0dba\u0dc0\u0dcf \u0d9c\u0dd0\u0dc3\u0dd4\u0db8\u0dca "
             "\u0dc3\u0dad\u0dca\u200d\u0dba\u0dba \u0db4\u0dbb\u0dd3\u0d9a\u0dca\u0dc2\u0dcf \u0d9a\u0dbb\u0dba\u0dd2.")


# --------------------------------------------------------------------------
# viva Q&A
# --------------------------------------------------------------------------

def section_qa(pdf):
    pdf.h1("11", "Likely Viva Questions")
    qa = [
        ("Why is GameState declared as game[1] instead of just game?",
         "So we never have to write pointers. An array parameter decays to a pointer under the hood, so "
         "every function receives read/write access to the original state while the source only uses "
         "plain array syntax (game[0].field). It also makes 'pass the whole game' as trivial as passing "
         "one argument."),
        ("How do the four strategies differ?",
         "players.c is one big switch on PlayerType per decision. The Aggressive Investor completes "
         "monopolies aggressively, the Conservative Banker avoids risk and hotels while in debt, the Risk "
         "Taker spends everything and only insures after a loss, and the Opportunistic Trader buys cheap, "
         "sells into declines and flips assets."),
        ("What is a 'round' in your game?",
         "A round completes only when every solvent player has passed GO at least once, tracked in "
         "playedGoThisRound[]. This usually takes several turns per player. All round-end bookkeeping "
         "(loans, insurance expiry, ageing, modifiers, regulations) fires at that point."),
        ("How do you avoid permanently corrupting prices when events happen?",
         "Every effect is a timed ActiveModifier in Economy.modifiers[]. currentMarketValue multiplies "
         "all matching modifiers on the fly. When the timer hits zero, decrementModifiers removes it and "
         "values return to normal. The only permanent change is inflation via applyRate."),
        ("How is rent calculated?",
         "Base rent x a table multiplier by houses/hotel (x1,x2,x3,x5,x7,x10), then x each active rent "
         "modifier (group, global, hotel), then x the condition percent from Table 3. Railways and "
         "utilities have their own tables based on how many the owner has."),
        ("What happens on bankruptcy?",
         "The Risk Taker tries to sell its cheapest undeveloped property first. Otherwise "
         "liquidateBankruptAssets demolishes buildings, strips ownership and auctions every owned square. "
         "Cash is clamped to zero and the player receives no further money (receiveMoney no-ops)."),
        ("How does the loan system work?",
         "You pledge owned, unmortgaged, unlocked property as collateral worth 75% of its value. Interest "
         "is compounded into the balance every round. At zero rounds left, foreclose seizes and auctions "
         "the pledged property, and the player may become bankrupt."),
        ("Why is there a Python file in a C project?",
         "verify_analysis.py is a test tool, not part of the game. It replays a captured game log and "
         "checks every money movement, ownership change and dice roll against the rules. It found the six "
         "bugs listed in Section 10, all of which were fixed."),
        ("What was the hardest logic to get right?",
         "Rule 9 even development: a blocked group member must not only be skipped, it must also prevent "
         "the group from building a hotel, and build targets must never exceed 4 houses. The verification "
         "tool caught the violation and the fix is in developGroup."),
        ("What is the anti-speculation act?",
         "A regulation that limits a player to 3 undeveloped properties. After 5 rounds above the limit, "
         "the surplus is force-auctioned - and the seller is banned from bidding so they cannot buy it "
         "back at net-zero cost."),
        ("Which taxes exist?",
         "Income Tax: market-scaled rate x net worth, clamped at both 25% max and 0% minimum. Community "
         "Development Fund: 10% of property value. Luxury Property Tax: 25% of each hotel's value, a "
         "government regulation."),
        ("How is the winner decided?",
         "The last solvent player wins. If the game reaches round 500 with several players alive, "
         "determineWinner picks the highest net worth (cash + property + buildings - loans)."),
    ]
    for i, (q, a) in enumerate(qa, 1):
        pdf.h2("11.%d  %s" % (i, q), record=False)
        pdf.p(a)


# --------------------------------------------------------------------------
# function index
# --------------------------------------------------------------------------

FUNCTION_INDEX = [
    ("main.c", ["main"]),
    ("board.c", ["setProperty", "setRailway", "setUtility", "setSpecialSquare", "initializeBoard"]),
    ("players.c", ["initializePlayers", "shouldBuyProperty", "shouldConstruct", "wantsLoan",
                   "wantsToRepayLoan", "wantsIncreaseLoan", "wantsExtendLoan", "wantsRefinance",
                   "desiredInsurance", "shouldRenovateAgeDepreciation", "shouldMaintain",
                   "willingToBid", "shouldMortgage", "shouldRedeemMortgage", "shouldPayBail"]),
    ("finance.c", ["stripOwnership", "resetLoan", "adjustOwnedCount", "groupOf", "receiveMoney",
                   "payMoney", "liquidateBankruptAssets", "payTax", "payCommunityFundTax",
                   "findPropertyToMortgage", "findMortgagedProperty", "mortgageProperty",
                   "redeemMortgage", "handleMortgageDecisions", "calculateRent",
                   "calculateRailwayRent", "calculateUtilityRent", "groupSize", "ownsMonopoly",
                   "developGroup", "constructBuildings", "calculatePropertyValue",
                   "calculateBuildingValue", "calculateNetWorth", "countUndevelopedProperties",
                   "wouldCompleteMonopoly", "sellLowValueProperty", "sellDecliningProperties",
                   "sellUndevelopedPropertyToAuction", "forceSellExcess", "enforceAntiSpeculation",
                   "buyProperty", "payRent"]),
    ("bank.c", ["groupBasePrice", "totalEligibleCollateral", "calculateMaxLoan", "obtainLoan",
                "repayLoan", "handleBankVisit", "increaseLoan", "extendLoan", "refinanceLoan",
                "demolishBuildingsOn", "foreclose", "processLoans"]),
    ("auction.c", ["getAskingValue", "runAuction"]),
    ("events.c", ["clampLoanInterest", "adjustLoanInterest", "executeEvent",
                  "triggerEconomicEvent", "triggerGovernmentRegulation", "decrementEventTimers"]),
    ("economy.c", ["applyRate", "initEconomy", "addModifier", "addSourcedModifier",
                   "modifierMultiplier", "isModifierActive", "decrementModifiers", "formatLKR",
                   "applyInflation", "currentMarketValue", "currentTaxRatePercent", "ageProperties",
                   "tryRenovateAgeDepreciation", "rentConditionPercent", "ageBuildings",
                   "performMaintenance", "renovateStructuralDamage"]),
    ("insurance.c", ["propertyValue", "repairCost", "pickDisaster", "isCovered",
                     "compensationPercent", "purchaseInsurance", "findPropertyToInsure",
                     "findPropertyToRenew", "handleInsuranceVisit", "tryAutoRepair", "disasterName",
                     "payCompensation", "triggerDisaster", "processInsuranceExpiry"]),
    ("market.c", ["initMarket", "groupName", "pickEligibleGroup", "reviewPropertyMarket",
                  "drawRegionalCard", "printSectionHeader", "printBoomDecline",
                  "describeRegionalCondition", "printRegionalSection", "describeOtherCondition",
                  "printOtherConditions", "displayMarketConditions"]),
    ("game.c", ["rollDice", "movePlayer", "handleJail", "playTurn", "resolveGroup",
                "determineTurnOrder", "countHouses", "countHotels", "displayRoundSummary",
                "countSolventPlayers", "playGame", "determineWinner", "displayFinalResults",
                "startGame"]),
]


def section_index(pdf):
    pdf.h1("12", "Complete Function Index")
    pdf.p("Every function in the project, grouped by file. Useful for scanning "
          "'which file has what' in one place.")
    for fname, funcs in FUNCTION_INDEX:
        pdf.h2("12.%d  %s" % (FUNCTION_INDEX.index((fname, funcs)) + 1, fname), record=True)
        cols = 3
        rows = []
        row = []
        for fn in funcs:
            row.append(fn)
            if len(row) == cols:
                rows.append(row)
                row = []
        if row:
            while len(row) < cols:
                row.append("")
            rows.append(row)
        pdf.table([""] * cols, rows, widths=[0.34] * cols, font_size=8.0,
                  header_fill=(60, 80, 120))


# --------------------------------------------------------------------------
# appendix - full source
# --------------------------------------------------------------------------

def section_appendix(pdf):
    pdf.h1("13", "Appendix - Complete Source Code")
    pdf.p("All source files in full, as they exist in the project at the time this "
          "guide was generated. This section uses syntax-tinted code: green comments, "
          "red strings, blue numbers, navy keywords and grey preprocessor lines.")
    appendix_files = [
        ("A.1  types.h  -  the data model", "types.h"),
        ("A.2  functions.h  -  the project API", "functions.h"),
        ("A.3  main.c  -  entry point", "main.c"),
        ("A.4  board.c  -  board construction", "board.c"),
        ("A.5  players.c  -  the 4 AI strategies", "players.c"),
        ("A.6  game.c  -  the game engine", "game.c"),
        ("A.7  finance.c  -  the economic core", "finance.c"),
        ("A.8  bank.c  -  loans and foreclosure", "bank.c"),
        ("A.9  auction.c  -  the auction engine", "auction.c"),
        ("A.10  events.c  -  cards and regulations", "events.c"),
        ("A.11  economy.c  -  inflation and modifiers", "economy.c"),
        ("A.12  insurance.c  -  policies and disasters", "insurance.c"),
        ("A.13  market.c  -  market review and regional cards", "market.c"),
        ("A.14  verify_analysis.py  -  the verification analyzer", "verify_analysis.py"),
        ("A.15  Rent.csv  -  property price/rent data", "Rent.csv"),
    ]
    for title, rel in appendix_files:
        try:
            src = read_file(rel)
        except OSError:
            continue
        n = src.count("\n") + 1
        pdf.code_block(src, title="%s   (%d lines)" % (title, n))


# --------------------------------------------------------------------------
# main - two passes for the TOC page numbers
# --------------------------------------------------------------------------

def render_all(pdf, record):
    """Render every section. If record is True, section page numbers are saved."""
    pdf.recording = record
    section_overview(pdf)
    section_build(pdf)
    section_tree(pdf)
    section_architecture(pdf)
    section_data_model(pdf)
    module_main(pdf)
    section_rules(pdf)
    section_algorithms(pdf)
    section_verification(pdf)
    section_qa(pdf)
    section_index(pdf)
    section_appendix(pdf)


def render_cover(pdf):
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 297, "F")
    pdf.set_text_color(245, 245, 255)
    pdf.set_font("Arial", "B", 34)
    pdf.set_y(72)
    pdf.cell(0, 16, "MONOPOLY.LK", align="C")
    pdf.ln(20)
    pdf.set_font("Arial", "", 15)
    pdf.set_text_color(215, 224, 240)
    pdf.cell(0, 8, "A Sri Lanka themed Monopoly simulation in C", align="C")
    pdf.ln(22)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(190, 200, 220)
    pdf.cell(0, 7, "Viva Preparation Guide - every file, function and rule explained", align="C")
    pdf.ln(9)
    pdf.cell(0, 7, "With full source-code appendix", align="C")
    pdf.ln(30)
    pdf.set_font("Nirmala", "", 13)
    pdf.set_text_color(214, 224, 235)
    pdf.cell(0, 8, "\u0dc0\u0dd2\u0db7\u0dcf\u0d9c\u0dba\u0da7 \u0dc3\u0dd4\u0daf\u0dcf\u0db1\u0db8\u0dca \u0dc0\u0dd3\u0db8\u0dda \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0db8\u0dcf\u0dbb\u0dca\u0d9c\u0ddd\u0db4\u0daf\u0dda\u0dc1\u0dba", align="C")
    pdf.set_text_color(25, 25, 25)


def render_toc(pdf, entries, offset):
    """Render the table of contents using monospace alignment. Entries contain
    pass-1 page numbers; the displayed number is page + offset."""
    pdf.add_page()
    pdf.set_font("Arial", "B", 15)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, "Table of Contents", new_x="RIGHT", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Courier", "B", 8.5)
    pdf.set_text_color(25, 25, 25)
    shown = 0
    for title, lvl, page in entries:
        disp_page = page + offset
        indent = "        " if lvl else ""
        if lvl:
            pdf.set_font("Courier", "", 8.5)
        else:
            pdf.set_font("Courier", "B", 9)
        core = indent + title
        # fill with dots up to TOC_MAX_CHARS - page width, then page number
        pageno = str(disp_page)
        avail = TOC_MAX_CHARS - len(pageno) - 2
        if len(core) > avail:
            core = core[:avail - 2] + ".."
        line = core.ljust(avail, ".") + "  " + pageno
        pdf.write(h=5.0, text=line)
        pdf.ln(5.0)
        shown += 1
    return pdf.page_no()


def toc_page_count(entries):
    """Determine how many pages the TOC will occupy (monospace lines)."""
    lines = 0
    for title, lvl, _page in entries:
        core = ("        " if lvl else "") + title
        avail = TOC_MAX_CHARS - 6
        lines += max(1, math.ceil(len(core) / float(TOC_MAX_CHARS - 3)))
    lines += 4
    per_page = int(250 / 5.0)
    return max(1, math.ceil(lines / per_page))


def main():
    # pass 1 - collect section page numbers (content only; no cover/TOC yet)
    p1 = Guide()
    render_all(p1, record=True)
    entries = list(p1.toc_entries)

    eps = toc_page_count(entries)

    # pass 2 - render cover + TOC, then verify the TOC really takes `eps`
    # pages. Pages before the first content page = 1 (cover) + toc pages.
    out = Guide()
    render_cover(out)
    offset = eps + 1
    last = render_toc(out, entries, offset=offset)
    real_toc_pages = last - 1  # TOC starts on page 2 after the cover
    if real_toc_pages != eps:
        # rebase: recompute offset from the real TOC length and re-render
        out = Guide()
        render_cover(out)
        offset = real_toc_pages + 1
        last = render_toc(out, entries, offset=offset)
        assert last - 1 == real_toc_pages

    out.recording = False
    render_all(out, record=False)

    out_path = os.path.join(ROOT, "MONOPOLY_LK_Viva_Guide.pdf")
    out.output(out_path)
    print("PDF written: %s" % out_path)
    print("Pages: %d (TOC: %d pages)" % (out.pages_count, offset - 1))


if __name__ == "__main__":
    main()