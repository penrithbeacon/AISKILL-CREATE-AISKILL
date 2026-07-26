# Create AI Skill Package

**AI Skill UUID:** `a1805527-85e9-4002-9ab3-770084e9b45c`
**Package ID:** `com.openaiskillpackage.create-aiskill`
**Version:** 2.5.2
**Type:** procedural
**Author:** Anthony Harrison
**Author Email:** widgets@penrithbeacon.com
**License:** MIT
**Homepage:** https://penrithbeacon.com/
**Tags:** scaffold, create, aiskill, package, generator, meta

Scaffolds a new, originally-authored .aiskill package (Track A), or converts an existing skill from a foreign Agent Skills repo into one or more .aiskill packages with per-skill license gating (Track B).

Create AI Skill Package is the meta-skill that produces every other .aiskill
package in this ecosystem. It has two tracks: scaffold a brand-new,
originally-authored package from a plain-language description of what it
should do (Track A), or convert an existing skill already built to the open
Agent Skills format -- SKILL.md with YAML frontmatter, as used by Claude
Code, Cursor, and others -- into one or more .aiskill packages, carrying
forward the original license and provenance rather than re-authoring it
from scratch (Track B).

Reach for Track A whenever a procedure is worth turning into a verified,
versioned, unit-tested package instead of a prompt kept in a notes file --
something you or a team will run repeatedly and want to trust. Reach for
Track B when a skill already exists for a different AI agent format and
you want it brought into this ecosystem's stronger verification model:
mandatory unit testing, checksummed integrity, and a registry-based
external verification check that neither the Agent Skills format nor most
other skill formats provide on their own.

This is the one .aiskill package that was not itself produced by another
.aiskill package -- every package that exists or will exist in this
ecosystem was scaffolded or converted using this one. It ships with a full
unit test suite covering both tracks' naming conventions, per-skill license
classification, and the automatic assets/-prefixed path rewriting that
conversion depends on, and every package it produces carries SYSTEM.md's
external verification protocol from the moment it's created.

---

## Capabilities

- `filesystem.read`
- `filesystem.write`
- `process.exec`
- `network.fetch`

## Permissions

- **`filesystem.write`** — paths: `<aiskills_root>/AISKILL-*`
- **`network.fetch`** — hosts: `github.com`

---

*Generated deterministically by `build_card.py`, part of the **AISKILL-CREATE-AISKILL** skill,
from this package's own `manifest.yaml` — do not hand-edit. Re-run `build_card.py` after any
`manifest.yaml` change, before packaging.*
