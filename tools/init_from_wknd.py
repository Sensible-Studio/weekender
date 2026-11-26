#!/usr/bin/env python3
"""Makes the Weekender project from Adobe's WKND sources (MIT): copies the two repositories into one
folder and renames WKND to Weekender in file contents, file names and Java packages.
    python3 weekender_init.py <aem-guides-wknd> <aem-guides-wknd-shared> <target>
"""
import os, shutil, sys

site, shared, target = sys.argv[1:4]
if os.path.exists(target) and os.listdir(target) and not os.path.isdir(os.path.join(target, ".git")):
    sys.exit(target + " exists and is not empty")

SKIP_TOP = {".git", "it.tests", "ui.tests", "dispatcher", ".github", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md",
            "RELEASING.md", "README.md", "archetype.properties", ".circleci"}

def copy(src, dest, skip=()):
    os.makedirs(dest, exist_ok=True)
    for name in os.listdir(src):
        if name in skip or name == ".DS_Store":
            continue
        s, d = os.path.join(src, name), os.path.join(dest, name)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=shutil.ignore_patterns(".DS_Store", "target", "node_modules", "node", "dist"), dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

copy(site, target, SKIP_TOP)
copy(os.path.join(shared, "ui.content"), os.path.join(target, "ui.content.shared"))

RULES = [
    ("aem-guides-wknd-shared", "weekender-shared"),
    ("aem-guides-wknd", "weekender"),
    ("com.adobe.aem.guides.wknd", "io.sensiblestudio.weekender"),
    ("com/adobe/aem/guides/wknd", "io/sensiblestudio/weekender"),
    ("com.adobe.aem.guides", "io.sensiblestudio"),
    ("wknd-shared", "weekender-shared"),
    ("WKND", "Weekender"),
    ("Wknd", "Weekender"),
    ("wknd", "weekender"),
]

def rename_text(text):
    for a, b in RULES:
        text = text.replace(a, b)
    return text

changed = 0
for root, dirs, files in os.walk(target):
    dirs[:] = [d for d in dirs if d != ".git"]
    for f in files:
        if f == "LICENSE":
            continue
        p = os.path.join(root, f)
        try:
            raw = open(p, "rb").read()
            if b"\0" in raw[:4096]:
                continue
            text = raw.decode("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new = rename_text(text)
        if new != text:
            open(p, "w", encoding="utf-8", newline="").write(new)
            changed += 1

# names, deepest first
moved = 0
for root, dirs, files in os.walk(target, topdown=False):
    if ".git" in root.split(os.sep):
        continue
    for name in files + dirs:
        new = rename_text(name)
        if new != name:
            os.rename(os.path.join(root, name), os.path.join(root, new))
            moved += 1

# the Java package: com/adobe/aem/guides/weekender -> io/sensiblestudio/weekender
for root, dirs, files in os.walk(target):
    if root.endswith(os.path.join("com", "adobe", "aem", "guides")) and "weekender" in dirs:
        base = root[: -len(os.path.join("com", "adobe", "aem", "guides"))]
        dest = os.path.join(base, "io", "sensiblestudio")
        os.makedirs(dest, exist_ok=True)
        shutil.move(os.path.join(root, "weekender"), os.path.join(dest, "weekender"))
        for d in ("guides", "aem", "adobe", "com"):
            try:
                os.rmdir(os.path.join(base, *{"guides": ("com", "adobe", "aem", "guides"), "aem": ("com", "adobe", "aem"),
                                               "adobe": ("com", "adobe"), "com": ("com",)}[d]))
            except OSError:
                pass
        moved += 1
        dirs[:] = []

print("files changed: %d, names changed: %d" % (changed, moved))
