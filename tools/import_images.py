#!/usr/bin/env python3
"""Replaces every photo of the shared media folder with a freely licensed one from Wikimedia Commons.

The project this one started from shipped stock photos that may only be shown as part of that demo.
Here each photo is one whose licence lets anybody use it (public domain, CC0 or CC BY), found by a
search for what the folder is about, downloaded at 1920 px, and stored as a new asset with its
author, licence and source in its metadata. IMAGES.md lists them all; tools/images.json is the
same list for this script, so a second run changes nothing unless --refresh is given.

    python3 tools/import_images.py            # fetch what is missing, rewrite the references
    python3 tools/import_images.py --refresh  # choose again (keeps nothing)

No dependencies. It talks to commons.wikimedia.org only.
"""
import html, json, os, re, shutil, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
DAM = os.path.join(PROJECT, "ui.content.shared", "src", "main", "content", "jcr_root", "content", "dam", "weekender-shared")
JCR_DAM = "/content/dam/weekender-shared"
MANIFEST = os.path.join(HERE, "images.json")
UA = {"User-Agent": "WeekenderDemoBuilder/0.1 (demo site image import)"}
API = "https://commons.wikimedia.org/w/api.php"
ALLOWED = ("cc0", "public domain", "pd", "cc by 2.0", "cc by 2.5", "cc by 3.0", "cc by 4.0", "cc-by-2.0", "cc-by-3.0", "cc-by-4.0")
NOT_A_PHOTO = re.compile(r"map|logo|diagram|flag|coat of arms|plaque|poster|stamp|chart|graph|sign\b|icon|drawing|painting|"
                         r"engraving|lithograph|illustration|screenshot|book|page|document|letter|memorial|grave|portrait|headshot|"
                         r"satellite|nasa|modis|landsat|sentinel|iss0|from space|aerial|"
                         r"race|championship|competition|world cup|team|ceremony|parade|festival|crowd|"
                         r"child|kids\\b|girl|boy\\b|baby|panneau|artwork|marquetry|sculpture|store|shop\b|parking|entrance|station|statue|monument|museum|church|"
                         r"\b1[5-8]\d\d\b|\b19[0-7]\d\b", re.I)
AGENCIES = re.compile(r"national park|nps|forest service|usfs|usgs|geological survey|noaa|bureau of land|blm|fish and wildlife|usfws", re.I)


def series(title):
    """Photos of one series differ by a number: one of them is enough."""
    return re.sub(r"[\d\W_]+", " ", re.sub(r"^File:|\.[A-Za-z]+$", "", title).lower()).strip()

# what each folder is about: searches, tried in order until the folder has its photos
QUERIES = {
    "en/activities/camping": ["camping tent mountains", "tent campsite lake"],
    "en/activities/climbing": ["rock climbing climber cliff", "sport climbing rock face"],
    "en/activities/cycling": ["road cycling cyclist mountain road", "bicycle touring road"],
    "en/activities/hiking": ["hiking trail mountains hikers", "hiker mountain path"],
    "en/activities/skiing": ["alpine skiing skier slope", "skiing powder snow mountain"],
    "en/adventures/bali-surf-camp": ["surfing Bali", "Bali beach surf"],
    "en/adventures/beervana-portland": ["craft brewery Portland Oregon", "beer tasting flight brewery", "Portland Oregon skyline"],
    "en/adventures/climbing-new-zealand": ["rock climbing New Zealand", "New Zealand Southern Alps mountains"],
    "en/adventures/colorado-rock-climbing": ["rock climbing Colorado", "Eldorado Canyon Colorado"],
    "en/adventures/cycling-southern-utah": ["mountain biking Moab Utah", "Utah desert road red rock"],
    "en/adventures/cycling-tuscany": ["cycling Tuscany", "Tuscany hills road cypress", "Val d'Orcia landscape"],
    "en/adventures/downhill-skiing-wyoming": ["skiing Jackson Hole", "Grand Teton winter snow"],
    "en/adventures/gastronomic-marais-tour": ["Le Marais Paris street", "Paris cafe terrace", "Paris bakery"],
    "en/adventures/napa-wine-tasting": ["Napa Valley vineyard", "wine tasting vineyard California"],
    "en/adventures/riverside-camping-australia": ["camping river Australia", "Australian outback river gum trees", "campfire camping night"],
    "en/adventures/ski-touring-mont-blanc": ["ski touring Mont Blanc", "Mont Blanc massif winter", "ski mountaineering Alps"],
    "en/adventures/surf-camp-in-costa-rica": ["surfing Costa Rica", "Costa Rica Pacific beach", "Costa Rica beach sunset"],
    "en/adventures/tahoe-skiing": ["skiing Lake Tahoe", "Lake Tahoe winter snow"],
    "en/adventures/west-coast-cycling": ["Pacific Coast Highway Big Sur", "cycling California coast"],
    "en/adventures/whistler-mountain-biking": ["mountain biking Whistler", "mountain bike trail forest British Columbia", "Whistler mountain summer"],
    "en/adventures/yosemite-backpacking": ["backpacking Yosemite", "Yosemite Valley landscape"],
    "en/magazine/alaska-adventure": ["Alaska wilderness mountains", "Denali National Park landscape", "Alaska glacier"],
    "en/magazine/arctic-surfing": ["surfing Lofoten", "Lofoten beach winter", "Unstad beach"],
    "en/magazine/fly-fishing-amazon": ["fly fishing river angler", "Amazon river rainforest"],
    "en/magazine/la-skateparks": ["skatepark Los Angeles", "Venice Beach skatepark", "skateboarding skatepark bowl"],
    "en/magazine/san-diego-surf-spots": ["surfing San Diego", "La Jolla beach surf", "Ocean Beach San Diego pier"],
    "en/magazine/skitouring": ["ski touring", "backcountry skiing ascent", "ski tracks powder mountain"],
    "en/magazine/western-australia": ["Western Australia coast", "Karijini National Park", "Western Australia beach turquoise"],
}
FALLBACK = ["mountain landscape lake", "coast cliffs ocean", "forest trail"]


