#!/bin/sh
# regenerate the listing from annotations.json and check the round trip
cd "$(dirname "$0")/.."
T="${A7800_TOOLKIT:-a7800-toolkit/tools}"
python "$T/disasm.py" work/ps.a78 -c annotations.json -o src "$@" 2>&1 | grep -E "^  (b|f)[0-9] +bank|lint|error|Error|Traceback"
python "$T/verify.py" work/ps.a78 -d src 2>&1 | tail -1
