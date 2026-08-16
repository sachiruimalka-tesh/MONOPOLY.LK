#!/usr/bin/env python3
"""MONOPOLY-LK verification analyzer.

Programmatically parses a redirected stdout log (run.txt / test.txt) and
checks for bugs and anomalies following MonopolyLK_Verification_Technique.pdf:

  1. State-space consistency (square index <-> name)
  2. Ownership / assignment integrity
  3. Lifecycle / elimination handling
  4. Ledger / running-total spot-checks
  5. Final / summary arithmetic
  6. Range / bounds sanity
  7. Structural consistency

Usage:  python verify_analysis.py <logfile> [<logfile> ...]
"""

import re
import sys

# --------------------------------------------------------------------------
# Board constants, mirroring board.c / types.h (base values, pre-inflation)
# --------------------------------------------------------------------------
BOARD = {
    0: "GO", 1: "Pettah", 2: "Community Development Fund", 3: "Maradana",
    4: "Income Tax", 5: "Colombo Fort Railway Station", 6: "Bambalapitiya",
    7: "National Event Card", 8: "Wellawatte", 9: "Mount Lavinia",
    10: "Jail / Just Visiting", 11: "Nugegoda", 12: "Ceylon Electricity Board",
    13: "Maharagama", 14: "Kottawa", 15: "Kandy Railway Station",
    16: "Negombo", 17: "Sri Lanka Insurance", 18: "Katunayake", 19: "Ja-Ela",
    20: "Free Parking", 21: "Kandy City", 22: "National Event Card",
    23: "Peradeniya", 24: "Katugastota", 25: "Galle Railway Station",
    26: "Galle Fort", 27: "Unawatuna",
    28: "National Water Supply and Drainage Board", 29: "Hikkaduwa",
    30: "Go To Jail", 31: "Jaffna Town", 32: "Nallur",
    33: "Ceylinco Insurance", 34: "Trincomalee", 35: "Jaffna Railway Station",
    36: "National Event Card", 37: "Nuwara Eliya", 38: "Bank of Ceylon",
    39: "Galle Face",
}

NAME2IDX = {v: k for k, v in BOARD.items()}

PROP_TYPE = {1, 3, 6, 8, 9, 11, 13, 14, 16, 18, 19, 21, 23, 24, 26, 27,
             29, 31, 32, 34, 37, 39}
RAIL_TYPE = {5, 15, 25, 35}
UTIL_TYPE = {12, 28}

GROUP = {1: "BROWN", 3: "BROWN", 6: "LB", 8: "LB", 9: "LB", 11: "PINK",
         13: "PINK", 14: "PINK", 16: "ORANGE", 18: "ORANGE", 19: "ORANGE",
         21: "RED", 23: "RED", 24: "RED", 26: "YELLOW", 27: "YELLOW",
         29: "YELLOW", 31: "GREEN", 32: "GREEN", 34: "GREEN", 37: "DB",
         39: "DB"}

BASE_PRICE = {1: 1500, 3: 1800, 6: 2500, 8: 2700, 9: 3000, 11: 3500,
              13: 3800, 14: 4000, 16: 4500, 18: 4700, 19: 5000, 21: 5500,
              23: 5800, 24: 6000, 26: 6500, 27: 6800, 29: 7000, 31: 8000,
              32: 8300, 34: 8500, 37: 10000, 39: 12000}
BASE_HCOST = {1: 500, 3: 500, 6: 750, 8: 750, 9: 750, 11: 1000, 13: 1000,
              14: 1000, 16: 1250, 18: 1250, 19: 1250, 21: 1500, 23: 1500,
              24: 1500, 26: 2000, 27: 2000, 29: 2000, 31: 2500, 32: 2500,
              34: 2500, 37: 3000, 39: 3000}
BASE_TCOST = {1: 2000, 3: 2000, 6: 3000, 8: 3000, 9: 3000, 11: 4000,
              13: 4000, 14: 4000, 16: 5000, 18: 5000, 19: 5000, 21: 6000,
              23: 6000, 24: 6000, 26: 8000, 27: 8000, 29: 8000, 31: 10000,
              32: 10000, 34: 10000, 37: 12000, 39: 12000}
BASE_MORTGAGE = {1: 750, 3: 900, 6: 1250, 8: 1350, 9: 1500, 11: 1750,
                 13: 1900, 14: 2000, 16: 2250, 18: 2350, 19: 2500,
                 21: 2750, 23: 2900, 24: 3000, 26: 3250, 27: 3400,
                 29: 3500, 31: 4000, 32: 4150, 34: 4250, 37: 5000, 39: 6000}
BASE_RENT = {1: 100, 3: 120, 6: 180, 8: 200, 9: 220, 11: 260, 13: 280,
             14: 300, 16: 350, 18: 370, 19: 400, 21: 450, 23: 480,
             24: 500, 26: 600, 27: 620, 29: 650, 31: 750, 32: 780,
             34: 800, 37: 1000, 39: 1200}

RAIL_PRICE = {5: 1500, 15: 1500, 25: 1500, 35: 1500}
UTIL_PRICE = {12: 1500, 28: 1500}

PLAYERS = ["Aggressive Investor", "Conservative Banker", "Risk Taker",
           "Opportunistic Trader"]
P2I = {p: i for i, p in enumerate(PLAYERS)}

INFLATION_SET = {-3, 0, 2, 5, 8, 12}


def parse_money(s):
    """'LKR 12,345.' / 'LKR 12345' / '12,345' -> 12345"""
    s = s.replace("LKR", "").replace(",", "").replace(" ", "").replace(".", "")
    return int(s)


# --------------------------------------------------------------------------
# Log reader (handles UTF-8 and UTF-16 LE, which Windows redirects produce)
# --------------------------------------------------------------------------
def read_lines(path):
    with open(path, "rb") as f:
        raw = f.read()
    head = raw[:4096]
    if b"\x00" in head and (b"MONOPOLY" not in head and b"Pettah" not in head):
        text = raw.decode("utf-16-le", errors="replace")
    else:
        text = raw.decode("utf-8", errors="replace")
    if text.startswith("\ufeff"):
        text = text[1:]
    return text.splitlines()


# --------------------------------------------------------------------------
# Modifier type tags tracked from the log
# --------------------------------------------------------------------------
VAL_GLOBAL = "VAL_GLOBAL"
VAL_GROUP = "VAL_GROUP"
VAL_INDEX = "VAL_INDEX"
VAL_RAIL = "VAL_RAIL"
RENT_GLOBAL = "RENT_GLOBAL"
RENT_GROUP = "RENT_GROUP"
RENT_HOTEL = "RENT_HOTEL"
RENT_RAIL = "RENT_RAIL"
RENT_UTIL = "RENT_UTIL"
CONSTRUCTION = "CONSTRUCTION"
INSURANCE = "INSURANCE"
MORTGAGE = "MORTGAGE"
AUCTION = "AUCTION"
RECESSION = "RECESSION"


