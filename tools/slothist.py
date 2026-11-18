"""slothist.py RUN [f0 f1] -- from work/runs/RUN/ram.bin (tools/run.lua's snapshots): which object types
were seen in which slot (ram $1800+slot), grouped by the wave parameters ($44,$45,$46) in force.
Confirms the slot floors of the three spawners and the fixed slot ranges."""
import collections
import os
import struct
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REC = 4 + 192 + 2048 + 1536


def snaps(run):
    d = open(os.path.join(HERE, "work", "runs", run, "ram.bin"), "rb").read()
    for i in range(0, len(d) - REC + 1, REC):
        fr = struct.unpack("<I", d[i:i + 4])[0]
        zp = d[i + 4:i + 196]
        lo = d[i + 196:i + 196 + 2048]
        hi = d[i + 196 + 2048:i + REC]

        def rd(a, zp=zp, lo=lo, hi=hi):
            if a < 0x100:
                return zp[a - 0x40]
            if a < 0x2000:
                return lo[a - 0x1800]
            return hi[a - 0x2200]
        yield fr, rd


def main():
    run = sys.argv[1]
    f0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    f1 = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 9
    bytype = collections.defaultdict(collections.Counter)      # type -> slot counter
    floors = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    maxlive = collections.defaultdict(collections.Counter)
    n = 0
    for fr, rd in snaps(run):
        if not (f0 <= fr <= f1):
            continue
        n += 1
        key = (rd(0x44), rd(0x45), rd(0x46))
        cnt = collections.Counter()
        for s in range(32):
            t = rd(0x1800 + s)
            if t < 0x80:
                bytype[t][s] += 1
                cnt[t] += 1
                if t in (4, 5, 6):
                    floors[key][t][s] += 1
        for t in (4, 5, 6):
            maxlive[key][t] = max(maxlive[key][t], cnt[t])
    print("%d snapshots" % n)
    print("type: slots seen (count)")
    for t in sorted(bytype):
        c = bytype[t]
        print("  %02X: slots %02X-%02X  n=%d" % (t, min(c), max(c), sum(c.values())))
    print("by ($44,$45,$46): lowest slot / max alive for types 6,5,4")
    for key in sorted(floors):
        row = []
        for t in (6, 5, 4):
            c = floors[key][t]
            row.append("t%d min %s max-alive %d" % (t, ("%02X" % min(c)) if c else "--", maxlive[key][t]))
        print("  %02X %02X %02X: %s" % (key + ("; ".join(row),)))


if __name__ == "__main__":
    main()
