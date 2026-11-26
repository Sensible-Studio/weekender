# Notice

Weekender is a derivative of two projects by Adobe, both under the MIT licence (Copyright (c) 2020 Adobe):

- [adobe/aem-guides-wknd](https://github.com/adobe/aem-guides-wknd), the WKND reference site;
- [adobe/aem-guides-wknd-shared](https://github.com/adobe/aem-guides-wknd-shared), its shared content.

The licence text and the copyright notice are in [LICENSE](LICENSE) and in the headers of the files that came from those projects.

## Kept

The structure of the project and of the site, the components, the templates and their policies, the styles, the Sling Models, the content fragment models, and most of the text of the pages and fragments.

## Changed

- **The name.** WKND became Weekender in file contents, file names, repository paths (`/apps/weekender`, `/content/weekender`, `/conf/weekender`) and Java packages (`io.sensiblestudio.weekender`).
- **The two projects are one.** The shared content is the module `ui.content.shared`.
- **Every photo.** The originals were stock photos that may only be shown as part of Adobe's demo. They were replaced by photos from Wikimedia Commons under free licences; see [IMAGES.md](IMAGES.md). Renditions and thumbnails made from the old photos were removed. Portraits are drawn initials. The two PDF documents are one-page samples.
- **The logo, the favicons and the pictures of the templates** were drawn for this project.
- **Texts that spoke for Adobe's demo**: the footer and one answer of the FAQ.
- **Removed**: the "AI-powered search" page (it needs a service of Adobe's cloud), the sample user and group, the integration tests, the UI tests and the dispatcher configuration.
- **Node identifiers** are new, so that the site installs beside the one it started from.
- **The bundle's imports** accept a wider range of versions of two libraries (Jackson annotations, Commons Lang).
