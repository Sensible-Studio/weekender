#!/usr/bin/env python3
"""Puts Weekender's own texts into the content packages.

Adobe's sample content came with Adobe's articles and teasers. Ours are in tools/texts:

  tools/texts/fragments/**/*.html   one content fragment each. The first lines are "key: value"
                                    (fragment: its path below /content/dam/weekender-shared, title:,
                                    and any other property of the fragment's master variation; page:
                                    and summary: give the description of its page in every copy of the
                                    site). After an empty line comes the HTML of the element "main", one
                                    block per paragraph, or several elements, each after a line "== name".
                                    The text that pages keep of a fragment follows.
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
SAMPLE = "ui.content.sample/src/main/content/jcr_root/content"
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


def plain(markup):
    text = re.sub(r"<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def fragments(check):
    problems = 0
    placed = {}  # fragment path -> (title, {element: markup})
    for path in sorted(glob.glob("tools/texts/fragments/**/*.html", recursive=True)):
        head, _, body = open(path, encoding="utf-8").read().partition("\n\n")
        props = dict((k.strip(), v.strip()) for k, v in (line.split(":", 1) for line in head.splitlines() if ":" in line))
        fragment = props.pop("fragment")
        page, summary = props.pop("page", None), props.pop("summary", None)
        target = os.path.join(SHARED, fragment, ".content.xml")
        if body.lstrip().startswith("== "):
            elements = {}
            for part in re.split(r"(?m)^== ", body)[1:]:
                name, _, markup = part.partition("\n")
                elements[name.strip()] = markup
        else:
            elements = {props.pop("element", "main"): body}
        source = new = open(target, encoding="utf-8").read()
        for element, markup in elements.items():
            markup = "\n".join(block.strip() for block in markup.strip().split("\n\n"))
            elements[element] = markup
            start = new.index("<master")
            old = re.search(r'\s%s="([^"]*)"' % re.escape(element), new[start:tag_end(new, start)])
            if element == "main" and old and blocks_of(xml_text(old.group(1))) != blocks_of(markup):
                print("note  %s: blocks were %s, are %s" % (path, " ".join(blocks_of(xml_text(old.group(1)))), " ".join(blocks_of(markup))))
            new, ok = set_attr(new, start, element, markup)
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
        title = re.search(r'\stitle="([^"]*)"', new[new.index("<master"):tag_end(new, new.index("<master"))])
        placed["/content/dam/weekender-shared/" + fragment] = (xml_text(title.group(1)) if title else "", elements)
        if new != source and not check:
            open(target, "w", encoding="utf-8").write(new)
        if page and summary:
            for site in sorted(glob.glob(SAMPLE + "/weekender/*/en/" + page + "/.content.xml")):
                source = open(site, encoding="utf-8").read()
                new, ok = set_attr(source, source.index("<jcr:content"), "jcr:description", summary)
                if new != source and not check:
                    open(site, "w", encoding="utf-8").write(new)
    problems += cached(placed, check)
    return problems


def cached(placed, check):
    """The content fragment component keeps the text it shows in the page: that copy follows the fragment."""
    for folder, _, files in os.walk(SAMPLE):
        if ".content.xml" not in files:
            continue
        path = os.path.join(folder, ".content.xml")
        source = new = open(path, encoding="utf-8").read()
        at = 0
        while True:
            at = new.find("<", at)
            if at < 0:
                break
            if new.startswith("<!--", at):
                at = new.index("-->", at) + 3
                continue
            end = tag_end(new, at)
            tag = new[at:end]
            attrs = dict((k, xml_text(v)) for _, k, v in ATTR.findall(tag))
            fragment = placed.get(attrs.get("fragmentPath"))
            element = attrs.get("elementNames", "")
            if fragment and "contentfragment" in attrs.get("sling:resourceType", "") and element in fragment[1] and "text" in attrs:
                new, _ = set_attr(new, at, "text", (fragment[0] + " " + plain(fragment[1][element])).strip())
                end = tag_end(new, at)
            at = end + 1
        if new != source and not check:
            open(path, "w", encoding="utf-8").write(new)
    return 0


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
                            # Rich text has non-breaking and doubled spaces where the plain text has one.
                            loose = re.compile(r"(?:\s|&nbsp;|\xa0)+".join(re.escape(word) for word in form.split(" ")))
                            if loose.search(changed):
                                markup = "<" in changed
                                with_this = html.escape(new, quote=False) if markup else new
                                changed = loose.sub(lambda _: with_this, changed)
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
