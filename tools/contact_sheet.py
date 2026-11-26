#!/usr/bin/env python3
"""Contact sheets of the photos, to look them over: tools/contact_sheet.py <out folder>.
Uses sips (macOS) to make small PNG copies, reads those itself, and writes sheets of 40."""
import json, os, struct, subprocess, sys, tempfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
DAM = os.path.join(PROJECT, "ui.content.shared", "src", "main", "content", "jcr_root", "content", "dam", "weekender-shared")
W, H, COLS, ROWS, PAD = 180, 120, 8, 5, 6


def read_png(path):
    data = open(path, "rb").read()
    pos, idat, w = 8, b"", 0
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    bpp = {2: 3, 6: 4, 0: 1, 4: 2}[colour]
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev = [], bytearray(stride)
    i = 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return w, h, bpp, rows


def write_png(path, w, h, px):
    raw = b"".join(b"\0" + bytes(px[y * w * 3:(y + 1) * w * 3]) for y in range(h))
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
                           chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    names = sorted(k for k, v in json.load(open(os.path.join(HERE, "images.json"))).items() if v.get("commons"))
    tmp = tempfile.mkdtemp()
    per = COLS * ROWS
    index = []
    for s in range(0, len(names), per):
        sw, sh = COLS * (W + PAD) + PAD, ROWS * (H + PAD) + PAD
        px = bytearray([255]) * (sw * sh * 3)
        for n, name in enumerate(names[s:s + per]):
            src = os.path.join(DAM, name, "_jcr_content", "renditions", "original")
            small = os.path.join(tmp, "t.png")
            subprocess.run(["sips", "-s", "format", "png", "-z", str(H), str(W), src, "--out", small], capture_output=True)
            try:
                w, h, bpp, rows = read_png(small)
            except Exception as e:
                continue
            ox, oy = PAD + (n % COLS) * (W + PAD), PAD + (n // COLS) * (H + PAD)
            for y in range(min(h, H)):
                line = rows[y]
                base = ((oy + y) * sw + ox) * 3
                for x in range(min(w, W)):
                    px[base + x * 3:base + x * 3 + 3] = line[x * bpp:x * bpp + 3] if bpp >= 3 else bytes([line[x * bpp]]) * 3
            index.append("%d.%d %s" % (s // per + 1, n + 1, name))
        write_png(os.path.join(out, "sheet-%d.png" % (s // per + 1)), sw, sh, px)
    open(os.path.join(out, "index.txt"), "w").write("\n".join(index) + "\n")
    print("%d photos on %d sheets" % (len(index), (len(names) + per - 1) // per))


if __name__ == "__main__":
    main()
