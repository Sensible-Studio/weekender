#!/usr/bin/env python3
"""Weekender's own look, drawn here: the logo, the favicons, the pictures of the templates and the
"page not found" photo. Nothing of the project this one started from is left in those files.

    python3 tools/brand.py

No dependencies: the PNG files are written pixel by pixel, the logo is an SVG.
"""
import json, os, re, shutil, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import import_images as images  # the search and the asset files

GREEN, SAND, INK, WHITE, GREY, LIGHT = (31, 95, 85), (232, 196, 124), (32, 32, 32), (255, 255, 255), (206, 210, 214), (240, 242, 244)


class Canvas:
    def __init__(self, w, h, colour=WHITE):
        self.w, self.h = w, h
        self.px = [colour] * (w * h)

    def rect(self, x0, y0, x1, y1, colour):
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            row = y * self.w
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                self.px[row + x] = colour

    def circle(self, cx, cy, r, colour):
        for y in range(max(0, int(cy - r)), min(self.h, int(cy + r) + 1)):
            for x in range(max(0, int(cx - r)), min(self.w, int(cx + r) + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.px[y * self.w + x] = colour

    def triangle(self, a, b, c, colour):
        def side(p, q, r):
            return (p[0] - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (p[1] - r[1])
        xs, ys = [a[0], b[0], c[0]], [a[1], b[1], c[1]]
        for y in range(max(0, int(min(ys))), min(self.h, int(max(ys)) + 1)):
            for x in range(max(0, int(min(xs))), min(self.w, int(max(xs)) + 1)):
                p = (x + .5, y + .5)
                d = [side(p, a, b), side(p, b, c), side(p, c, a)]
                if not (min(d) < 0 and max(d) > 0):
                    self.px[y * self.w + x] = colour

    def png(self):
        raw = b"".join(b"\0" + b"".join(bytes(p) for p in self.px[y * self.w:(y + 1) * self.w]) for y in range(self.h))
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)) + \
            chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def mark(size):
    """The sign: a sun over two peaks, on green."""
    c = Canvas(size, size, GREEN)
    s = size / 100.0
    c.circle(68 * s, 32 * s, 11 * s, SAND)
    c.triangle((10 * s, 82 * s), (42 * s, 30 * s), (74 * s, 82 * s), WHITE)
    c.triangle((46 * s, 82 * s), (70 * s, 48 * s), (92 * s, 82 * s), (214, 232, 226))
    return c.png()


def logo(colour):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 239.35 89.09" role="img" aria-label="Weekender">'
            '<rect x="2" y="18" width="53" height="53" rx="9" fill="#1f5f55"/>'
            '<circle cx="38" cy="35" r="6" fill="#e8c47c"/>'
            '<path d="M7 62 24 34 41 62Z" fill="#fff"/><path d="M26 62 39 44 51 62Z" fill="#d6e8e2"/>'
            '<text x="66" y="56" font-family="\'Helvetica Neue\', Helvetica, Arial, sans-serif" font-size="31" '
            'font-weight="700" letter-spacing="-.6" fill="%s">Weekender</text></svg>\n' % colour).encode()


def template_picture(kind):
    """A drawing of a page layout, for the template picker."""
    c = Canvas(480, 460, WHITE)
    c.rect(0, 0, 480, 44, LIGHT)
    c.rect(18, 12, 38, 32, GREEN)
    c.rect(48, 18, 130, 26, GREY)
    for i in range(4):
        c.rect(300 + i * 42, 18, 332 + i * 42, 26, GREY)
    if kind == "landing":
        c.rect(0, 44, 480, 230, (190, 214, 208))
        c.rect(40, 150, 260, 172, WHITE)
        c.rect(40, 184, 180, 196, WHITE)
        for i in range(3):
            c.rect(24 + i * 150, 254, 156 + i * 150, 344, GREY)
            c.rect(24 + i * 150, 354, 126 + i * 150, 364, LIGHT)
    elif kind == "article":
        c.rect(60, 70, 420, 92, GREY)
        c.rect(60, 104, 240, 114, LIGHT)
        c.rect(60, 132, 420, 262, (190, 214, 208))
        for i in range(7):
            c.rect(60, 284 + i * 20, 420 - (60 if i % 3 == 2 else 0), 294 + i * 20, LIGHT)
    elif kind == "adventure":
        c.rect(0, 44, 480, 190, (190, 214, 208))
        c.rect(24, 210, 300, 230, GREY)
        for i in range(6):
            c.rect(24, 250 + i * 20, 300, 260 + i * 20, LIGHT)
        c.rect(324, 210, 456, 380, LIGHT)
        c.rect(340, 228, 440, 240, GREY)
        c.rect(340, 340, 440, 364, GREEN)
    elif kind == "fragment":
        c.rect(40, 90, 440, 250, LIGHT)
        c.rect(60, 112, 280, 130, GREY)
        for i in range(4):
            c.rect(60, 150 + i * 20, 420, 160 + i * 20, GREY)
    else:
        c.rect(40, 70, 300, 92, GREY)
        for i in range(5):
            c.rect(40, 116 + i * 20, 440, 126 + i * 20, LIGHT)
        c.rect(40, 236, 230, 356, GREY)
        c.rect(250, 236, 440, 356, GREY)
    c.rect(0, 420, 480, 460, LIGHT)
    return c.png()


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(data)


