"""run.py NAME [KEY=VALUE ...] -- one windowless MAME run of tools/run.lua in work/runs/NAME.
KEYs are run.lua's PS_* variables without the prefix (FRAMES=7200 SEED=3 XT=xt.log RAM=ram.bin
SNAP=600 POKES=... LOCK=... PEEK=... WTAP=... RTAP=...). File values are relative to the run dir.
MAME never opens a window: -video none -sound none -nothrottle, ui.ini skip_warnings 1."""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAME = os.environ.get("A7800_MAME", "a78.exe")


def main():
    name = sys.argv[1]
    rd = os.path.join(ROOT, "work", "runs", name)
    shutil.rmtree(rd, ignore_errors=True)
    os.makedirs(os.path.join(rd, "cfg"))
    open(os.path.join(rd, "ui.ini"), "w").write("skip_warnings 1\n")
    cart = os.path.join(ROOT, "work", "ps.a78")
    env = dict(os.environ)
    for kv in sys.argv[2:]:
        k, v = kv.split("=", 1)
        if k == "CART":
            cart = v
            continue
        env["PS_" + k] = v
    cmd = [MAME, "a7800", "-cart", cart, "-bios", "skip", "-skip_gameinfo", "-video", "none",
           "-sound", "none", "-nothrottle", "-inipath", ".", "-cfg_directory", "cfg",
           "-nvram_directory", "nv", "-snapshot_directory", "snap",
           "-autoboot_script", os.path.join(HERE, "run.lua")]
    with open(os.path.join(rd, "mame.out"), "w") as o:
        r = subprocess.run(cmd, cwd=rd, env=env, stdout=o, stderr=subprocess.STDOUT, timeout=3500)
    print(name, "exit", r.returncode, os.listdir(rd))


if __name__ == "__main__":
    main()