class Analyzer:
    def __init__(self, path):
        self.path = path
        self.lines = read_lines(path)
        self.n = len(self.lines)
        self.findings = []

        # per-square live state
        self.owner = [-1] * 40
        self.mortgaged = [0] * 40
        self.houses = [0] * 40
        self.hotel = [0] * 40
        self.insurance = [0] * 40          # 0 none, 1 basic, 2 comp, 3 BI
        self.ins_rounds = [0] * 40
        self.price = [BASE_PRICE.get(i, RAIL_PRICE.get(i, UTIL_PRICE.get(i, 0)))
                      for i in range(40)]
        self.mortgage_val = [BASE_MORTGAGE.get(i, 0) for i in range(40)]
        self.hcost = [BASE_HCOST.get(i, 0) for i in range(40)]
        self.tcost = [BASE_TCOST.get(i, 0) for i in range(40)]
        self.baserent = [BASE_RENT.get(i, 0) for i in range(40)]
        self.age = [0] * 40
        self.ren_round = [0] * 40          # last round renovated (0 = never)
        self.struct = [0] * 40
        self.pre_price = [0] * 40
        self.pre_rent = [0] * 40
        self.damaged = [0] * 40            # disaster-damaged (no rent)
        self.repair_owed = [0] * 40
        self.bi_lost = [0] * 40            # business interruption countdown

        # per-player live state
        self.pos = [0] * 4
        self.cash = [30000] * 4
        self.bankrupt = [0] * 4
        self.loan_active = [0] * 4
        self.loan_amount = [0] * 4
        self.loan_remaining = [0] * 4
        self.loan_rate = [0] * 4
        self.last_dice = [0] * 4
        self.bankrupt_round = [0] * 4

        # economy
        self.round = 0
        self.modifiers = []                # [type, group|-1, index|-1, pct, left]
        self.collected_mods = []           # modifiers added this round
        self.inflation_rate = 0
        self.loan_interest_rate = 8
        self.income_tax_rate = 15
        self.closed_prop = -1
        self.closed_rounds = 0

        # contextual
        self.auction_prop = -1
        self.auction_seller = -1
        self.in_summary = False
        self.summary_round = 0
        self.lux_tax_fired = False
        self.anti_spec_active = False
        self.foreclose_pending = False

    # ----------------------------------------------------------------------
    # helpers
    # ----------------------------------------------------------------------
    def report(self, level, claim, line, quote=""):
        self.findings.append({
            "level": level,
            "claim": claim,
            "line": line,
            "quote": quote,
        })

    def prop_name(self, idx):
        return BOARD.get(idx, "?")

    def count_owned(self, p, types):
        c = 0
        for i in range(40):
            if self.owner[i] == p and (i in types or not types):
                c += 1
        return c

    def count_houses(self, p):
        return sum(self.houses[i] for i in range(40)
                   if self.owner[i] == p and self.hotel[i] == 0)

    def count_hotels(self, p):
        return sum(1 for i in range(40)
                   if self.owner[i] == p and self.hotel[i] == 1)

    # -- value model -------------------------------------------------------
    def apply_inflation(self, rate):
        for i in range(40):
            if i not in PROP_TYPE and i not in RAIL_TYPE and i not in UTIL_TYPE:
                continue
            self.price[i] = self.price[i] + self.price[i] * rate // 100
            if self.price[i] < 1:
                self.price[i] = 1
            self.mortgage_val[i] = self.mortgage_val[i] + \
                self.mortgage_val[i] * rate // 100
            if self.mortgage_val[i] < 1:
                self.mortgage_val[i] = 1
            if i in PROP_TYPE:
                self.baserent[i] = self.baserent[i] + \
                    self.baserent[i] * rate // 100
                self.hcost[i] = self.hcost[i] + self.hcost[i] * rate // 100
                self.tcost[i] = self.tcost[i] + self.tcost[i] * rate // 100

    def add_mod(self, mtype, group, index, pct, left):
        self.collected_mods.append([mtype, group, index, pct, left])

    def value_mult(self, idx):
        mult = 100
        for m in self.modifiers:
            if m[0] == VAL_GLOBAL and (m[1] == -1 or True):
                mult = mult * m[3] // 100
        if idx in PROP_TYPE:
            g = GROUP[idx]
            for m in self.modifiers:
                if m[0] == VAL_GROUP and (m[1] == g or m[1] == -1):
                    mult = mult * m[3] // 100
        if idx in RAIL_TYPE:
            for m in self.modifiers:
                if m[0] == VAL_RAIL:
                    mult = mult * m[3] // 100
        for m in self.modifiers:
            if m[0] == VAL_INDEX and (m[2] == idx or m[2] == -1):
                mult = mult * m[3] // 100
        return mult

    def market_value(self, idx):
        price = self.price[idx]
        age = self.age[idx]
        depr = 0
        if age > 50:
            depr = (age - 50) // 5
            if depr > 30:
                depr = 30
        price = price - price * depr // 100
        price = price * self.value_mult(idx) // 100
        return price

    def mult_for(self, mtype, group=-1, index=-1):
        mult = 100
        for m in self.modifiers:
            if m[0] != mtype:
                continue
            if group != -1 and m[1] != -1 and m[1] != group:
                continue
            if index != -1 and m[2] != -1 and m[2] != index:
                continue
            mult = mult * m[3] // 100
        return mult

    def building_value(self, p):
        total = 0
        for i in range(40):
            if self.owner[i] != p:
                continue
            if self.hotel[i]:
                total += self.tcost[i]
            else:
                total += self.houses[i] * self.hcost[i]
        return total

    def prop_value(self, p):
        total = 0
        for i in range(40):
            if self.owner[i] == p:
                total += self.market_value(i)
        return total

    def net_worth(self, p):
        return (self.cash[p] + self.prop_value(p) + self.building_value(p)
                - self.loan_amount[p])

    def dec_mods(self):
        kept = []
        for m in self.modifiers:
            m[4] -= 1
            if m[4] > 0:
                kept.append(m)
        self.modifiers = kept
        for m in self.collected_mods:
            self.modifiers.append(m)
        self.collected_mods = []

    def land_index_from_name(self, name, line):
        idx = NAME2IDX.get(name)
        if idx is None:
            self.report("REVIEW", "Unknown square name in log: %r" % name,
                        line, name)
            return -1
        return idx

    # ----------------------------------------------------------------------
    # main loop
    # ----------------------------------------------------------------------
    def run(self):
        i = 0
        while i < self.n:
            line = self.lines[i].strip()
            ln = i + 1
            self.handle(line, ln, i)
            i += 1
        return self.findings

    # ----------------------------------------------------------------------
    def handle(self, line, ln, i):
        # ---- round headers ------------------------------------------------
        m = re.match(r"^ROUND (\d+)$", line)
        if m:
            self.round = int(m.group(1))
            return
        m = re.match(r"^Round (\d+) Summary$", line)
        if m:
            self.summary_round = int(m.group(1))
            self.end_of_round(i + 1)
            return

        # ---- dice & movement ----------------------------------------------
        m = re.match(r"^(.+?) rolled (\d+)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            d = int(m.group(2))
            if self.bankrupt[p]:
                self.report("BUG", "Bankrupt player %s rolled dice." %
                            PLAYERS[p], ln, line)
            if not (2 <= d <= 12):
                self.report("BUG", "Dice roll %d out of range 2..12 for %s." %
                            (d, PLAYERS[p]), ln, line)
            self.last_dice[p] = d
            return
        m = re.match(r"^(.+?) rolls (\d+)\.$", line)
        if m and m.group(1) in P2I:
            d = int(m.group(2))
            if not (2 <= d <= 12):
                self.report("BUG", "First-player roll %d out of range 2..12." %
                            d, ln, line)
            return
        m = re.match(r"^(.+?) is in Jail\. Rolled (\d+) and (\d+)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            a = int(m.group(2))
            b = int(m.group(3))
            if not (1 <= a <= 6 and 1 <= b <= 6):
                self.report("BUG", "Jail dice %d/%d out of range 1..6." %
                            (a, b), ln, line)
            return
        m = re.match(r"^(.+?) moves from Square (\d+) to Square (\d+)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            frm = int(m.group(2))
            to = int(m.group(3))
            if not (0 <= frm < 40 and 0 <= to < 40):
                self.report("BUG", "Square %d/%d outside 0..39." %
                            (frm, to), ln, line)
            if self.last_dice[p] and (frm + self.last_dice[p]) % 40 != to:
                self.report("BUG",
                            "%s moved %d->%d but dice was %d." %
                            (PLAYERS[p], frm, to, self.last_dice[p]),
                            ln, line)
            self.pos[p] = to
            return
        m = re.match(r"^(.+?) is sent to Jail!$", line)
        if m and m.group(1) in P2I:
            self.pos[P2I[m.group(1)]] = 10
            return

        # ---- GO -----------------------------------------------------------
        m = re.match(r"^(.+?) passed GO\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            go = 2000
            if i + 1 < self.n:
                m2 = re.match(r"^Collected LKR ([0-9,]+)$",
                              self.lines[i + 1].strip())
                if m2:
                    go = parse_money(m2.group(1))
            if self.bankrupt[p]:
                self.report("BUG", "Bankrupt player %s passed GO." %
                            PLAYERS[p], ln, line)
            prev = self.cash[p]
            self.cash[p] += go
            if i + 2 < self.n:
                m3 = re.match(r"^Current Balance : LKR ([0-9,]+)$",
                              self.lines[i + 2].strip())
                if m3:
                    bal = parse_money(m3.group(1))
                    if bal != prev + go:
                        self.report("BUG",
                                    "%s GO balance %d != %d + %d." %
                                    (PLAYERS[p], bal, prev, go), ln,
                                    self.lines[i + 2].strip())
            return

        # ---- purchases ----------------------------------------------------
        m = re.match(r"^(.+?) purchased (.+?) for LKR ([0-9,]+)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            name = m.group(2)
            price = parse_money(m.group(3))
            idx = self.land_index_from_name(name, ln)
            if idx >= 0 and idx != self.pos[p]:
                self.report("BUG",
                            "%s bought %s (square %d) while on square %d." %
                            (PLAYERS[p], name, idx, self.pos[p]), ln, line)
            if idx >= 0 and self.owner[idx] != -1:
                self.report("BUG",
                            "%s bought already-owned %s (owner %d)." %
                            (PLAYERS[p], name, self.owner[idx]), ln, line)
            if self.bankrupt[p]:
                self.report("BUG", "Bankrupt player %s purchased %s." %
                            (PLAYERS[p], name), ln, line)
            prev = self.cash[p]
            self.cash[p] -= price
            if idx >= 0:
                self.owner[idx] = p
                self.mortgaged[idx] = 0
            # verify declared remaining balance
            if i + 1 < self.n:
                m2 = re.match(r"^Remaining Balance : LKR ([0-9,]+)\.$",
                              self.lines[i + 1].strip())
                if m2:
                    bal = parse_money(m2.group(1))
                    if bal != prev - price:
                        self.report("BUG",
                                    "%s purchase balance %d != %d - %d." %
                                    (PLAYERS[p], bal, prev, price), ln,
                                    self.lines[i + 1].strip())
            return

        # ---- rent ---------------------------------------------------------
        m = re.match(r"^(.+?) landed on (.+?)\.$", line)
        if m and m.group(1) in P2I and \
                m.group(2) not in ("Income Tax", "Community Development Fund"):
            p = P2I[m.group(1)]
            name = m.group(2)
            if name in NAME2IDX and self.pos[p] != NAME2IDX[name]:
                self.report("BUG",
                            "%s landed on %s (square %d) but is on square %d." %
                            (PLAYERS[p], name, NAME2IDX[name], self.pos[p]),
                            ln, line)
            # is this a rent-paying landing?  (next line says Rent Paid)
            nxt = self.lines[i + 1].strip() if i + 1 < self.n else ""
            if re.match(r"^Rent Paid : LKR", nxt):
                self.handle_rent(p, name, ln, i)
                return
            return

        # ---- construction -------------------------------------------------
        m = re.match(r"^(.+?) constructed one house on (.+?)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            name = m.group(2)
            idx = self.land_index_from_name(name, ln)
            if idx >= 0:
                if self.owner[idx] != p:
                    self.report("BUG",
                                "%s built a house on %s (owner %d)." %
                                (PLAYERS[p], name, self.owner[idx]), ln, line)
                if self.mortgaged[idx]:
                    self.report("BUG",
                                "%s built a house on mortgaged %s." %
                                (PLAYERS[p], name), ln, line)
                self.houses[idx] += 1
            cost = 0
            if i + 1 < self.n:
                m2 = re.match(r"^Construction Cost : LKR ([0-9,]+)\.$",
                              self.lines[i + 1].strip())
                if m2:
                    cost = parse_money(m2.group(1))
            self.cash[p] -= cost
            return
        m = re.match(r"^(.+?) upgraded (.+?) to a Hotel\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            name = m.group(2)
            idx = self.land_index_from_name(name, ln)
            if idx >= 0:
                if self.owner[idx] != p:
                    self.report("BUG",
                                "%s built a hotel on %s (owner %d)." %
                                (PLAYERS[p], name, self.owner[idx]), ln, line)
                self.hotel[idx] = 1
                self.houses[idx] = 0
            cost = 0
            if i + 1 < self.n:
                m2 = re.match(r"^Construction Cost : LKR ([0-9,]+)\.$",
                              self.lines[i + 1].strip())
                if m2:
                    cost = parse_money(m2.group(1))
            self.cash[p] -= cost
            return

        # ---- mortgage / redeem -------------------------------------------
        m = re.match(r"^(.+?) mortgaged (.+?) for LKR ([0-9,]+)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            name = m.group(2)
            payout = parse_money(m.group(3))
            idx = self.land_index_from_name(name, ln)
            if idx >= 0 and self.owner[idx] != p:
                self.report("BUG",
                            "%s mortgaged %s (owner %d)." %
                            (PLAYERS[p], name, self.owner[idx]), ln, line)
            self.mortgaged[idx] = 1
            self.cash[p] += payout
            return
        m = re.match(r"^(.+?) redeemed the mortgage on (.+?) for LKR ([0-9,]+)\.$",
                     line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            name = m.group(2)
            cost = parse_money(m.group(3))
            idx = self.land_index_from_name(name, ln)
            if idx >= 0 and self.owner[idx] != p:
                self.report("BUG",
                            "%s redeemed mortgage on %s (owner %d)." %
                            (PLAYERS[p], name, self.owner[idx]), ln, line)
            self.mortgaged[idx] = 0
            self.cash[p] -= cost
            return

        # ---- sales to bank -------------------------------------------------
        m = re.match(r"^(.+?) sold (.+?) to the Bank for LKR ([0-9,]+)", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            name = m.group(2)
            value = parse_money(m.group(3))
            idx = self.land_index_from_name(name, ln)
            if idx >= 0 and self.owner[idx] != p:
                self.report("BUG",
                            "%s sold %s (owner %d) to the Bank." %
                            (PLAYERS[p], name, self.owner[idx]), ln, line)
            self.cash[p] += value
            if idx >= 0:
                self.owner[idx] = -1
                self.mortgaged[idx] = 0
                self.houses[idx] = 0
                self.hotel[idx] = 0
            return

        # ---- loans ----------------------------------------------------------
        m = re.match(r"^(.+?) obtained a secured loan\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            amt = 0
            rate = 0
            j = i + 1
            while j < self.n:
                l2 = self.lines[j].strip()
                m2 = re.match(r"^Loan Amount : LKR ([0-9,]+)\.$", l2)
                if m2:
                    amt = parse_money(m2.group(1))
                m3 = re.match(r"^Interest Rate : (\d+)%$", l2)
                if m3:
                    rate = int(m3.group(1))
                if l2 == "" and m2 is None:
                    break
                if re.match(r"^Collateral :$", l2):
                    break
                j += 1
            if self.loan_active[p]:
                self.report("BUG",
                            "%s obtained a second loan while one was active." %
                            PLAYERS[p], ln, line)
            self.loan_active[p] = 1
            self.loan_amount[p] = amt
            self.loan_rate[p] = rate
            self.loan_remaining[p] = 20
            self.cash[p] += amt
            return
        m = re.match(r"^(.+?) repaid LKR (\d+) towards their loan\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            amt = int(m.group(2))
            self.cash[p] -= amt
            self.loan_amount[p] -= amt
            if self.loan_amount[p] <= 0:
                self.loan_active[p] = 0
                self.loan_amount[p] = 0
            return
        m = re.match(r"^(.+?) increased their loan by LKR (\d+)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            amt = int(m.group(2))
            self.cash[p] += amt
            self.loan_amount[p] += amt
            return
        m = re.match(r"^(.+?)'s loan accrued LKR (\d+) interest\. "
                     r"New balance : LKR (\d+)$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            interest = int(m.group(2))
            newbal = int(m.group(3))
            if self.loan_amount[p] + interest != newbal:
                self.report("BUG",
                            "%s loan interest %d + %d != new balance %d." %
                            (PLAYERS[p], self.loan_amount[p], interest, newbal),
                            ln, line)
            self.loan_amount[p] = newbal
            self.loan_remaining[p] -= 1
            return
        m = re.match(r"^(.+?) extended their loan by (\d+) rounds\.$", line)
        if m and m.group(1) in P2I:
            self.loan_remaining[P2I[m.group(1)]] += int(m.group(2))
            return
        m = re.match(r"^(.+?) refinanced their loan at the current rate of "
                     r"(\d+)%\.$", line)
        if m and m.group(1) in P2I:
            self.loan_rate[P2I[m.group(1)]] = int(m.group(2))
            return
        m = re.match(r"^(.+?) has defaulted on their loan!$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            self.foreclose(p, ln, i)
            return

        # ---- bankruptcy -----------------------------------------------------
        if line == "*** BANKRUPTCY ***":
            nxt = self.lines[i + 1].strip() if i + 1 < self.n else ""
            m2 = re.match(r"^(.+?) has been declared bankrupt\.$", nxt)
            if m2 and m2.group(1) in P2I:
                p = P2I[m2.group(1)]
                self.handle_bankruptcy(p, ln, i + 1)
            return

        # ---- auctions -------------------------------------------------------
        m = re.match(r"^\*\*\* AUCTION \*\*\*$", line)
        if m:
            self.auction_prop = -1
            self.auction_seller = -1
            if i + 1 < self.n:
                m2 = re.match(r"^Property : (.+?)$", self.lines[i + 1].strip())
                if m2:
                    nm = m2.group(1)
                    self.auction_prop = self.land_index_from_name(nm, ln + 1)
            return
        m = re.match(r"^(.+?) wins the auction for LKR ([0-9,]+)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            bid = parse_money(m.group(2))
            idx = self.auction_prop
            if idx >= 0 and self.owner[idx] != -1 and self.auction_seller == -1 \
                    and not getattr(self, "foreclose_pending", False):
                self.report("BUG",
                            "Auctioned %s was already owned by player %d." %
                            (self.prop_name(idx), self.owner[idx]), ln, line)
            if self.bankrupt[p]:
                self.report("BUG", "Bankrupt player %s won an auction." %
                            PLAYERS[p], ln, line)
            self.cash[p] -= bid
            if self.auction_seller >= 0:
                self.cash[self.auction_seller] += bid
                if self.auction_seller == p:
                    self.report("BUG",
                                "Anti-Speculation forced seller %s bought "
                                "back %s (net-zero cost)." %
                                (PLAYERS[p], self.prop_name(idx)), ln, line)
            if idx >= 0:
                self.owner[idx] = p
                self.mortgaged[idx] = 0
                self.houses[idx] = 0
                self.hotel[idx] = 0
            self.auction_prop = -1
            self.auction_seller = -1
            return
        m = re.match(r"^No bids received\. (.+?) remains with the Bank\.$",
                     line)
        if m:
            idx = self.auction_prop
            if idx >= 0:
                self.owner[idx] = -1
                self.mortgaged[idx] = 0
                self.houses[idx] = 0
                self.hotel[idx] = 0
            self.auction_prop = -1
            self.auction_seller = -1
            return
        m = re.match(r"^Anti-Speculation Act : (.+?) must sell (.+?)\.$", line)
        if m and m.group(1) in P2I:
            self.auction_seller = P2I[m.group(1)]
            return

        # ---- insurance -------------------------------------------------------
        m = re.match(r"^(.+?) purchased insurance for (.+?)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            name = m.group(2)
            idx = self.land_index_from_name(name, ln)
            if idx >= 0 and self.owner[idx] != p:
                self.report("BUG",
                            "%s insured %s (owner %d)." %
                            (PLAYERS[p], name, self.owner[idx]), ln, line)
            premium = 0
            if i + 1 < self.n:
                m2 = re.match(r"^Premium : LKR ([0-9,]+)\.$",
                              self.lines[i + 1].strip())
                if m2:
                    premium = parse_money(m2.group(1))
            self.cash[p] -= premium
            if idx >= 0:
                self.ins_rounds[idx] = 20
            return
        m = re.match(r"^Insurance policy on (.+?) expires in (\d+) rounds\.$",
                     line)
        if m:
            return
        m = re.match(r"^Insurance policy on (.+?) has expired\.$", line)
        if m:
            idx = self.land_index_from_name(m.group(1), ln)
            if idx >= 0:
                self.insurance[idx] = 0
            return

        # ---- taxes ----------------------------------------------------------
        m = re.match(r"^(.+?) landed on Income Tax\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            amt = 0
            j = i + 1
            while j < self.n:
                l2 = self.lines[j].strip()
                m2 = re.match(r"^(.+?) paid tax : LKR (\d+)$", l2)
                if m2:
                    amt = int(m2.group(2))
                    break
                j += 1
            self.cash[p] -= amt
            return
        m = re.match(r"^(.+?) landed on Community Development Fund\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            amt = 0
            j = i + 1
            while j < self.n:
                l2 = self.lines[j].strip()
                m2 = re.match(r"^(.+?) paid community development tax : LKR (\d+)$",
                              l2)
                if m2:
                    amt = int(m2.group(2))
                    break
                j += 1
            self.cash[p] -= amt
            return

        # ---- bail ----------------------------------------------------------
        m = re.match(r"^(.+?) pays bail of LKR (\d+) and is released from "
                     r"Jail\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            self.cash[p] -= int(m.group(2))
            return
        m = re.match(r"^(.+?) has been in Jail for \d+ turns - must pay bail "
                     r"of LKR (\d+) and is released\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            self.cash[p] -= int(m.group(2))
            return

        # ---- disaster / repair ----------------------------------------------
        m = re.match(r"^Affected Property : (.+?) \(owner : (.+?)\)$", line)
        if m and m.group(2) in P2I:
            self.disaster_prop = NAME2IDX.get(m.group(1), -1)
            self.disaster_owner = P2I[m.group(2)]
            return
        m = re.match(r"^Compensation Paid : LKR (\d+)$", line)
        if m:
            comp = int(m.group(1))
            if self.disaster_owner >= 0:
                self.cash[self.disaster_owner] += comp
            if self.disaster_prop >= 0:
                self.repair_owed[self.disaster_prop] -= comp
            return
        m = re.match(r"^(.+?) is damaged and stops earning rent until "
                     r"repaired\.$", line)
        if m:
            idx = NAME2IDX.get(m.group(1), -1)
            if idx >= 0:
                self.damaged[idx] = 1
            return
        m = re.match(r"^(.+?) repaired (.+?)\. It can collect rent again\.$",
                     line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            idx = NAME2IDX.get(m.group(2), -1)
            cost = self.repair_owed[idx] if idx >= 0 else 0
            if i + 1 < self.n:
                m2 = re.match(r"^Repair Cost : LKR ([0-9,]+)\.?$",
                              self.lines[i + 1].strip())
                if m2:
                    cost = parse_money(m2.group(1))
            self.cash[p] -= cost
            if idx >= 0:
                self.damaged[idx] = 0
                self.repair_owed[idx] = 0
            return

        # ---- maintenance / renovation ----------------------------------------
        m = re.match(r"^(.+?) performed maintenance on (.+?)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            idx = NAME2IDX.get(m.group(2), -1)
            cost = 0
            if i + 1 < self.n:
                m2 = re.match(r"^Maintenance Cost : LKR (\d+)$",
                              self.lines[i + 1].strip())
                if m2:
                    cost = int(m2.group(1))
            self.cash[p] -= cost
            return
        m = re.match(r"^(.+?) renovated (.+?)\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            idx = NAME2IDX.get(m.group(2), -1)
            cost = 0
            if i + 1 < self.n:
                m2 = re.match(r"^Renovation Cost : LKR (\d+)$",
                              self.lines[i + 1].strip())
                if m2:
                    cost = int(m2.group(1))
            self.cash[p] -= cost
            if idx >= 0:
                self.age[idx] = 0
                self.ren_round[idx] = self.round
            return
        m = re.match(r"^(.+?) fully renovated (.+?) after structural "
                     r"damage\.$", line)
        if m and m.group(1) in P2I:
            p = P2I[m.group(1)]
            idx = NAME2IDX.get(m.group(2), -1)
            cost = 0
            if i + 1 < self.n:
                m2 = re.match(r"^Renovation Cost : LKR (\d+)$",
                              self.lines[i + 1].strip())
                if m2:
                    cost = int(m2.group(1))
            self.cash[p] -= cost
            if idx >= 0:
                self.price[idx] = self.pre_price[idx]
                self.baserent[idx] = self.pre_rent[idx]
                self.struct[idx] = 0
            return
        m = re.match(r"^(.+?) has suffered structural damage from neglect!$",
                     line)
        if m:
            idx = NAME2IDX.get(m.group(1), -1)
            if idx >= 0:
                self.pre_price[idx] = self.price[idx]
                self.pre_rent[idx] = self.baserent[idx]
                self.price[idx] = self.price[idx] * 85 // 100
                self.baserent[idx] = self.baserent[idx] * 75 // 100
                self.struct[idx] = 1
            return

        # ---- economy triggers ------------------------------------------------
        m = re.match(r"^New Inflation Rate : ([+-]?\d+)%$", line)
        if m:
            rate = int(m.group(1))
            if rate not in INFLATION_SET:
                self.report("BUG", "Unexpected inflation rate %d." % rate,
                            ln, line)
            self.inflation_rate = rate
            self.apply_inflation(rate)
            return
        m = re.match(r"^New Loan Interest Rate : (\d+)%$", line)
        if m:
            self.loan_interest_rate = int(m.group(1))
            if not (1 <= self.loan_interest_rate <= 25):
                self.report("BUG",
                            "Loan interest %d outside 1..25." %
                            self.loan_interest_rate, ln, line)
            return

        # national event cards
        if line == "*** NATIONAL EVENT CARD ***":
            self.parse_event_card(ln, i)
            return
        if line == "=== Economic Event ===":
            self.parse_econ_event(ln, i)
            return
        if line == "=== Government Regulation ===":
            self.parse_regulation(ln, i)
            return
        if line == "=== Regional Development Card ===":
            self.parse_regional(ln, i)
            return
        if line == "=== Property Market Review ===":
            self.parse_market_review(ln, i)
            return
        if line == "*** DISASTER ***":
            return

        # game over
        if line == "GAME OVER":
            self.parse_game_over(ln, i)
            return

    # ----------------------------------------------------------------------
    def handle_rent(self, payer, name, ln, i):
        nxt = self.lines[i + 1].strip()
        m = re.match(r"^Rent Paid : LKR ([0-9,]+)\.$", nxt)
        if not m:
            return
        rent = parse_money(m.group(1))
        owner_name = ""
        if i + 2 < self.n:
            m2 = re.match(r"^Owner : (.+?)\.$", self.lines[i + 2].strip())
            if m2:
                owner_name = m2.group(1)
        owner = P2I.get(owner_name, -1)
        idx = NAME2IDX.get(name, -1)

        if owner == payer:
            self.report("BUG",
                        "%s paid rent to themselves on %s." %
                        (PLAYERS[payer], name), ln, nxt)
        if owner >= 0 and self.bankrupt[owner]:
            self.report("BUG",
                        "Rent on %s paid to bankrupt owner %s." %
                        (name, PLAYERS[owner]), ln, nxt)
        if idx >= 0 and self.owner[idx] != owner:
            self.report("BUG",
                        "Rent on %s paid to %s but tracked owner is %s." %
                        (name, PLAYERS[owner] if owner >= 0 else "?",
                         PLAYERS[self.owner[idx]] if self.owner[idx] >= 0
                         else "Bank"), ln, nxt)
        if idx >= 0 and self.mortgaged[idx]:
            self.report("BUG", "Rent collected on mortgaged %s." % name,
                        ln, nxt)
        if not self.bankrupt[payer]:
            self.cash[payer] -= rent
        if owner >= 0:
            self.cash[owner] += rent
        self.last_rent_owner = owner

    # ----------------------------------------------------------------------
    def handle_bankruptcy(self, p, ln, li):
        self.bankrupt[p] = 1
        self.bankrupt_round[p] = self.summary_round or self.round
        self.cash[p] = 0
        self.loan_active[p] = 0
        self.loan_amount[p] = 0

        # liquidateBankruptAssets() strips ownership of every square the
        # player owns before auctioning it - mirror that here so the
        # follow-up auctions see owner -1
        for i2 in range(40):
            if self.owner[i2] == p:
                self.owner[i2] = -1
                self.mortgaged[i2] = 0
                self.houses[i2] = 0
                self.hotel[i2] = 0

        # evidence: what preceded the bankruptcy message?
        found = ""
        for k in range(max(0, li - 8), li):
            t = self.lines[k].strip()
            if re.search(r"LKR [0-9,]+", t):
                found = t
        if not found:
            self.report("REVIEW",
                        "No monetary evidence immediately before %s's "
                        "bankruptcy." % PLAYERS[p], ln, "")

        # assets must be auctioned next
        owned = [i for i in range(40) if self.owner[i] == p]
        if owned:
            msg = "Bankrupt %s owned %d square(s) that must be auctioned." % (
                PLAYERS[p], len(owned))
            self.pending_liquidation = owned
            self.pending_liquidation_player = p
            self.liquidation_checked_at = ln
            self.pending_auctions = list(owned)
        else:
            self.pending_liquidation = []

    def foreclose(self, p, ln, i):
        # verify evidence (accrued interest line precedes)
        found = ""
        for k in range(max(0, i - 20), i):
            t = self.lines[k].strip()
            if "accrued" in t or "New balance" in t:
                found = t
        if not found:
            self.report("REVIEW",
                        "No loan-interest evidence before %s's foreclosure." %
                        PLAYERS[p], ln, "")

        # the defaulted loan is cleared (bank.c foreclose) - the pledged
        # collateral squares keep their tracked owner until each auction
        # reassigns them, so suppress the "already owned" auction check
        # until the next round summary
        self.loan_active[p] = 0
        self.loan_amount[p] = 0
        self.foreclose_pending = True

    # ----------------------------------------------------------------------
    def parse_event_card(self, ln, i):
        j = i + 1
        while j < self.n and self.lines[j].strip() == "":
            j += 1
        if j >= self.n:
            return
        txt = self.lines[j].strip()
        g = 0
        if "Tourism Hype" in txt:
            self.add_mod(RENT_HOTEL, -1, -1, 200, 5)
        elif "Fuel Shortage" in txt:
            self.add_mod(RENT_RAIL, -1, -1, 200, 5)
        elif "Heavy Floods" in txt:
            pass
        elif "Political Rally" in txt:
            pass
        elif "Stock Market Rise" in txt:
            self.add_mod(VAL_GLOBAL, -1, -1, 110, 15)
        elif "Economic Downturn" in txt:
            self.add_mod(VAL_GLOBAL, -1, -1, 85, 15)
        elif "Housing Subsidy" in txt:
            self.add_mod(CONSTRUCTION, -1, -1, 70, 15)
        elif "Interest Rate Cut" in txt:
            self.loan_interest_rate -= 2
        elif "Interest Rate Increase" in txt:
            self.loan_interest_rate += 2
        elif "Tax Amnesty" in txt:
            for p in range(4):
                if not self.bankrupt[p]:
                    self.cash[p] += 2000
        elif "Power Failure" in txt:
            self.add_mod(RENT_UTIL, -1, -1, 50, 3)
        elif "Foreign Funding" in txt:
            self.add_mod(VAL_GROUP, GROUP[16], -1, 115, 15)
        elif "Port Expansion" in txt:
            self.add_mod(VAL_RAIL, -1, -1, 120, 15)
        elif "Festival Season" in txt:
            self.add_mod(RENT_HOTEL, -1, -1, 150, 5)
        elif "Labour Strike" in txt:
            pass
        elif "Insurance Discount" in txt:
            self.add_mod(INSURANCE, -1, -1, 80, 10)
        elif "Property Revaluation" in txt:
            for nm, gi in (("Brown", 1), ("Light Blue", 6), ("Pink", 11),
                           ("Orange", 16), ("Red", 21), ("Yellow", 26),
                           ("Green", 31), ("Dark Blue", 37)):
                if txt.startswith("Property Revaluation : %s " % nm):
                    self.add_mod(VAL_GROUP, gi, -1, 115, 15)
                    break
        elif "Currency Depreciation" in txt:
            self.add_mod(CONSTRUCTION, -1, -1, 110, 15)
        elif "Government Grant" in txt:
            m = re.match(r"^Government Grant : (.+?) receives LKR 5,000\.$",
                         txt)
            if m and m.group(1) in P2I:
                lucky = P2I[m.group(1)]
                if self.bankrupt[lucky]:
                    self.report("BUG",
                                "Government Grant awarded to bankrupt %s." %
                                PLAYERS[lucky], ln, txt)
                else:
                    self.cash[lucky] += 5000
        elif "National Disaster" in txt:
            pass

    def parse_econ_event(self, ln, i):
        j = i + 1
        while j < self.n and self.lines[j].strip() == "":
            j += 1
        if j >= self.n:
            return
        txt = self.lines[j].strip()
        if "Tourism Boom" in txt:
            self.add_mod(RENT_HOTEL, -1, -1, 200, 15)
            self.add_mod(VAL_GROUP, GROUP[26], -1, 115, 15)
        elif "Fuel Crisis" in txt:
            self.add_mod(RENT_RAIL, -1, -1, 200, 15)
            self.add_mod(CONSTRUCTION, -1, -1, 120, 15)
        elif "Heavy Monsoon" in txt:
            self.add_mod(INSURANCE, -1, -1, 115, 15)
            self.add_mod(VAL_GROUP, GROUP[26], -1, 90, 15)
        elif "Economic Recession" in txt:
            self.add_mod(VAL_GLOBAL, -1, -1, 85, 15)
            self.add_mod(RENT_GLOBAL, -1, -1, 90, 15)
            self.add_mod(RECESSION, -1, -1, 100, 15)
            self.loan_interest_rate = self.loan_interest_rate + \
                self.loan_interest_rate * 15 // 100
        elif "Stock Market Boom" in txt:
            self.add_mod(VAL_GLOBAL, -1, -1, 110, 15)
            self.loan_interest_rate = self.loan_interest_rate - \
                self.loan_interest_rate * 10 // 100
        elif "Government Housing Programme" in txt:
            self.add_mod(CONSTRUCTION, -1, -1, 75, 15)
        elif "Foreign Investment" in txt:
            self.add_mod(VAL_GROUP, GROUP[16], -1, 120, 15)
        elif "Political Unrest" in txt:
            self.add_mod(RENT_HOTEL, -1, -1, 50, 15)

    def parse_regulation(self, ln, i):
        j = i + 1
        while j < self.n and self.lines[j].strip() == "":
            j += 1
        if j >= self.n:
            return
        txt = self.lines[j].strip()
        if "Increase Property Tax" in txt:
            self.income_tax_rate = self.income_tax_rate + \
                self.income_tax_rate * 50 // 100
            if self.income_tax_rate > 25:
                self.income_tax_rate = 25
        elif "Reduce Loan Interest" in txt:
            self.loan_interest_rate -= 2
            if self.loan_interest_rate < 1:
                self.loan_interest_rate = 1
        elif "Housing Subsidy" in txt:
            self.add_mod(CONSTRUCTION, -1, -1, 70, 20)
        elif "Luxury Property Tax" in txt:
            self.lux_tax_fired = True
            # amount per hotel is not printed - charged silently
            for i2 in range(40):
                if self.hotel[i2] and self.owner[i2] >= 0:
                    tax = self.market_value(i2) * 25 // 100
                    self.cash[self.owner[i2]] -= tax
        elif "Railway Modernization" in txt:
            self.add_mod(RENT_RAIL, -1, -1, 125, 20)
        elif "Electricity Tariff Revision" in txt:
            self.add_mod(RENT_UTIL, -1, -1, 120, 20)
        elif "Insurance Regulation" in txt:
            self.add_mod(INSURANCE, -1, -1, 85, 20)
        elif "Anti-Speculation Act" in txt:
            self.anti_spec_active = True

    def parse_regional(self, ln, i):
        j = i + 1
        while j < self.n and self.lines[j].strip() == "":
            j += 1
        if j >= self.n:
            return
        txt = self.lines[j].strip()
        if "Southern Tourism Boom" in txt:
            self.add_mod(RENT_GROUP, GROUP[26], -1, 140, 15)
        elif "Port City Expansion" in txt:
            self.add_mod(VAL_GROUP, GROUP[1], -1, 125, 15)
            self.add_mod(VAL_INDEX, -1, 5, 125, 15)
        elif "IT Industry Growth" in txt:
            self.add_mod(VAL_GROUP, GROUP[11], -1, 120, 15)
        elif "Northern Development" in txt:
            self.add_mod(VAL_GROUP, GROUP[31], -1, 130, 15)
        elif "Tea Export Boom" in txt:
            self.add_mod(VAL_INDEX, -1, 37, 135, 15)
        elif "Airport Expansion" in txt:
            self.add_mod(RENT_GROUP, GROUP[16], -1, 130, 15)
        elif "University City Growth" in txt:
            self.add_mod(VAL_GROUP, GROUP[21], -1, 120, 15)
        elif "Beach Pollution" in txt:
            self.add_mod(RENT_GROUP, GROUP[26], -1, 70, 15)
        elif "Flood Damage" in txt:
            self.add_mod(VAL_GROUP, GROUP[26], -1, 80, 15)
        elif "Transport Strike" in txt:
            self.add_mod(RENT_RAIL, -1, -1, 60, 15)
        elif "Electricity Tariff Increase" in txt:
            self.add_mod(RENT_UTIL, -1, -1, 125, 15)
        elif "Water Shortage" in txt:
            self.add_mod(RENT_UTIL, -1, -1, 120, 15)
            self.add_mod(VAL_INDEX, -1, 13, 90, 15)
            self.add_mod(VAL_INDEX, -1, 29, 90, 15)

    def parse_market_review(self, ln, i):
        boom = ""
        decline = ""
        for k in range(i + 1, min(i + 6, self.n)):
            t = self.lines[k].strip()
            m = re.match(r"^Market Boom : (.+?) \(values", t)
            if m:
                boom = m.group(1)
            m = re.match(r"^Market Decline : (.+?) \(values", t)
            if m:
                decline = m.group(1)
        GROUP_N2I = {"Brown": 1, "Light Blue": 6, "Pink": 11, "Orange": 16,
                     "Red": 21, "Yellow": 26, "Green": 31, "Dark Blue": 37}
        if boom in GROUP_N2I:
            g = GROUP_N2I[boom]
            self.add_mod(VAL_GROUP, g, -1, 120, 10)
            self.add_mod(RENT_GROUP, g, -1, 125, 10)
            self.add_mod(MORTGAGE, g, -1, 115, 10)
            self.add_mod(CONSTRUCTION, g, -1, 110, 10)
        if decline in GROUP_N2I:
            g = GROUP_N2I[decline]
            self.add_mod(VAL_GROUP, g, -1, 85, 10)
            self.add_mod(RENT_GROUP, g, -1, 80, 10)
            self.add_mod(MORTGAGE, g, -1, 90, 10)
            self.add_mod(AUCTION, g, -1, 75, 10)

    # ----------------------------------------------------------------------
    def end_of_round(self, start_line):
        """A 'Round N Summary' header was just seen.  Apply the round-end
        tick (age, modifier decay) and then verify the summary block."""
        # replicate: ageProperties (every property age++), decrementModifiers
        for i2 in range(40):
            self.age[i2] += 1
        self.dec_mods()

        # parse the summary block that follows
        nw = [None] * 4
        cash = [None] * 4
        props = [None] * 4
        rails = [None] * 4
        utils = [None] * 4
        houses = [None] * 4
        hotels = [None] * 4
        loan = [None] * 4
        status = [None] * 4
        cur = None
        k = start_line
        while k < self.n:
            t = self.lines[k].strip()
            if t == "Current Market Conditions":
                break
            if t in P2I:
                cur = P2I[t]
            elif cur is not None:
                m = re.match(r"^Cash : LKR ([0-9,]+)$", t)
                if m:
                    cash[cur] = parse_money(m.group(1))
                m = re.match(r"^Net Worth : LKR ([0-9,]+)$", t)
                if m:
                    nw[cur] = parse_money(m.group(1))
                m = re.match(r"^Properties : (\d+)$", t)
                if m:
                    props[cur] = int(m.group(1))
                m = re.match(r"^Railways\s+: (\d+)$", t)
                if m:
                    rails[cur] = int(m.group(1))
                m = re.match(r"^Utilities\s+: (\d+)$", t)
                if m:
                    utils[cur] = int(m.group(1))
                m = re.match(r"^Houses\s+: (\d+)$", t)
                if m:
                    houses[cur] = int(m.group(1))
                m = re.match(r"^Hotels\s+: (\d+)$", t)
                if m:
                    hotels[cur] = int(m.group(1))
                m = re.match(r"^Outstanding Loan : LKR ([0-9,]+)$", t)
                if m:
                    loan[cur] = parse_money(m.group(1))
                m = re.match(r"^Status : (.+)$", t)
                if m:
                    status[cur] = m.group(1)
            k += 1

        for p in range(4):
            if self.bankrupt[p]:
                # a bankrupt player must show 0 everywhere
                if cash[p] not in (0, None):
                    self.report("BUG",
                                "Round %d: bankrupt %s has non-zero cash %d." %
                                (self.summary_round, PLAYERS[p], cash[p]),
                                start_line, "")
                if nw[p] not in (0, None):
                    self.report("BUG",
                                "Round %d: bankrupt %s has non-zero net "
                                "worth %d." % (self.summary_round, PLAYERS[p],
                                               nw[p]), start_line, "")
                continue
            if cash[p] is not None:
                diff = cash[p] - self.cash[p]
                if diff != 0:
                    self.report("REVIEW",
                                "Round %d: %s reported cash %d vs tracked %d "
                                "(diff %d)." % (self.summary_round, PLAYERS[p],
                                                cash[p], self.cash[p], diff),
                                start_line, "")
                self.cash[p] = cash[p]   # resync
            if props[p] is not None:
                if props[p] != self.count_owned(p, PROP_TYPE):
                    self.report("BUG",
                                "Round %d: %s Properties %d vs tracked %d." %
                                (self.summary_round, PLAYERS[p], props[p],
                                 self.count_owned(p, PROP_TYPE)),
                                start_line, "")
            if rails[p] is not None:
                if rails[p] != self.count_owned(p, RAIL_TYPE):
                    self.report("BUG",
                                "Round %d: %s Railways %d vs tracked %d." %
                                (self.summary_round, PLAYERS[p], rails[p],
                                 self.count_owned(p, RAIL_TYPE)),
                                start_line, "")
            if utils[p] is not None:
                if utils[p] != self.count_owned(p, UTIL_TYPE):
                    self.report("BUG",
                                "Round %d: %s Utilities %d vs tracked %d." %
                                (self.summary_round, PLAYERS[p], utils[p],
                                 self.count_owned(p, UTIL_TYPE)),
                                start_line, "")
            if houses[p] is not None:
                if houses[p] != self.count_houses(p):
                    self.report("BUG",
                                "Round %d: %s Houses %d vs tracked %d." %
                                (self.summary_round, PLAYERS[p], houses[p],
                                 self.count_houses(p)), start_line, "")
            if hotels[p] is not None:
                if hotels[p] != self.count_hotels(p):
                    self.report("BUG",
                                "Round %d: %s Hotels %d vs tracked %d." %
                                (self.summary_round, PLAYERS[p], hotels[p],
                                 self.count_hotels(p)), start_line, "")
            if loan[p] is not None:
                exp = self.loan_amount[p] if self.loan_active[p] else 0
                if loan[p] != exp:
                    self.report("BUG",
                                "Round %d: %s loan %d vs tracked %d." %
                                (self.summary_round, PLAYERS[p], loan[p],
                                 exp), start_line, "")
            if nw[p] is not None:
                exp = self.net_worth(p)
                if nw[p] != exp:
                    self.report("REVIEW",
                                "Round %d: %s net worth %d vs recomputed %d "
                                "(diff %d)." % (self.summary_round, PLAYERS[p],
                                                nw[p], exp, nw[p] - exp),
                                start_line, "")

        # liquidation completeness: bankrupt players' assets were auctioned
        if hasattr(self, "pending_liquidation") and self.pending_liquidation:
            still = [i for i in self.pending_liquidation
                     if self.owner[i] == self.pending_liquidation_player]
            if still:
                self.report("BUG",
                            "Ghost owners after bankruptcy of %s: %s not "
                            "reassigned." %
                            (PLAYERS[self.pending_liquidation_player],
                             [self.prop_name(x) for x in still]),
                            start_line, "")
            self.pending_liquidation = []

        self.lux_tax_fired = False
        self.foreclose_pending = False

    # ----------------------------------------------------------------------
    def parse_game_over(self, ln, i):
        # winner block: Winner / name / Total Cash / LKR x / Total Property
        # Value / LKR x / Outstanding Loans / LKR x|None / Net Worth / LKR x
        j = i + 1
        winner = None
        cash = None
        prop = None
        loans = None
        nw = None
        while j < self.n:
            t = self.lines[j].strip()
            if t == "Final Standings (all players)":
                break
            if t in P2I:
                winner = P2I[t]
            elif t == "Total Cash":
                if j + 1 < self.n:
                    m = re.match(r"^LKR ([0-9,]+)$",
                                 self.lines[j + 1].strip())
                    if m:
                        cash = parse_money(m.group(1))
            elif t == "Total Property Value":
                if j + 1 < self.n:
                    m = re.match(r"^LKR ([0-9,]+)$",
                                 self.lines[j + 1].strip())
                    if m:
                        prop = parse_money(m.group(1))
            elif t == "Outstanding Loans":
                if j + 1 < self.n:
                    m = re.match(r"^LKR ([0-9,]+)$",
                                 self.lines[j + 1].strip())
                    if m:
                        loans = parse_money(m.group(1))
                    else:
                        loans = 0
            elif t == "Net Worth":
                if j + 1 < self.n:
                    m = re.match(r"^LKR ([0-9,]+)$",
                                 self.lines[j + 1].strip())
                    if m:
                        nw = parse_money(m.group(1))
            j += 1

        if winner is not None and cash is not None and prop is not None \
                and loans is not None and nw is not None:
            if cash + prop - loans != nw:
                self.report("BUG",
                            "Winner %s final arithmetic: %d + %d - %d = %d, "
                            "printed net worth %d." %
                            (PLAYERS[winner], cash, prop, loans,
                             cash + prop - loans, nw), ln, "")

        # final standings: bankrupt players must be 0
        cur = None
        while j < self.n:
            t = self.lines[j].strip()
            if t in P2I:
                cur = P2I[t]
            elif cur is not None:
                m = re.match(r"^Cash : LKR ([0-9,]+)$", t)
                if m:
                    c = parse_money(m.group(1))
                    if self.bankrupt[cur] and c != 0:
                        self.report("BUG",
                                    "Final: bankrupt %s has cash %d." %
                                    (PLAYERS[cur], c), ln, t)
                m = re.match(r"^Net Worth : LKR ([0-9,]+)$", t)
                if m:
                    v = parse_money(m.group(1))
                    if self.bankrupt[cur] and v != 0:
                        self.report("BUG",
                                    "Final: bankrupt %s has net worth %d." %
                                    (PLAYERS[cur], v), ln, t)
            j += 1


def analyze(path):
    a = Analyzer(path)
    a.run()
    print("=" * 70)
    print("LOG: %s" % path)
    print("=" * 70)
    bugs = [f for f in a.findings if f["level"] == "BUG"]
    reviews = [f for f in a.findings if f["level"] == "REVIEW"]
    print("confirmed bugs: %d   review items: %d" % (len(bugs), len(reviews)))
    print("-" * 70)
    for f in bugs + reviews:
        print("[%s] line %d: %s" % (f["level"], f["line"], f["claim"]))
        if f["quote"]:
            print("      evidence: \"%s\"" % f["quote"])
    print()
    return a.findings


if __name__ == "__main__":
    for path in sys.argv[1:]:
        analyze(path)
