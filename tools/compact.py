"""compact.py SPACE START END  -- print a dense view of the generated listing (src/<space>.asm)
between two addresses (hex): 'ADDR  MNEMONIC OPERAND', labels and xrefs kept short.
Saves reading context; the listing itself is disposable (regenerate with disasm.py)."""
import re
import sys
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    space, a0, a1 = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
    xr = "-x" in sys.argv
    path = os.path.join(HERE, "src", space + ".asm")
    cur = None
    out = []
    pend = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        m = re.search(r";\s*([0-9A-F]{4})(?::|\s\s)", line)
        if m:
            cur = int(m.group(1), 16)
            body = line[:line.rfind(";")].strip() if ";" in line else line.strip()
            # keep a trailing free comment (bank switch notes)
            tail = ""
            mm = re.search(r";\s*[0-9A-F]{4}:\s*(?:[0-9A-F]{2}\s)+\s*(.*)$", line)
            if mm and mm.group(1).strip():
                tail = "  ; " + mm.group(1).strip()
            body = re.sub(r"\s+", " ", body)
            if a0 <= cur <= a1:
                out.extend(pend)
                out.append("%04X  %s%s" % (cur, body, tail))
            pend = []
        else:
            s = line.strip()
            if not s:
                continue
            if s.startswith("; xrefs:"):
                if xr:
                    pend.append("      " + s)
                continue
            if cur is not None:
                pend.append(s if not s.startswith(";") else "      " + s[:160])
    print("\n".join(out))


if __name__ == "__main__":
    main()
