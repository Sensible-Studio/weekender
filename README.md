# Weekender

The demo site of [Sensible Studio](https://github.com/Sensible-Studio/sensible-studio): a fictitious travel and adventure magazine with a home page, articles, adventures, a FAQ and an "about us" page, in several countries and languages.

It is an ordinary project in the format of Adobe Experience Manager: an OSGi bundle with Sling Models, components that extend the Core Components, editable templates and policies, client libraries built with webpack, content fragments with their models, experience fragments and content packages. The same package installs on AEM and on Sensible Studio. That is the point of it.

Weekender started from Adobe's [WKND reference site](https://github.com/adobe/aem-guides-wknd) and its [shared content](https://github.com/adobe/aem-guides-wknd-shared), both published under the MIT licence. See [NOTICE.md](NOTICE.md) for what was kept and what was changed.

## Install it

On Sensible Studio, from a release:

```
bin/studio setup --demo
bin/studio start
```

then open `http://localhost:4502/content/weekender/us/en.html`.

By hand: download `weekender.all-<version>.zip` from this repository's releases and put it in the instance's `install` folder, together with the three content packages inside it (`jcr_root/apps/weekender-packages/content/install` and `jcr_root/apps/weekender-vendor-packages/content/install`): the installer does not unpack a package from inside another.

## Build it

You need Java 21, Maven 3.9 and the internet (Node.js is downloaded by the build).

```
mvn clean install
```

The result is `all/target/weekender.all-<version>.zip`.

| Module | What it is |
|---|---|
| `core` | The OSGi bundle: Sling Models and services |
| `ui.apps` | Components, templates' code, client libraries (`/apps/weekender`) |
| `ui.frontend` | The CSS and JavaScript sources, built with webpack into a client library |
| `ui.config` | OSGi configuration |
| `ui.content` | Templates, policies and the base of the site (`/conf/weekender`, `/content/weekender`) |
| `ui.content.shared` | Media, content fragments, their models, tags and GraphQL queries (`/content/dam/weekender-shared`, `/conf/weekender-shared`) |
| `ui.content.sample` | The pages of the site |
| `all` | Everything in one package |

## The photos

Every photo is from [Wikimedia Commons](https://commons.wikimedia.org), under a licence that lets anybody use it: public domain, CC0 or Creative Commons Attribution. [IMAGES.md](IMAGES.md) lists each one with its author, licence and source; the same credit is in each file's metadata in Media. The portraits of the contributors are drawn initials, not photos of people.

`tools/` has the scripts that did it, so it can be done again or checked:

| Script | What it does |
|---|---|
| `init_from_wknd.py` | Makes this project from the two WKND repositories: copies them into one and renames everything |
| `import_images.py` | Replaces every photo of the shared media with a freely licensed one and writes `IMAGES.md` |
| `redo_images.py` | Chooses other photos for the assets listed in `tools/redo.txt`, after a look at the contact sheets |
| `contact_sheet.py` | Puts all photos on a few sheets, to look them over |
| `brand.py` | Draws the logo, the favicons and the pictures of the templates |

## Licence

MIT. See [LICENSE](LICENSE). The photos keep their own licences, listed in [IMAGES.md](IMAGES.md).

Weekender is not affiliated with, endorsed by or sponsored by Adobe. Adobe, Adobe Experience Manager and AEM are trademarks of Adobe Inc.
