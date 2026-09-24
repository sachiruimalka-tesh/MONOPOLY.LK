# -*- coding: utf-8 -*-
"""Generates MONOPOLY_LK_Code_Reference.pdf - a complete documentation of
every file, function, variable, macro, enum and struct field in the
MONOPOLY.LK project. Reads the structured data from code_docs_data.py."""

import math
import os
from fpdf import FPDF

from code_docs_data import (
    GAME_CYCLE_NOTE, MACROS, MACRO_CATEGORIES,
    ENUMS, STRUCTS, MODULES,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "MONOPOLY_LK_Code_Reference.pdf")
FONT_DIR = r"C:\Windows\Fonts"

# palette
NAVY = (16, 42, 92)
TEAL = (14, 116, 120)
INDIGO = (72, 61, 139)
SLATE = (31, 45, 61)
GRAY = (100, 116, 139)
LIGHT = (241, 245, 249)
BAR = (37, 99, 235)
BAR2 = (13, 148, 136)
CODE_BG = (250, 250, 252)
MUTED = (71, 85, 105)

CODE_LH = 4.6
A4W, A4H = 210, 297


class CodeReference(FPDF):
    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.recording = False
        self.toc_entries = []
        self.l_margin = 15
        self.r_margin = 15
        self.t_margin = 16
        self.b_margin = 18
        self.set_margins(self.l_margin, self.t_margin, self.r_margin)
        self.set_auto_page_break(True, self.b_margin)
        self.add_font("Arial", "", os.path.join(FONT_DIR, "arial.ttf"))
        self.add_font("Arial", "B", os.path.join(FONT_DIR, "arialbd.ttf"))
        self.add_font("Arial", "I", os.path.join(FONT_DIR, "ariali.ttf"))
        self.add_font("Arial", "BI", os.path.join(FONT_DIR, "arialbi.ttf"))

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 8, "MONOPOLY.LK  |  Source Code Reference  |  Page %d" %
                  self.page_no(), align="C")

    def col_heads(self, cols, widths, cell_w):
        self.set_font("Arial", "B", 8.0)
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        x0 = self.get_x()
        for c, w in zip(cols, widths):
            self.cell(cell_w * w, 6.5, "  " + c, fill=True)
        self.ln(6.5)
        self.set_text_color(25, 25, 25)

    def macro_summary(self):
        self.set_font("Arial", "", 9)
        for cat, title in MACRO_CATEGORIES:
            pals = [m for m in MACROS if m[2] == cat]
            if not pals:
                continue
            self.h2(title, record=False, size=9.5)
            widths = [0.34, 0.12, 0.54]
            cw = self.w - self.l_margin - self.r_margin
            self.set_font("Arial", "B", 7.8)
            self.set_fill_color(*NAVY)
            self.set_text_color(255, 255, 255)
            for c, w in zip(["Macro", "Value", "Purpose"], widths):
                self.cell(cw * w, 6, "  " + c, fill=True)
            self.ln(6)
            self.set_text_color(20, 20, 20)
            for name, val, _c, desc in pals:
                if self.get_y() > self.h - self.b_margin - 12:
                    self.add_page()
                tw = self.get_string_width("  " + desc)
                hn = 4.8
                if tw > cw * widths[2] - 2:
                    hn = 4.8 * math.ceil(tw / (cw * widths[2] - 2))
                self.set_font("Courier", "B", 7.6)
                self.cell(cw * widths[0], hn, "  " + name)
                self.set_font("Courier", "", 7.6)
                self.cell(cw * widths[1], hn, val)
                self.set_font("Arial", "", 7.8)
                self.multi_cell(cw * widths[2], 4.5, desc, align="L")
                self.ln(0.2)
            self.ln(1.2)

    # -- helpers -----------------------------------------------------------
    def h1(self, num, text):
        self.toc_entries.append((num + "  " + text, 0, self.page_no()))
        self.add_page()
        self.set_fill_color(*NAVY)
        self.rect(0, 0, A4W, 22, "F")
        self.set_font("Arial", "B", 17)
        self.set_text_color(255, 255, 255)
        self.set_y(6.5)
        self.cell(self.w - self.l_margin - self.r_margin, 8, "%s   %s" % (num, text))
        self.set_y(26)
        self.set_text_color(15, 23, 42)

    def h2(self, title, record=True, size=12.5):
        if self.get_y() > self.h - self.b_margin - 22:
            self.add_page()
        if record:
            self.toc_entries.append((title, 1, self.page_no()))
        self.ln(2)
        self.set_font("Arial", "B", size)
        self.set_text_color(*TEAL)
        self.cell(0, 7, title)
        self.ln(7)
        self.set_text_color(15, 23, 42)

    def p(self, text):
        self.set_font("Arial", "", 9.2)
        self.multi_cell(self.w - self.l_margin - self.r_margin, 4.8, text, align="J")
        self.ln(1.0)

    def note(self, text):
        self.set_font("Arial", "I", 8.4)
        self.set_text_color(*MUTED)
        self.multi_cell(self.w - self.l_margin - self.r_margin, 4.4, text, align="J")
        self.set_text_color(15, 23, 42)
        self.ln(1.0)

    def sig_banner(self, text):
        cw = self.w - self.l_margin - self.r_margin
        self.set_fill_color(*CODE_BG)
        self.set_draw_color(*SLATE)
        self.set_font("Courier", "B", 8.2)
        self.set_text_color(*NAVY)
        y0 = self.get_y()
        lines = []
        for raw in text.split("\n"):
            while self.get_string_width(raw) > cw - 6:
                cut = len(raw) - 1
                while cut > 0 and self.get_string_width(raw[:cut]) > cw - 6:
                    cut -= 1
                lines.append(raw[:cut])
                raw = raw[cut:]
            lines.append(raw)
        h = len(lines) * 4.8 + 4
        if self.get_y() + h > self.h - self.b_margin:
            self.add_page()
        self.rect(self.l_margin, y0, cw, h, "DF")
        y = y0 + 2
        for ln in lines:
            self.set_xy(self.l_margin + 3, y)
            self.cell(cw - 6, 4.8, ln)
            y += 4.8
        self.set_y(y + 1)

    def render_source(self, text, title="Actual source code"):
        """Draw the real C source, wrapping long lines, page-break aware."""
        cw = self.w - self.l_margin - self.r_margin
        self.set_font("Arial", "B", 8.6)
        self.set_text_color(*TEAL)
        self.cell(0, 5.6, title)
        self.ln(5.8)
        self.set_text_color(15, 23, 42)
        self.set_font("Courier", "", 7.4)
        lh = 4.2
        pad = 3
        top_pad = 1.5
        # build wrapped lines
        rows = []
        for raw in text.split("\n"):
            if raw.strip() == "":
                rows.append("")
                continue
            while self.get_string_width(raw) > cw - 2 * pad:
                cut = len(raw) - 1
                while cut > 0 and self.get_string_width(raw[:cut]) > cw - 2 * pad:
                    cut -= 1
                rows.append(raw[:cut].replace("\t", "    "))
                raw = raw[cut:]
            rows.append(raw.replace("\t", "    "))
        if self.get_y() + (min(len(rows), 6) * lh + top_pad + 4) > self.h - self.b_margin:
            self.add_page()
        i = 0
        while i < len(rows):
            if self.get_y() > self.h - self.b_margin - 2:
                self.add_page()
            y0 = self.get_y()
            if i == 0:
                self.set_y(y0 + top_pad)
            fit = 0
            avail = self.h - self.b_margin - self.get_y() - 1
            fit = int(avail // lh)
            if fit <= 0:
                self.add_page()
                continue
            chunk = rows[i:i + fit]
            h = len(chunk) * lh
            total_h = h + (top_pad if i == 0 else 0)
            self.set_fill_color(*CODE_BG)
            self.set_draw_color(203, 213, 225)
            self.rect(self.l_margin, y0, cw, total_h + (0.6 if i == 0 and False else 0.4), "DF")
            y = y0 + (top_pad if i == 0 else 0.2)
            for ln in chunk:
                self.set_xy(self.l_margin + pad, y)
                if ln:
                    self.set_font("Courier", "", 7.4)
                    self.cell(cw - 2 * pad, lh, ln)
                y += lh
            self.set_y(y + 0.6)
            i += fit

    def kv_field(self, label, value):
        self.set_font("Arial", "B", 8.6)
        self.set_text_color(*SLATE)
        self.cell(0, 5.2, label + "  ")
        self.set_font("Arial", "", 8.6)
        self.set_text_color(15, 23, 42)
        self.multi_cell(0, 5.2, value, align="L")
        self.ln(0.4)

    def param_table(self, rows, title="Parameters"):
        if not rows:
            return
        cw = self.w - self.l_margin - self.r_margin
        self.set_font("Arial", "B", 9)
        self.set_text_color(*TEAL)
        self.cell(0, 6, title)
        self.ln(6)
        self.set_text_color(25, 25, 25)
        self.set_font("Arial", "B", 8.4)
        self.cell(cw * 0.24, 6, "  Name", fill=True)
        self.cell(cw * 0.76, 6, "  Meaning", fill=True)
        self.ln(6)
        self.set_font("Arial", "", 8.2)
        for i, (name, desc) in enumerate(rows):
            if self.get_y() > self.h - self.b_margin - 14:
                self.add_page()
            if i % 2:
                self.set_fill_color(240, 244, 248)
                fill = True
            else:
                self.set_fill_color(255, 255, 255)
                fill = False
            h = 4.8
            self.set_font("Arial", "", 8.2)
            for chunk, w in ((name, cw * 0.24), (desc, cw * 0.76)):
                h2n = 4.8 * math.ceil(self.get_string_width(chunk) / (w - 2))
                h = max(h, h2n)
            self.set_font("Arial", "B", 8.2)
            self.multi_cell(cw * 0.24, h, "  " + name, fill=fill, align="L")
            self.set_xy(self.l_margin + cw * 0.24, self.get_y() - h)
            self.set_font("Arial", "", 8.2)
            self.multi_cell(cw * 0.76, h, "  " + desc, fill=fill, align="L")
            self.ln(0)
        self.ln(2)
        self.set_fill_color(255, 255, 255)

    def h3(self, title):
        if self.get_y() > self.h - self.b_margin - 18:
            self.add_page()
        self.ln(1)
        self.set_font("Arial", "B", 10)
        self.set_text_color(*INDIGO)
        self.cell(0, 6, title)
        self.ln(6)
        self.set_text_color(15, 23, 42)

    def bullets(self, items):
        for it in items:
            if self.get_y() > self.h - self.b_margin - 12:
                self.add_page()
            x0 = self.get_x()
            self.set_font("Arial", "", 9)
            self.cell(4, 4.8, "-")
            self.set_x(x0 + 4)
            self.multi_cell(self.w - self.l_margin - self.r_margin - 4, 4.8, it, align="L")
            self.ln(0.4)


# ---------------------------------------------------------------------------
# content sections
# ---------------------------------------------------------------------------

def render_cover(pdf):
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, A4W, A4H, "F")
    pdf.set_text_color(245, 248, 255)
    pdf.set_font("Arial", "B", 30)
    pdf.set_y(70)
    pdf.cell(0, 12, "MONOPOLY.LK", align="C")
    pdf.ln(14)
    pdf.set_font("Arial", "", 13)
    pdf.cell(0, 7, "A Sri Lanka themed Monopoly simulation in C", align="C")
    pdf.ln(16)
    pdf.set_font("Arial", "B", 19)
    pdf.set_text_color(125, 211, 252)
    pdf.cell(0, 9, "Complete Source Code Reference", align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(203, 213, 225)
    pdf.cell(0, 6, "Every file, function, variable, macro, enum and struct field", align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "I", 9.5)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 6, "Generated from the actual source code", align="C")