def clean_renditions(asset):
    renditions = os.path.join(asset, "_jcr_content", "renditions")
    for name in os.listdir(renditions):
        if not name.startswith("original"):
            p = os.path.join(renditions, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)


def main():
    done = []
    # favicons
    for base in ("ui.frontend/src/main/webpack/resources/images/favicons",
                 "ui.apps/src/main/content/jcr_root/apps/weekender/clientlibs/clientlib-site/resources/images/favicons"):
        folder = os.path.join(PROJECT, base)
        if os.path.isdir(folder):
            for name in os.listdir(folder):
                m = re.match(r"favicon-(\d+)\.png$", name)
                if m:
                    write(os.path.join(folder, name), mark(int(m.group(1))))
                    done.append(base + "/" + name)

    for module in ("ui.content", "ui.content.sample"):
        root = os.path.join(PROJECT, module, "src", "main", "content", "jcr_root")
        if not os.path.isdir(root):
            continue
        # the pictures of the templates and of their types
        wcm = os.path.join(root, "conf", "weekender", "settings", "wcm")
        for dirpath, _, files in os.walk(wcm):
            if "thumbnail.png" in files:
                name = os.path.basename(dirpath)
                kind = "landing" if "landing" in name else "article" if "article" in name else "adventure" if "adventure" in name \
                    else "fragment" if "fragment" in name else "content"
                write(os.path.join(dirpath, "thumbnail.png"), template_picture(kind))
                done.append(os.path.relpath(dirpath, PROJECT) + "/thumbnail.png")
        # the logo: SVG only (the PNG copies are gone, what used them uses the SVG)
        site = os.path.join(root, "content", "dam", "weekender", "en", "site")
        for variant, colour in (("dk", "#202020"), ("light", "#ffffff")):
            asset = os.path.join(site, "weekender-logo-%s.svg" % variant)
            if os.path.isdir(asset):
                write(os.path.join(asset, "_jcr_content", "renditions", "original"), logo(colour))
                clean_renditions(asset)
                open(os.path.join(asset, ".content.xml"), "w").write(images.ASSET_XML.format(
                    mime="image/svg+xml", title="Weekender logo (%s)" % ("dark" if variant == "dk" else "light"), author="Weekender",
                    licence="CC0", page="", description="The Weekender logo, drawn for this project.", size=""))
                done.append(os.path.relpath(asset, PROJECT))
            old = os.path.join(site, "weekender-logo-%s.png" % variant)
            if os.path.isdir(old):
                shutil.rmtree(old)
        # small pictures kept beside pages and profiles: the sign
        for dirpath, dirs, files in os.walk(root):
            for name in files:
                p = os.path.join(dirpath, name)
                if name.startswith("_dam_thumbnail_") and name.endswith(".png"):
                    write(p, mark(int(re.sub(r"\D", "", name) or 48)))
                    done.append(os.path.relpath(p, PROJECT))
                elif name in ("file", "image") and "/content/dam/" not in dirpath + "/":
                    if open(p, "rb").read(8).startswith(b"\x89PNG"):
                        write(p, mark(256))
                        done.append(os.path.relpath(p, PROJECT))

    # what used the PNG logos
    for dirpath, dirs, files in os.walk(PROJECT):
        dirs[:] = [d for d in dirs if d not in (".git", "target", "node_modules", "node", "tools")]
        for name in files:
            p = os.path.join(dirpath, name)
            try:
                text = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            new = text.replace("weekender-logo-dk.png", "weekender-logo-dk.svg").replace("weekender-logo-light.png", "weekender-logo-light.svg")
            if new != text:
                open(p, "w", encoding="utf-8", newline="").write(new)

    # the photo of the "page not found" pages
    site_manifest = os.path.join(HERE, "images-site.json")
    record = json.load(open(site_manifest)) if os.path.exists(site_manifest) else {}
    if "not-found.jpg" not in record:
        shared = json.load(open(images.MANIFEST)) if os.path.exists(images.MANIFEST) else {}
        used = {m["commons"] for m in shared.values() if m.get("commons")}
        found = []
        for query in ("foggy forest path", "fog mountain trail", "misty forest road"):
            found = images.search(query, used)
            if found:
                break
        if found:
            c = found[0]
            data = images.get(c["download"], binary=True)
            for module in ("ui.content", "ui.content.sample"):
                asset = os.path.join(PROJECT, module, "src", "main", "content", "jcr_root", "content", "dam", "weekender", "en", "site", "not-found.jpg")
                if os.path.isdir(asset):
                    write(os.path.join(asset, "_jcr_content", "renditions", "original"), data)
                    clean_renditions(asset)
                    open(os.path.join(asset, ".content.xml"), "w").write(images.ASSET_XML.format(
                        mime="image/jpeg", title=images.x(c["title"]), author=images.x(c["author"]), licence=images.x(c["licence"]),
                        page=images.x(c["page"]), description=images.x("%s. Photo: %s, %s, via Wikimedia Commons." % (c["title"], c["author"], c["licence"])),
                        size='\n            tiff:ImageWidth="{Long}%d"\n            tiff:ImageLength="{Long}%d"' % (c["width"], c["height"])))
            record["not-found.jpg"] = c
            json.dump(record, open(site_manifest, "w"), indent=1, sort_keys=True)
            done.append("not-found.jpg <- " + c["commons"])
    print("%d files drawn or replaced" % len(done))
    for d in done[:60]:
        print("  " + d)


if __name__ == "__main__":
    main()
