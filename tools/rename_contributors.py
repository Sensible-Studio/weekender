#!/usr/bin/env python3
"""Gives the contributors of the demo invented names.

Adobe's sample content names its contributors after real people. Weekender's articles are written
anew (tools/texts), so they may not carry those bylines: every name, path and drawn portrait is
renamed here. Run once from the repository root; running it again changes nothing.
"""
import os
import re

PEOPLE = [
    # old slugs, old names, new slug, new name
    (["ian-provo"], ["Ian Provo"], "tomas-berglund", "Tomas Berglund"),
    (["jacob-wester"], ["Jacob Wester"], "nils-aaberg", "Nils Aaberg"),
    (["jake-hammer", "alex-iby"], ["Jake Hammer", "Alex Iby"], "rafael-monteiro", "Rafael Monteiro"),
    (["justin-barr"], ["Justin Barr"], "dana-whitlow", "Dana Whitlow"),
    (["kumar-selveraj", "kumar-selvaraj"], ["Kumar Selveraj", "Kumar Selvaraj"], "arun-pillai", "Arun Pillai"),
    (["sofia-sj-berg", "sofia-sjoeberg", "ayo-ogunseinde"], ["Sofia Sjöberg", "Ayo Ogunseinde"], "elin-marklund", "Elin Marklund"),
    (["stacey-roswells"], ["Stacey Roswells"], "maya-ortega", "Maya Ortega"),
]
SKIP_DIRS = {".git", "target", "node_modules", "dist"}
BINARY = (".jpg", ".jpeg", ".png", ".pdf", ".zip", ".jar", ".mp4", ".webp", ".gif", ".woff", ".woff2", ".ttf", ".ico")
# The record of what Adobe's files were called stays as it is; only our own drawn portraits are renamed there.
RECORDS = {"IMAGES.md", "images.json", "images-site.json", "rejected.txt", "redo.txt"}


def replaced(text, record):
    for slugs, names, slug, name in PEOPLE:
        first, last = name.split(" ")
        for old in slugs:
            if record:
                text = text.replace(old + ".svg", slug + ".svg")
            else:
                text = text.replace(old, slug)
        if record:
            continue
        for old in names:
            old_first, old_last = old.split(" ")
            text = text.replace(old, name)
            text = re.sub(r'(firstName=")%s\w*(")' % re.escape(old_first), r"\g<1>%s\2" % first, text)
            text = re.sub(r'(lastName=")%s(")' % re.escape(old_last), r"\g<1>%s\2" % last, text)
    return text


def main():
    changed = 0
    for folder, dirs, files in os.walk(".", topdown=False):
        if any(part in SKIP_DIRS for part in folder.split(os.sep)):
            continue
        for name in files:
            path = os.path.join(folder, name)
            if name == "rename_contributors.py" or name.lower().endswith(BINARY):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except (UnicodeDecodeError, OSError):
                continue
            new = replaced(text, name in RECORDS)
            if name == "original" and new.lstrip().startswith("<svg") and "contributors" in folder:
                initials = None
                for _, _, slug, person in PEOPLE:
                    if "/%s.svg/" % slug in replaced(path, False) + "/":
                        initials = "".join(w[0] for w in person.split(" "))
                if initials:
                    new = re.sub(r">[A-Z]{1,2}</text>", ">%s</text>" % initials, new)
            if new != text:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
                changed += 1
        for name in files + dirs:
            new = replaced(name, False)
            if new != name:
                target = os.path.join(folder, new)
                if os.path.exists(target):
                    print("exists already, left alone:", os.path.join(folder, name))
                    continue
                os.rename(os.path.join(folder, name), target)
                changed += 1
    print(changed, "files and folders changed")


if __name__ == "__main__":
    main()