def render_intro(pdf):
    pdf.h1("1", "How to Use This Reference")
    pdf.p("This document describes ALL the code in the MONOPOLY.LK project: every "
          "source file, every function (signature, parameters, return value, local "
          "variables and step-by-step logic), every compile-time constant, every "
          "enum value and every struct field. Read it alongside the source files "
          "to prepare for a viva: each section below is grouped by module exactly "
          "as the code is organised. For every function and every source file, the "
          "ACTUAL C code is printed directly underneath its explanation, so you can "
          "compare what each function does with exactly how it does it.")
    pdf.p(GAME_CYCLE_NOTE)
    pdf.h2("Files covered")
    pdf.bullets([
        "types.h  -  all #define constants, enums and the data structures (Loan, Property, Square, Player, ActiveModifier, Economy, GameState).",
        "functions.h  -  the project API: every function prototype grouped by module.",
        "board.c  -  the 40-square Sri Lanka board.",
        "players.c  -  the 4 AI strategies and all decision functions.",
        "game.c  -  the game engine: turn loop, dice, movement, jail, rounds, winner.",
        "finance.c  -  money, rent, buying, mortgages, taxes, buildings, net worth, Anti-Speculation Act.",
        "bank.c  -  loans, collateral, foreclosure.",
        "auction.c  -  the auction engine.",
        "events.c  -  event cards, economic events, regulations.",
        "economy.c  -  inflation, modifiers, ageing, maintenance, value maths.",
        "insurance.c  -  insurance policies, disasters, repairs.",
        "market.c  -  boom/decline reviews, regional cards, market conditions.",
        "main.c  -  the entry point.",
    ])


