"""bankpic.py -- render every bank's four 4K blocks as 16-line strips (line-planar: the top line of a
16-line zone object is page +15), 2 bits a pixel, grey. One PNG per bank in work/gfx/bankN.png:
strips for $x000, $x400.. are split in four 256-px-wide rows so the picture is 512 wide.
Also prints, per bank and 4K block, the share of zero bytes. Needs Pillow."""
import os

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rom = open(os.path.join(HERE, "work", "ps.a78"), "rb").read()[128:]
OUT = os.path.join(HERE, "work", "gfx")
os.makedirs(OUT, exist_ok=True)
GREY = [0, 90, 170, 255]


def main():
    for b in range(8):
        img = rom[b * 0x4000:(b + 1) * 0x4000]
        base = 0xC000 if b == 7 else 0x8000
        zs = []
        # 4 blocks x (256 bytes = 1024 px) -> split each strip into 2 halves of 512 px
        W, SH = 512, 16
        pic = Image.new("L", (W, (SH + 2) * 8), 40)
        for blk in range(4):
            block = img[blk * 0x1000:(blk + 1) * 0x1000]
            zs.append(100 * block.count(0) // 0x1000)
            for half in range(2):
                y0 = (blk * 2 + half) * (SH + 2)
                for line in range(16):
                    page = block[(15 - line) * 256:(16 - line) * 256]
                    for xb in range(128):
                        v = page[half * 128 + xb]
                        for p in range(4):
                            c = (v >> (6 - 2 * p)) & 3
                            pic.putpixel((xb * 4 + p, y0 + line), GREY[c])
        pic = pic.resize((W * 2, pic.size[1] * 3), Image.NEAREST)
        pic.save(os.path.join(OUT, "bank%d.png" % b))
        print("bank %d (window base $%04X): zero%% per 4K block: %s" % (b, base, zs))


if __name__ == "__main__":
    main()
