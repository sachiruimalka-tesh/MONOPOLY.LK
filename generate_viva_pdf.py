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
        if title:
            self.set_font("Arial", "B", 9)
            self.set_text_color(*NAVY)
            self.multi_cell(0, 4.8, title, align="L")
            self.set_text_color(25, 25, 25)
            self.ln(0.8)
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
    pdf.note("`gcc *.c -o monopoly` produces a clean build with zero warnings or errors. "
             "Each .c file #includes types.h and functions.h, and main.c + game.c are the only "
             "places that need the whole picture.")
    pdf.p("To run the automatic verifier on a saved log:")
    pdf.code_block(
        "python verify_analysis.py run.txt   # replays the log and reports [BUG]/[REVIEW] items"
    )
    pdf.hint("\u0d9a\u0dca\u200d\u0dbb\u0dd3\u0da9\u0dcf\u0dc0 \u0d9a\u0dca\u200d\u0dbb\u0dd2\u0dba\u0dcf\u0dad\u0dca\u0db8\u0d9a "
             "\u0d9a\u0dd2\u0dbb\u0dd3\u0db8\u0da7 \u0db8\u0ddb\u0dad\u0dca\u200d\u0dbb\u0dd3 \u0d85\u0dc0\u0dc1\u0dca\u200d\u0dba "
             "\u0db1\u0dd0\u0dad.")


def section_tree(pdf):
    pdf.h1("4", "The Code Tree (File Structure)")
    pdf.p("Here is the whole project laid out as a tree, with the size of each file "
          "and a one-line description. Memorising this order (types -> headers -> "
          "game flow -> economy files) helps you describe the architecture in a viva.")
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
        "    cash = 0                             // remaining debt is written off"
    )

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

    pdf.h3("Net worth (Rule 15)")
    pdf.code_block(
        "netWorth = cash\n"
        "         + currentMarketValue of every owned property (railway/util included)\n"
        "         + (houses * houseCost)  or  hotelCost for hotels\n"
        "         - outstanding loan amount\n"
        "\n"
        "note: mortgaged properties contribute ZERO to net worth"
    )

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
        pdf.h2("%s   (%d lines)" % (title, n))
        pdf.code_block(src)


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