def render_constants(pdf):
    pdf.h1("2", "Compile-Time Constants (types.h #define)")
    pdf.p("These constants drive every rule in the game. They are grouped by the "
          "rule area they belong to. Knowing them shows you understand the whole "
          "rulebook, since each one maps to a specific rule-LK or Section number.")
    pdf.macro_summary()


def render_enums(pdf):
    pdf.h1("3", "Enums and Data Structures (types.h)")
    sub = 1
    for ename, vals in ENUMS.items():
        pdf.h2("3.%d  enum %s" % (sub, ename))
        sub += 1
        cw = pdf.w - pdf.l_margin - pdf.r_margin
        colw = [cw * 0.30, cw * 0.70]
        pdf.set_font("Arial", "B", 8.4)
        pdf.cell(colw[0], 6, "  Value", fill=True)
        pdf.cell(colw[1], 6, "  Meaning", fill=True)
        pdf.ln(6)
        for i, (name, desc) in enumerate(vals):
            if pdf.get_y() > pdf.h - pdf.b_margin - 14:
                pdf.add_page()
            fill = i % 2 == 0
            hn = 4.8
            pdf.set_font("Arial", "", 8.2)
            for chunk, w in ((name, colw[0]), (desc, colw[1])):
                h2n = 4.8 * math.ceil(pdf.get_string_width(chunk) / (w - 2))
                hn = max(hn, h2n)
            pdf.set_font("Courier", "B", 8.2)
            pdf.multi_cell(colw[0], hn, "  " + name, fill=fill, align="L")
            pdf.set_xy(pdf.l_margin + colw[0], pdf.get_y() - hn)
            pdf.set_font("Arial", "", 8.2)
            pdf.multi_cell(colw[1], hn, "  " + desc, fill=fill, align="L")
            pdf.ln(0)
        pdf.ln(1.5)
    for sname, fields in STRUCTS.items():
        pdf.h2("3.%d  struct %s" % (sub, sname))
        sub += 1
        cw = pdf.w - pdf.l_margin - pdf.r_margin
        colw = [cw * 0.22, cw * 0.18, cw * 0.60]
        pdf.set_font("Arial", "B", 8.4)
        pdf.cell(colw[0], 6, "  Field", fill=True)
        pdf.cell(colw[1], 6, "  Type", fill=True)
        pdf.cell(colw[2], 6, "  Purpose", fill=True)
        pdf.ln(6)
        for i, (f, t, d) in enumerate(fields):
            if pdf.get_y() > pdf.h - pdf.b_margin - 16:
                pdf.add_page()
            fill = i % 2 == 0
            hn = 4.8
            pdf.set_font("Arial", "", 8.0)
            for chunk, w in ((f, colw[0]), (t, colw[1]), (d, colw[2])):
                h2n = 4.8 * math.ceil(pdf.get_string_width(chunk) / (w - 2))
                hn = max(hn, h2n)
            pdf.set_font("Courier", "B", 8.0)
            pdf.multi_cell(colw[0], hn, "  " + f, fill=fill, align="L")
            pdf.set_xy(pdf.l_margin + colw[0], pdf.get_y() - hn)
            pdf.set_font("Courier", "", 8.0)
            pdf.multi_cell(colw[1], hn, t, fill=fill, align="L")
            pdf.set_xy(pdf.l_margin + colw[0] + colw[1], pdf.get_y() - hn)
            pdf.set_font("Arial", "", 8.0)
            pdf.multi_cell(colw[2], hn, "  " + d, fill=fill, align="L")
            pdf.ln(0)
        pdf.ln(1.5)


