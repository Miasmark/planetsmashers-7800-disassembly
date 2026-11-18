"""fpstats.py RUN [f0] -- summarise work/runs/RUN/fp.txt (run.lua PS_FPROBE): by number of live object
slots, the main-loop passes per frame (1.0 = logic at 60 Hz) and the NMI's length in raster lines
(entry line to RTI)."""
import collections
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    run = sys.argv[1]
    f0 = int(sys.argv[2]) if len(sys.argv) > 2 else 700
    by = collections.defaultdict(list)
    ins = collections.Counter()
    for l in open(os.path.join(HERE, "work", "runs", run, "fp.txt")):
        fr, p, a, b, live = l.split()
        if int(fr) < f0:
            continue
        by[int(live)].append((int(p), float(b) - float(a)))
        ins[round(float(a))] += 1
    print("NMI entry line (count):", dict(ins.most_common(4)))
    print("live  frames  passes/frame  nmi lines mean  max")
    for live in sorted(by):
        v = by[live]
        print("%4d  %6d  %11.2f  %13.1f  %5.1f" % (live, len(v), sum(x[0] for x in v) / len(v),
                                                 sum(x[1] for x in v) / len(v), max(x[1] for x in v)))


if __name__ == "__main__":
    main()
