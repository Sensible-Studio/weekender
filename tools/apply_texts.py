#!/usr/bin/env python3
"""Puts Weekender's own texts into the content packages.

Adobe's sample content came with Adobe's articles and teasers. Ours are in tools/texts:

  tools/texts/fragments/**/*.html   one content fragment each. The first lines are "key: value"
                                    (fragment: its path below /content/dam/weekender-shared, title:,
                                    and any other property of the fragment's master variation,
                                    "element: main" names the element the text goes to); after an
                                    empty line comes the HTML, one block per paragraph.
  tools/texts/strings.json          {"old text": "new text"} for short texts in pages and experience
                                    fragments (teasers, descriptions, quotes), in every copy of the site.

Run from the repository root: python3 tools/apply_texts.py [--check]. It says what it could not place.
"""
import glob
import html
import json
import os
import re
import sys

SHARED = "ui.content.shared/src/main/content/jcr_root/content/dam/weekender-shared"
ROOTS = ["ui.content.sample/src/main/content/jcr_root/content", "ui.content.shared/src/main/content/jcr_root/content"]
ATTR = re.compile(r'(\s)([\w:.-]+)="([^"]*)"')


def xml_attr(value):
    value = value.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;").replace("\r", "&#xd;").replace("\n", "&#xa;")
    return value


def xml_text(value):
    return html.unescape(value) if "&" in value else value


def tag_end(source, start):
    """Where the start tag that begins at `start` ends: a ">" outside the attribute values."""
    quoted = False
    for i in range(start, len(source)):
        if source[i] == '"':
            quoted = not quoted
        elif source[i] == ">" and not quoted:
            return i
    raise ValueError("no end of tag")


def set_attr(source, start, name, value):
    """Sets attribute `name` of the element that starts at `start`; adds nothing if it is missing."""
    end = tag_end(source, start)
    element = source[start:end]
    pattern = re.compile(r'(\s)%s="[^"]*"' % re.escape(name))
    if not pattern.search(element):
        return source, False
    element = pattern.sub(lambda m: '%s%s="%s"' % (m.group(1), name, xml_attr(value)), element, count=1)
    return source[:start] + element + source[end:], True


def blocks_of(markup):
    return re.findall(r"<(h[1-6]|p|ul|ol|blockquote)[ >]", markup)


def fragments(check):
    problems = 0
    for path in sorted(glob.glob("tools/texts/fragments/**/*.html", recursive=True)):
        head, _, body = open(path, encoding="utf-8").read().partition("\n\n")
        props = dict((k.strip(), v.strip()) for k, v in (line.split(":", 1) for line in head.splitlines() if ":" in line))
        element = props.pop("element", "main")
        target = os.path.join(SHARED, props.pop("fragment"), ".content.xml")
        markup = "\n".join(block.strip() for block in body.strip().split("\n\n"))
        source = open(target, encoding="utf-8").read()
        start = source.index("<master")
        old = re.search(r'\s%s="([^"]*)"' % re.escape(element), source[start:tag_end(source, start)])
        if old and blocks_of(xml_text(old.group(1))) != blocks_of(markup) and xml_text(old.group(1)) != markup:
            print("note  %s: blocks were %s, are %s" % (path, " ".join(blocks_of(xml_text(old.group(1)))), " ".join(blocks_of(markup))))
        new, ok = set_attr(source, start, element, markup)
        if not ok:
            print("MISSING element %s in %s" % (element, target))
            problems += 1
        for name, value in props.items():
            new, ok = set_attr(new, new.index("<master"), name, value)
            if not ok:
                print("MISSING property %s in %s" % (name, target))
                problems += 1
            if name == "title":
                new, _ = set_attr(new, new.index("<jcr:content"), "jcr:title", value)
        if new != source and not check:
            open(target, "w", encoding="utf-8").write(new)
    return problems


def strings(check):
    table = json.load(open("tools/texts/strings.json", encoding="utf-8"))
    used = dict.fromkeys(table, 0)
    for root in ROOTS:
        for folder, _, files in os.walk(root):
            for name in files:
                if not name.endswith(".xml"):
                    continue
                path = os.path.join(folder, name)
                source = open(path, encoding="utf-8").read()

                def swap(match):
                    value = xml_text(match.group(3))
                    changed = value
                    for old, new in table.items():
                        for form in (old, html.escape(old, quote=False), html.escape(old, quote=True)):
                            if form in changed:
                                markup = "<" in changed
                                changed = changed.replace(form, html.escape(new, quote=False) if markup else new)
                                used[old] += 1
                                break
                    if changed == value:
                        return match.group(0)
                    return '%s%s="%s"' % (match.group(1), match.group(2), xml_attr(changed))

                new = ATTR.sub(swap, source)
                if new != source and not check:
                    open(path, "w", encoding="utf-8").write(new)
    missing = [old for old, n in used.items() if not n]
    if missing:
        # A text that is in place already is not missing.
        everything = "".join(open(os.path.join(f, n), encoding="utf-8").read() for r in ROOTS for f, _, ns in os.walk(r) for n in ns if n.endswith(".xml"))
        everything = html.unescape(html.unescape(everything))
        missing = [old for old in missing if table[old] not in everything]
    for old in missing:
        print("NOT FOUND  %s" % old[:90])
    print("%d texts placed, %d not found" % (sum(1 for n in used.values() if n), len(missing)))
    return len(missing)


if __name__ == "__main__":
    check = "--check" in sys.argv
    sys.exit(1 if fragments(check) + strings(check) else 0)