def render_functions(pdf, source_map):
    pdf.h1("4", "Function Reference (module by module)")
    pdf.p("Each module below lists its functions alphabetically in source order. "
          "For every function you get: the exact signature, a plain-English purpose, "
          "the REAL source code, the return value, the parameters, the local "
          "variables, and the step-by-step logic. Each module also starts with its "
          "file header (includes and comments).")
    n = 0
    for fname, foverview, funcs in MODULES:
        n += 1
        pdf.h2("4.%d   %s" % (n, fname))
        pdf.p(foverview)
        preamble, by_name = source_map[fname]
        if by_name:
            pdf.h3("File header (includes / comments)")
            pdf.render_source("\n".join(preamble), title="")
        for fn in funcs:
            name, sig, purpose, params, ret, locals_, logic = fn
            pdf.h3(name)
            pdf.sig_banner(sig)
            if pdf.get_y() > pdf.h - pdf.b_margin - 20:
                pdf.add_page()
            pdf.p(purpose)
            pdf.render_source(by_name.get(name, "/* source not found: %s */" % name))
            pdf.param_table([("returns", ret)], title="Return value")
            pdf.param_table(params, title="Parameters")
            pdf.param_table(locals_, title="Local variables")
            if logic:
                pdf.h3("Logic")
                pdf.bullets(logic)
            pdf.ln(2)


