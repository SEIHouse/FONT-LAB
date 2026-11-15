# App stress test: SEA and SEN screens

Open `site/app-stress/index.html` on the Font Lab site (or any local HTTP server from the
repository root). It sets real app screens with the four SEIHouse type roles at once, so
SEIHouse Noto is judged in its actual job: the face that is everywhere.

| Role | Face on this page | Job |
|---|---|---|
| Title Engine | Living Titles runtime on the SEIHouse Display cuts (Soft, Edge, Ink, Wide) | Album, novel and world titles; users will customise cut and motion |
| Elemental Title | `@seihouse/elemental-title` on a chosen base face (Noto, Sans or the title cut) | Artist, author, reader and character names |
| SEIHouse Noto | Redraw 02, with its Night grade in Night theme | Navigation, track and chapter lists, metadata, numbers, buttons, settings |
| SEIHouse Sans | Sans 0.43, with its Night grade in Night theme | Reading text: chapters, lyrics, synopses, lore |
| Future serif | A stand-in (Georgia), clearly labelled | Editorial: liner notes, editor's notes |

Two views, the same type system:

- **SEA** (`#sea`): album, now playing with lyrics, artist page, search and library.
- **SEN** (`#sen`): novel page, a chapter with comments, the novel's world guide, profile and settings.

Below each view, the **SEIHouse Noto close-up** checks a size ladder (10–18 px), labels and
buttons, numbers in their real jobs, names in many scripts (characters SEIHouse Noto does not
draw yet are highlighted, read live from `noto/studies/redraw/manifest.json`), how the faces
sit together on one line, and truncation in tight widths.

Controls: Day/Night, text size (85–130%), phone width (360/390/430), title cut and motion,
name element, rarity and base face, an *Everywhere face* switch to compare against Google
Noto Sans or the system UI font, and *Show roles*, which outlines every piece of text in its
role's colour. Settings are remembered in this browser only.

All content is fictional. Rebuild after editing `src/`:

```sh
(cd display && npm ci)
node site/build_app_stress.mjs
```
