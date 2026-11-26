#!/usr/bin/env python3
"""Chooses other photos for the assets named in tools/redo.txt (one asset a line, as in
tools/images.json), after somebody looked at the contact sheets. The asset keeps its name, so
nothing that uses it changes. What was there is added to tools/rejected.txt and not chosen again.

    python3 tools/redo_images.py
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import import_images as images

# closer searches for the folders whose first choice went wrong
QUERIES = {
    "en/activities/climbing": ["climber on rock wall rope", "bouldering outdoor", "sport climbing limestone"],
    "en/activities/cycling": ["cyclist mountain pass road", "gravel cycling", "bicycle road Alps"],
    "en/activities/hiking": ["hikers trail Alps", "hiking Dolomites trail", "hiking trail ridge", "trekking path valley"],
    "en/activities/skiing": ["skier powder snow", "ski slope Alps", "freeride skiing", "skiing piste mountain"],
    "en/adventures/beervana-portland": ["beer flight tasting", "brewery fermentation tanks", "beer glasses bar"],
    "en/adventures/climbing-new-zealand": ["Castle Hill New Zealand", "Mount Cook Aoraki", "Wanaka New Zealand lake"],
    "en/adventures/cycling-tuscany": ["Chianti road vineyard", "Tuscany gravel road", "Crete Senesi"],
    "en/adventures/downhill-skiing-wyoming": ["Teton Range winter", "Jackson Hole Mountain Resort", "skiing powder Wyoming"],
    "en/adventures/gastronomic-marais-tour": ["Place des Vosges", "Rue des Rosiers", "Paris bistro terrace", "French pastries patisserie"],
    "en/adventures/napa-wine-tasting": ["Napa Valley winery", "wine barrels cellar", "Napa Valley vineyards autumn"],
    "en/adventures/riverside-camping-australia": ["Murray River campsite", "tent river bank", "Kakadu billabong", "Australia bush camping"],
    "en/adventures/ski-touring-mont-blanc": ["Mont Blanc from Chamonix", "Aiguille du Midi", "Vallee Blanche", "ski mountaineering glacier", "Mer de Glace"],
    "en/adventures/surf-camp-in-costa-rica": ["Tamarindo beach", "Santa Teresa beach Costa Rica", "Playa Hermosa Costa Rica", "Nosara beach", "Costa Rica surfer", "Manuel Antonio beach"],
    "en/adventures/tahoe-skiing": ["Heavenly Lake Tahoe ski", "Palisades Tahoe skiing", "Lake Tahoe snow winter"],
    "en/adventures/whistler-mountain-biking": ["Whistler Bike Park", "mountain biking trail British Columbia", "mountain biker downhill forest"],
    "en/magazine/fly-fishing-amazon": ["fly fishing", "angler casting river"],
    "en/magazine/la-skateparks": ["skateboarder skatepark", "Venice Skatepark", "skateboarding trick", "skate bowl concrete", "skateboard ramp"],
    "en/magazine/skitouring": ["ski touring skin track", "backcountry skiing", "ski tourers ascent"],
    "en/magazine/western-australia": ["Cape Le Grand National Park", "Kalbarri National Park", "Pinnacles Desert", "Cable Beach Broome", "Karijini gorge"],
}


def main():
    manifest = json.load(open(images.MANIFEST))
    redo = [l.strip() for l in open(os.path.join(HERE, "redo.txt")) if l.strip() and not l.startswith("#")]
    rejected_file = os.path.join(HERE, "rejected.txt")
    rejected = set(l.strip() for l in open(rejected_file)) if os.path.exists(rejected_file) else set()
    for key in redo:
        if key in manifest and manifest[key].get("commons"):
            rejected.add(manifest[key]["commons"])
    used = {m["commons"] for k, m in manifest.items() if m.get("commons")} | rejected
    cache = {}
    done = 0
    for key in redo:
        if key not in manifest:
            print("  ?? not in the list: " + key)
            continue
        folder, name = key.rsplit("/", 1)
        if folder not in cache:
            found = []
            for query in QUERIES.get(folder, []) + images.QUERIES.get(folder, []):
                found += images.search(query, used | {c["commons"] for c in found})
                time.sleep(1)
                if len(found) >= 12:
                    break
            cache[folder] = found
        choice = next((c for c in cache[folder] if c["commons"] not in used
                       and images.series(c["commons"]) not in {images.series(u) for u in used}), None)
        if not choice:
            print("  !! nothing better found for " + key)
            continue
        data = images.get(choice["download"], binary=True)
        time.sleep(1)
        if not data.startswith(b"\xff\xd8"):
            print("  !! not a JPEG: " + choice["commons"])
            used.add(choice["commons"])
            continue
        images.write_asset(folder, name, data, "image/jpeg", choice["title"], choice["author"], choice["licence"], choice["page"],
                           "%s. Photo: %s, %s, via Wikimedia Commons." % (choice["title"], choice["author"], choice["licence"]),
                           choice["width"], choice["height"])
        used.add(choice["commons"])
        manifest[key] = dict(choice, old=manifest[key]["old"])
        done += 1
        print("  %s <- %s (%s)" % (key, choice["commons"][:60], choice["licence"]), flush=True)
        json.dump(manifest, open(images.MANIFEST, "w"), indent=1, sort_keys=True)
    open(rejected_file, "w").write("\n".join(sorted(rejected)) + "\n")
    open(os.path.join(HERE, "redo.txt"), "w").write("# assets to choose again, one a line (as in images.json)\n")
    print("%d of %d chosen again" % (done, len(redo)))
    sys.argv = sys.argv[:1]
    images.main()  # the list people read


if __name__ == "__main__":
    main()