def render_toc(pdf, entries, offset):
    pdf.add_page()
    TOC_MAX = 92
    pdf.set_font("Arial", "B", 17)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 9, "Table of Contents")
    pdf.ln(11)
    pdf.set_text_color(15, 23, 42)
    for title, lvl, page in entries:
        disp = page + offset
        indent = "        " if lvl else ""
        pdf.set_font("Courier", "B", 9 if not lvl else 8.5)
        core = indent + title
        pstr = str(disp)
        avail = TOC_MAX - len(pstr) - 2
        if len(core) > avail:
            core = core[:avail - 2] + ".."
        line = (core + "." * (avail - len(core)))
        if pdf.get_y() > pdf.h - pdf.b_margin - 8:
            pdf.add_page()
        pdf.cell(0, 5, line + "  " + pstr)
        pdf.ln(5)


def main():
    from extract_code import extract_by_module
    source_map = extract_by_module()

    p1 = CodeReference()
    render_intro(p1)
    render_constants(p1)
    render_enums(p1)
    render_functions(p1, source_map)
    entries = list(p1.toc_entries)

    # TOC size estimate
    lines = 0
    for title, lvl, _p in entries:
        core = ("        " if lvl else "") + title
        lines += max(1, math.ceil(len(core) / float(90)))
    toc_pages = max(1, math.ceil((lines + 6) / 50))

    out = CodeReference()
    render_cover(out)
    offset = toc_pages + 2
    render_toc(out, entries, offset=offset)
    render_intro(out)
    render_constants(out)
    render_enums(out)
    render_functions(out, source_map)
    out.output(OUT)
    print("PDF written: %s" % OUT)
    print("Pages: %d (TOC: %d pages)" % (out.page_no(), toc_pages))


if __name__ == "__main__":
    main()