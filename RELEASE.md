# Tactical Compass — Release Kit (v1.0.0)

Everything needed to publish Tactical Compass on GitHub, Modrinth and CurseForge. The project page text is [README.md](README.md); this file holds the per-platform metadata, changelog and checklist.

***

## At a Glance
| | |
| --- | --- |
| Name | Tactical Compass |
| Mod ID | `tacticalcompass` |
| Version | 1.0.0 |
| Minecraft | 1.20.1 |
| Loader | Forge 47.x (built on 47.4.28) |
| Java | 17 |
| Environment | Client **and** server (required on both) |
| Dependencies | None (Forge only) |
| Author | imNikos |
| License | All Rights Reserved (set in `gradle.properties` → `mod_license`) |
| Jar | `build/libs/tacticalcompass-1.0.0.jar` |
| Icon | `assets/icon.png` (512×512) |
| Banner | `assets/social-preview.png` (1280×640) |

## Short Summary
Use wherever a one-liner is needed (Modrinth summary, CurseForge summary, GitHub "About"):

> A flip-up military compass with LED time and heading readouts, linkable to communications relays. No GUIs — everything is on the model.

GitHub About (matches the style of the other repos):

> Forge 1.20.1 mod: a flip-up military compass with an LED clock and pop-up heading readout, plus comms relays the needle can lock onto. No GUIs.

***

## GitHub
**Repository name**: `Tactical-Compass`

**Default branch**: `master` (matches the other plugin repos)

**Topics**: `minecraft`, `minecraft-mod`, `forge`, `forge-mod`, `minecraft-forge`, `1-20-1`, `compass`, `military`, `java`

**Social preview**: Settings → General → Social preview → upload `assets/social-preview.png`.

**Release**
- Tag: `v1.0.0`
- Title: `Tactical Compass 1.0.0`
- Attach: `tacticalcompass-1.0.0.jar`
- Body: the changelog below.

**Repo contents to commit**: `src/`, `tools/`, `assets/`, `gradle/`, `build.gradle`, `settings.gradle`, `gradle.properties`, `gradlew`, `gradlew.bat`, `README.md`, `RELEASE.md`, `LICENSE`, `.gitignore`, `.gitattributes`. Do **not** commit `build/`, `run/` or `.gradle/` (already in `.gitignore`).

## Modrinth
**Project type**: Mod

**Summary**: use the short summary above.

**Description**: paste `README.md` (Modrinth renders the same Markdown; swap the relative image paths for uploaded gallery URLs).

**Categories**: Equipment, Utility, Decoration

**Additional categories**: Technology

**Environment**: Client side — Required · Server side — Required

**Loaders**: Forge

**Game versions**: 1.20.1

**Version**
- Version number: `1.0.0`
- Version title: `Tactical Compass 1.0.0`
- Release channel: Release
- File: `tacticalcompass-1.0.0.jar`
- Dependencies: none

**Icon**: `assets/icon.png`

**Gallery suggestions**: social preview banner; first-person raised view (heading + time readable); hold view; open relay with radar screen; the three colourways side by side; third-person holding the relay.

**Links**: Source → GitHub repo · Issues → GitHub issues · Discord → https://discord.gg/9xJgzNqEaJ

## CurseForge
**Project type**: Mc Mods

**Summary**: use the short summary above (CurseForge caps it at ~255 characters).

**Description**: paste `README.md` in the Markdown editor; re-upload images to CurseForge and update the image links.

**Main category**: Armor, Tools, and Weapons

**Additional categories**: Utility & QoL, Cosmetic, Technology

**Game version**: 1.20.1 · **Mod loader**: Forge · **Java**: 17

**File upload**
- Display name: `Tactical Compass 1.0.0`
- Release type: Release
- Changelog: the changelog below
- Relations: none

**Logo**: `assets/icon.png` (square, at least 400×400 — this one is 512×512)

***

## Changelog — 1.0.0
Initial release.

**Tactical Compass**
- Flip-up lensatic-style compass in Black/blue, Olive/red and Camo/green.
- Equip animation: the compass rises closed, then the lid flips up with a small overshoot and a click.
- Rotating dial card that always points to true north, with 5° ticks and 30° numbering.
- 8-segment LED clock on the inside of the lid (in-game 00:00 – 24:00, blinking colon, `--:--` in fixed-time dimensions).
- Hold right-click to raise it: comes in closer and bigger, the lid opens wide, the crosshair sits in the sight window and a pop-up module shows the heading (000° – 359°).
- Right-click a Communications Relay to link the needle to it (lodestone-style); right-click again to unlink. LINK lamp lights while linked, the needle spins when the relay is in another dimension, and the link clears if the relay is destroyed.
- Animations and the raised pose are visible to other players in multiplayer.

**Communications Relay**
- Rugged field case with an animated radar screen, keyboard, radio unit, toggle switches, connectors and blinking status LEDs in each colourway's LED colour.
- Placed facing the player and closed by default.
- Right-click (empty hand or any non-compass item) opens or closes it with an interruptible chest-style lid animation; the antenna folds inside when closed.
- Sneak + right-click never interacts with the case, so blocks can be placed against it.
- Emits a little light while open; waterloggable; mined with a pickaxe; drops itself.

**General**
- No GUIs, HUD overlays or chat messages — everything is rendered on the item and block models.
- Recipes: the compass is shaped (dye, iron, redstone around a vanilla compass) and the relay is shapeless (dye + compass + redstone torch + iron block). No dye or green dye gives Olive, black gives Black, brown gives Camo.
- Compasses and relays can be re-dyed in the crafting grid (not into their current colour); compasses keep their relay link.
- Dedicated creative tab.

***

## Pre-Release Checklist
- [x] License: MIT.
- [ ] Confirm the repo URL `github.com/imnotnikos/Tactical-Compass` (it is written into `mods.toml` as the display URL and issue tracker).
- [ ] `./gradlew build` and grab `build/libs/tacticalcompass-1.0.0.jar`.
- [ ] Test the jar outside the dev environment: a normal Forge 1.20.1 client profile, plus a dedicated server with two players.
- [ ] Take gallery screenshots (dev client screenshots land in `run/screenshots/`).
- [ ] Create the GitHub repo, push, set the social preview, publish the `v1.0.0` release.
- [ ] Create the Modrinth project, upload the version, submit for review.
- [ ] Create the CurseForge project, upload the file, submit for review.
- [ ] Post in Discord with the links.

## Known Limitations
- Forge 1.20.1 only (no Fabric/NeoForge build yet).
- A compass lying on the ground always shows a north-up dial (dropped items carry no facing).
- In item frames, the compass is displayed unfolded flat; the dial reading there is decorative.
