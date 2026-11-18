"""ann.py -- small editor for annotations.json (run from anywhere).
  ann.py entry f7:C332 f7:C363 ...
  ann.py label f7:C2D2=PhaseWaves b3:9000=Foo ...
  ann.py ram 75=CurPlayer 1800=ObjType ...
  ann.py comment f7:C2D2 "text"
  ann.py block f7:C2C4 14 name "note"
  ann.py merge file.json      (keys: entries, labels, ram, comments, blocks)
Then regenerate: disasm.py + verify.py (tools/regen.sh)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(HERE, "annotations.json")


def norm(loc):
    sp, ad = loc.split(":")
    return "%s:%04X" % (sp, int(ad, 16))


def apply(d, kind, args):
    if kind == "entry":
        for a in args:
            a = norm(a)
            if a not in d["entries"]:
                d["entries"].append(a)
    elif kind == "label":
        for a in args:
            k, v = a.split("=")
            d["labels"][norm(k)] = v
    elif kind == "ram":
        for a in args:
            k, v = a.split("=")
            d["ram"][k.upper().lstrip("0") or "0"] = v
    elif kind == "comment":
        d["comments"][norm(args[0])] = args[1]
    elif kind == "block":
        loc = norm(args[0])
        d["blocks"] = [b for b in d["blocks"] if b["loc"] != loc]
        b = {"loc": loc, "len": int(args[1], 0), "name": args[2]}
        if len(args) > 3:
            b["note"] = args[3]
        d["blocks"].append(b)


def main():
    d = json.load(open(P, encoding="utf-8"))
    kind, args = sys.argv[1], sys.argv[2:]
    if kind == "merge":
        m = json.load(open(args[0], encoding="utf-8"))
        apply(d, "entry", m.get("entries", []))
        apply(d, "label", ["%s=%s" % kv for kv in m.get("labels", {}).items()])
        apply(d, "ram", ["%s=%s" % kv for kv in m.get("ram", {}).items()])
        for k, v in m.get("comments", {}).items():
            apply(d, "comment", [k, v])
        for b in m.get("blocks", []):
            apply(d, "block", [b["loc"], str(b["len"]), b["name"]] + ([b["note"]] if b.get("note") else []))
    else:
        apply(d, kind, args)
    json.dump(d, open(P, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