def get(url, params=None, binary=False):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
            return data if binary else json.loads(data)
        except Exception as e:  # the service asks to slow down now and then
            time.sleep(3 * (attempt + 1))
            last = e
    raise last


def plain(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


def search(query, used):
    """Photos for a query: landscape JPEGs, wide enough, under a licence that lets anybody use them."""
    out = []
    data = get(API, {"action": "query", "format": "json", "generator": "search", "gsrsearch": query + " filetype:bitmap",
                     "gsrnamespace": "6", "gsrlimit": "40", "prop": "imageinfo",
                     "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "1920"})
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        licence = plain(meta.get("LicenseShortName", {}).get("value"))
        title = p.get("title", "")
        if title in used or info.get("mime") != "image/jpeg" or licence.lower() not in ALLOWED:
            continue
        w, h = info.get("width", 0), info.get("height", 0)
        if w < 1900 or not h or not 1.25 <= w / h <= 2.1 or NOT_A_PHOTO.search(title):
            continue
        if plain(meta.get("Restrictions", {}).get("value")):
            continue  # trademarks, personality rights: leave those alone
        author = plain(meta.get("Artist", {}).get("value"))
        if licence.lower() in ("public domain", "pd") and not AGENCIES.search(author + " " + plain(meta.get("Credit", {}).get("value"))):
            continue  # "public domain" is mostly old pictures; photos of public agencies are the exception
        year = re.search(r"(1[89]|20)\d\d", plain(meta.get("DateTimeOriginal", {}).get("value")))
        if year and int(year.group(0)) < 1995:
            continue
        if series(title) in {series(u) for u in used} | {series(c["commons"]) for c in out}:
            continue
        out.append({
            "commons": title,
            "page": info.get("descriptionurl", ""),
            "download": info.get("thumburl") or info.get("url"),
            "width": info.get("thumbwidth") or w,
            "height": info.get("thumbheight") or h,
            "licence": licence,
            "licenceUrl": plain(meta.get("LicenseUrl", {}).get("value")),
            "author": plain(meta.get("Artist", {}).get("value"))[:120] or "unknown",
            "title": re.sub(r"\s+", " ", re.sub(r"^File:|\.[A-Za-z]+$", "", title).replace("_", " ")).strip()[:90],
        })
    return out


def x(text):
    return html.escape(text or "", quote=True).replace("\n", " ")


ASSET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<jcr:root xmlns:jcr="http://www.jcp.org/jcr/1.0" xmlns:nt="http://www.jcp.org/jcr/nt/1.0" xmlns:dam="http://www.day.com/dam/1.0" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:tiff="http://ns.adobe.com/tiff/1.0/"
    jcr:primaryType="dam:Asset">
    <jcr:content
        jcr:primaryType="dam:AssetContent">
        <metadata
            jcr:primaryType="nt:unstructured"
            dc:format="{mime}"
            dc:title="{title}"
            dc:creator="{author}"
            dc:rights="{licence}"
            dc:source="{page}"
            dc:description="{description}"{size}/>
        <related jcr:primaryType="nt:unstructured"/>
    </jcr:content>
</jcr:root>
"""
FILE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<jcr:root xmlns:jcr="http://www.jcp.org/jcr/1.0" xmlns:nt="http://www.jcp.org/jcr/nt/1.0"
    jcr:primaryType="nt:file">
    <jcr:content
        jcr:mimeType="{mime}"
        jcr:primaryType="nt:resource"/>
</jcr:root>
"""


def write_asset(folder, name, data, mime, title, author, licence, page, description, width=None, height=None):
    asset = os.path.join(DAM, folder, name)
    renditions = os.path.join(asset, "_jcr_content", "renditions")
    os.makedirs(os.path.join(renditions, "original.dir"), exist_ok=True)
    open(os.path.join(renditions, "original"), "wb").write(data)
    open(os.path.join(renditions, "original.dir", ".content.xml"), "w").write(FILE_XML.format(mime=mime))
    size = ""
    if width and height:
        size = '\n            tiff:ImageWidth="{Long}%d"\n            tiff:ImageLength="{Long}%d"' % (width, height)
    open(os.path.join(asset, ".content.xml"), "w").write(ASSET_XML.format(
        mime=mime, title=x(title), author=x(author), licence=x(licence), page=x(page), description=x(description), size=size))


def avatar(name, n):
    """A portrait nobody has rights in: initials on a colour."""
    words = [w for w in re.split(r"[^A-Za-z]+", name) if w and not w.isdigit()]
    initials = "".join(w[0].upper() for w in words[:2]) or "W"
    colour = ["#2f6f62", "#b5562b", "#3d5a80", "#7a4e8a", "#8a6d1f", "#356b3c", "#9a3b4f"][n % 7]
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
            '<rect width="600" height="600" fill="%s"/>'
            '<text x="300" y="300" dy=".35em" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" '
            'font-size="230" font-weight="700" fill="#ffffff" fill-opacity=".92">%s</text></svg>' % (colour, initials)).encode()


def pdf(title, lines):
    """A one-page PDF written by hand."""
    def esc(s):
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    text = "BT /F1 26 Tf 72 720 Td (%s) Tj ET\n" % esc(title)
    y = 680
    for line in lines:
        text += "BT /F1 12 Tf 72 %d Td (%s) Tj ET\n" % (y, esc(line))
        y -= 20
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        "<< /Length %d >>\nstream\n%sendstream" % (len(text), text),
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = "%PDF-1.4\n", []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += "%d 0 obj\n%s\nendobj\n" % (i, body)
    xref = len(out)
    out += "xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += "".join("%010d 00000 n \n" % o for o in offsets)
    out += "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return out.encode("latin-1")


def old_assets():
    """Every asset still as it came: (folder, name, mime)."""
    found = []
    for root, dirs, files in os.walk(DAM):
        if "original" in files and root.endswith(os.path.join("_jcr_content", "renditions")):
            asset = os.path.dirname(os.path.dirname(root))
            rel = os.path.relpath(asset, DAM)
            folder, name = os.path.split(rel)
            head = open(os.path.join(root, "original"), "rb").read(8)
            mime = "application/pdf" if head.startswith(b"%PDF") else "image/png" if head.startswith(b"\x89PNG") else \
                "image/svg+xml" if head.lstrip().startswith(b"<") else "image/jpeg"
            found.append((folder.replace(os.sep, "/"), name, mime))
    return sorted(found)


def main():
    refresh = "--refresh" in sys.argv
    manifest = {} if refresh or not os.path.exists(MANIFEST) else json.load(open(MANIFEST))
    done = {m["old"] for m in manifest.values()} | set(manifest)
    used = {m["commons"] for m in manifest.values() if m.get("commons")}
    todo = [a for a in old_assets() if "%s/%s" % (a[0], a[1]) not in done]
    by_folder = {}
    for folder, name, mime in todo:
        by_folder.setdefault(folder, []).append((name, mime))
    print("%d assets to replace in %d folders" % (len(todo), len(by_folder)))

    for folder, items in sorted(by_folder.items()):
        slug = folder.split("/")[-1]
        photos = [i for i in items if i[1] in ("image/jpeg", "image/png") and "contributors" not in folder]
        others = [i for i in items if i not in photos]
        candidates = []
        for query in QUERIES.get(folder, []) + FALLBACK:
            if len(candidates) >= len(photos):
                break
            for c in search(query, used | {c["commons"] for c in candidates}):
                candidates.append(c)
            time.sleep(1)
        start = len([k for k in manifest if k.startswith(folder + "/")])
        for n, (name, mime) in enumerate(photos):
            if n >= len(candidates):
                print("  !! no photo left for %s/%s" % (folder, name))
                continue
            c = candidates[n]
            data = get(c["download"], binary=True)
            time.sleep(1)
            if not data.startswith(b"\xff\xd8"):
                print("  !! not a JPEG: %s" % c["commons"])
                continue
            new = "%s-%d.jpg" % (slug, start + n + 1)
            shutil.rmtree(os.path.join(DAM, folder, name))
            write_asset(folder, new, data, "image/jpeg", c["title"], c["author"], c["licence"], c["page"],
                        "%s. Photo: %s, %s, via Wikimedia Commons." % (c["title"], c["author"], c["licence"]), c["width"], c["height"])
            used.add(c["commons"])
            manifest["%s/%s" % (folder, new)] = dict(c, old="%s/%s" % (folder, name))
            print("  %s/%s <- %s (%s)" % (folder, new, c["commons"][:60], c["licence"]))
        for n, (name, mime) in enumerate(others):
            base = re.sub(r"\.[A-Za-z]+$", "", name)
            shutil.rmtree(os.path.join(DAM, folder, name))
            if mime == "application/pdf":
                new = re.sub(r"[_]adobe$", "", base).replace("_", "-") + ".pdf"
                write_asset(folder, new, pdf("Weekender", ["A sample document of the Weekender demo site.", "It stands in for a brochure you could download here."]),
                            "application/pdf", "Weekender sample document", "Weekender", "CC0", "", "A sample document.")
                manifest["%s/%s" % (folder, new)] = {"old": "%s/%s" % (folder, name), "made": "a one-page sample PDF"}
            else:
                new = re.sub(r"-\d+$", "", base).replace("_", "-") + ".svg"
                write_asset(folder, new, avatar(base, n), "image/svg+xml", base.replace("-", " ").replace("_", " ").title(),
                            "Weekender", "CC0", "", "A drawn portrait: initials on a colour.")
                manifest["%s/%s" % (folder, new)] = {"old": "%s/%s" % (folder, name), "made": "initials on a colour"}
            print("  %s/%s (made here)" % (folder, new))
        json.dump(manifest, open(MANIFEST, "w"), indent=1, sort_keys=True)

    # folder thumbnails were made from the old photos
    for root, dirs, files in os.walk(os.path.join(PROJECT)):
        if any(p in root for p in ("/target", "/node_modules", "/.git")):
            continue
        for d in list(dirs):
            if d in ("folderThumbnail.dir",):
                shutil.rmtree(os.path.join(root, d))
                dirs.remove(d)
        for f in files:
            if f == "folderThumbnail":
                os.remove(os.path.join(root, f))

    # references, everywhere in the project
    pairs = sorted(((JCR_DAM + "/" + m["old"], JCR_DAM + "/" + new) for new, m in manifest.items()), key=lambda p: -len(p[0]))
    changed = 0
    for root, dirs, files in os.walk(PROJECT):
        dirs[:] = [d for d in dirs if d not in (".git", "target", "node_modules", "node", "tools")]
        for f in files:
            p = os.path.join(root, f)
            try:
                raw = open(p, "rb").read()
                if b"\0" in raw[:2048]:
                    continue
                text = raw.decode("utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            new = text
            for a, b in pairs:
                if a in new:
                    new = new.replace(a, b)
            if new != text:
                open(p, "w", encoding="utf-8", newline="").write(new)
                changed += 1
    print("references rewritten in %d files" % changed)

    # the list people read
    lines = ["# Images", "",
             "Every photo of the Weekender demo is from [Wikimedia Commons](https://commons.wikimedia.org), under a licence that lets",
             "anybody use it: public domain, CC0 or Creative Commons Attribution (CC BY). Each was scaled to 1920 pixels wide and",
             "saved again as a lighter JPEG; nothing else was changed. The same credit is in each file's metadata in Media.",
             "`tools/import_images.py` made this list.", "",
             "| File | Title on Commons | Author | Licence |", "|---|---|---|---|"]
    for new, m in sorted(manifest.items()):
        if m.get("commons"):
            licence = "[%s](%s)" % (m["licence"], m["licenceUrl"]) if m.get("licenceUrl") else m["licence"]
            lines.append("| `%s` | [%s](%s) | %s | %s |" % (new, m["title"].replace("|", "/"), m["page"], m["author"].replace("|", "/"), licence))
    site = os.path.join(HERE, "images-site.json")  # written by tools/brand.py
    if os.path.exists(site):
        for name, m in sorted(json.load(open(site)).items()):
            licence = "[%s](%s)" % (m["licence"], m["licenceUrl"]) if m.get("licenceUrl") else m["licence"]
            lines.append("| `/content/dam/weekender/en/site/%s` | [%s](%s) | %s | %s |" % (name, m["title"].replace("|", "/"), m["page"], m["author"].replace("|", "/"), licence))
    lines += ["", "Made for this project, free to use (CC0): the logo, the favicons and the pictures of the templates",
              "(`tools/brand.py` draws them), and:", ""]
    lines += ["- `%s`: %s" % (new, m["made"]) for new, m in sorted(manifest.items()) if m.get("made")]
    open(os.path.join(PROJECT, "IMAGES.md"), "w").write("\n".join(lines) + "\n")
    print("IMAGES.md: %d photos, %d made here" % (len([m for m in manifest.values() if m.get("commons")]), len([m for m in manifest.values() if m.get("made")])))


if __name__ == "__main__":
    main()
