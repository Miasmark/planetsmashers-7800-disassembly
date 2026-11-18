"""rtstables.py [space] -- find 'LDA tbl+1,i / PHA / LDA tbl,i / PHA / RTS' dispatches in the generated
listing, read each table from the ROM as (target-1) words and print the entry points
(until a word is implausible or the table runs into a traced instruction).
Prints 'space:ADDR' per line, ready for: python tools/ann.py entry $(python tools/rtstables.py f7)"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rom = open(os.path.join(HERE, "work", "ps.a78"), "rb").read()[128:]


def main():
    space = sys.argv[1] if len(sys.argv) > 1 else "f7"
    verbose = "-v" in sys.argv
    bank = int(space[1])
    base = 0xC000 if space == "f7" else (0x4000 if space == "f6" else 0x8000)
    img = rom[bank * 0x4000:(bank + 1) * 0x4000]
    lines = open(os.path.join(HERE, "src", space + ".asm"), encoding="utf-8", errors="replace").read().split("\n")
    ins = []          # (addr, text)
    code_addrs = set()
    for l in lines:
        m = re.search(r";\s*([0-9A-F]{4}):\s*((?:[0-9A-F]{2}\s)+)", l)
        if m and not l.strip().startswith(".byte"):
            a = int(m.group(1), 16)
            ins.append((a, bytes(int(x, 16) for x in m.group(2).split())))
            code_addrs.add(a)
    tables = []
    for i in range(len(ins) - 4):
        a0, b0 = ins[i]
        # LDA abs,X (BD) or abs,Y (B9); PHA (48); LDA abs,i; PHA; RTS (60)
        if b0[0] in (0xBD, 0xB9) and ins[i + 1][1] == b"\x48" and ins[i + 2][1][0] in (0xBD, 0xB9) \
                and ins[i + 3][1] == b"\x48" and ins[i + 4][1] == b"\x60":
            hi = b0[1] | (b0[2] << 8)
            lo = ins[i + 2][1][1] | (ins[i + 2][1][2] << 8)
            if hi == lo + 1:
                tables.append((a0, lo))
    out = []
    for site, t in tables:
        n = 0
        a = t
        while a + 1 < base + 0x4000 and a not in code_addrs and (a + 1) not in code_addrs:
            w = img[a - base] | (img[a + 1 - base] << 8)
            tgt = (w + 1) & 0xFFFF
            if not (base <= tgt < base + 0x4000):
                break
            out.append("%s:%04X" % (space, tgt))
            n += 1
            a += 2
        if verbose:
            print("# site %04X table %04X: %d entries" % (site, t, n), file=sys.stderr)
    print(" ".join(sorted(set(out))))


if __name__ == "__main__":
    main()
