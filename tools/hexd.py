"""hexd.py BANK ADDR LEN [WIDTH] -- hex dump of ROM bytes (bank 0-7; ADDR as mapped: $8000-$BFFF
window, $C000+ fixed bank 7, $4000-$7FFF bank 6)."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rom = open(os.path.join(HERE, "work", "ps.a78"), "rb").read()[128:]


def get(bank, addr, n):
    if addr >= 0xC000:
        off = 7 * 0x4000 + addr - 0xC000
    elif addr >= 0x8000:
        off = bank * 0x4000 + addr - 0x8000
    else:
        off = 6 * 0x4000 + addr - 0x4000
    return rom[off:off + n]


if __name__ == "__main__":
    bank, addr, n = int(sys.argv[1]), int(sys.argv[2], 16), int(sys.argv[3], 0)
    w = int(sys.argv[4]) if len(sys.argv) > 4 else 16
    d = get(bank, addr, n)
    for i in range(0, n, w):
        print("%04X  %s" % (addr + i, " ".join("%02X" % b for b in d[i:i + w])))
