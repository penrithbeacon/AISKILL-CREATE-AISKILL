# Create AI Skill Package

**AI Skill UUID:** `a1805527-85e9-4002-9ab3-770084e9b45c`
**Package ID:** `com.openaiskillpackage.create-aiskill`
**Version:** 2.5.0
**Type:** procedural
**Author:** Anthony Harrison
**Author Email:** widgets@penrithbeacon.com
**License:** MIT
**Homepage:** https://penrithbeacon.com/
**Tags:** scaffold, create, aiskill, package, generator, meta

Scaffolds a new, originally-authored .aiskill package (Track A), or converts an existing skill from a foreign Agent Skills repo into one or more .aiskill packages with per-skill license gating (Track B).

---

## Synopsis

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

## How It Works (Behavior)

This is the skill that creates skills. Each one lives as a single file with a `.aiskill` extension — a ZIP archive at its core, small enough to share in a message, complete enough to stand alone. Before diving into what it does, it's worth taking a moment to understand the world it belongs to, because that context is what makes this particular package so significant.

Create AI Skill Package is the meta-skill that produces every other `.aiskill` package in this ecosystem. It has two tracks: scaffold a brand-new, originally-authored package from a plain-language description of what it should do (Track A), or convert an existing skill already built to the open Agent Skills format — `SKILL.md` with YAML frontmatter, as used by Claude Code, Cursor, and others — into one or more `.aiskill` packages, carrying forward the original license and provenance rather than re-authoring it from scratch (Track B).

Reach for Track A whenever a procedure is worth turning into a verified, versioned, unit-tested package instead of a prompt kept in a notes file — something you or a team will run repeatedly and want to trust. Reach for Track B when a skill already exists for a different AI agent format and you want it brought into this ecosystem's stronger verification model: mandatory unit testing, checksummed integrity, and a registry-based external verification check that neither the Agent Skills format nor most other skill formats provide on their own.

This is the one `.aiskill` package that was not itself produced by another `.aiskill` package — every package that exists or will exist in this ecosystem was scaffolded or converted using this one. It ships with a full unit test suite covering both tracks' naming conventions, per-skill license classification, and the automatic `assets/`-prefixed path rewriting that conversion depends on, and every package it produces carries `SYSTEM.md`'s external verification protocol from the moment it's created.

When you run it, the agent asks whether you're building something new or bringing in a skill that already exists elsewhere, gathers what it needs in plain conversation, and hands you back a complete, versioned, tested `.aiskill` package — see **This Skill in Particular** below for the full walkthrough of either path.

---

## What's in this .aiskill package?

```
CREATE-AISKILL-2.5.0.aiskill  (ZIP archive)
├── manifest.yaml          # identity & metadata
├── SYSTEM.md               # verification protocol (invariant)
├── SKILL.md               # AI entry point — execution instructions
├── CARD.md                # human-facing summary, generated from manifest.yaml
├── README.md              # this file — byte-identical to the repo-root copy
├── CHANGELOG.md           # version history
├── LICENSE.txt            # MIT license text
├── checksums.yaml         # SHA-256 integrity hashes
├── assets/
│   ├── scripts/
│   │   ├── scaffold.py    # Track A — builds a new package from scratch
│   │   ├── convert.py     # Track B — converts an existing Agent Skills-format skill
│   │   ├── pack.py        # zips a finished skill/ directory into a .aiskill archive
│   │   └── build_card.py  # deterministically generates CARD.md from manifest.yaml
│   ├── templates/          # manifest.yaml/README.md/CHANGELOG.md/SYSTEM.md templates
│   │                        # scaffold.py and convert.py render into a new package
│   └── tests/              # unit tests covering both tracks
└── inputs/
    └── schema.json         # input schema for this skill's own runtime inputs
```

A package with no `assets/`/`inputs/` at all — nothing to run, nothing to test, nothing
bundled — is instead built and distributed as a `.mdskill` package, a lighter sibling format
for skills that are inert by nature. This one has real scripts and tests, so it's a full
`.aiskill` package.

---

## The AI Skill Universe

Most people are already familiar with the idea of giving an AI agent a set of instructions — a prompt that tells it what to do and how to behave. When someone refines a prompt they find themselves using repeatedly — saves it to a text file or a notebook so they can reach for it again whenever that same task comes up — that saved, reusable piece of text is called an **AI skill**. It is just text. Nothing more. But it is text that has been thought through, kept, and given a purpose.

An **AI Skill Package** is something different.

Where a simple AI skill is just text — a prompt saved to a file and pasted in whenever that task is needed — an AI Skill Package is a structured, versioned, unit-tested artifact that has been built, verified, and packaged in advance. It contains not just instructions, but scripts, templates, tests, and a manifest that identifies exactly what it is and what version it is. It has been checked, and it checks itself.

The key insight is this: **the AI becomes the executor, not the author.**

When an agent receives an AI Skill Package, the thinking has already been done. The procedure has already been written, tested, and verified by whoever built the package. The agent's job is simply to open it, read the entry point, follow the steps, and ask the user for anything it still needs. The output is reliable in a specific sense: the procedure is fixed and has already been tested, not regenerated from scratch each time. For a skill whose work is a computation — a script that computes a result — the same inputs produce the same result every time, on any agent. For a skill whose work is inherently generative (writing prose, designing something original), the procedure is still fixed and tested, even though the creative output naturally varies — the same way a photographer's process is repeatable even though no two photos are identical.

This is what separates an AI Skill Package from a prompt: reliability, repeatability, and trust.

---

## How People Use AI Skill Packages

You don't need to be a developer to use an AI Skill Package. You don't need to know what a manifest is, or what a unit test does, or how a ZIP archive is structured.

What you need is an idea — and a way to express it.

You open your AI agent (Claude Code, or any compatible runtime), and you say something like:

> _"Use the skill at /path/to/skill-name.aiskill to do this for me."_

You can type that, or you can press record and say it out loud. The agent reads the package, figures out what it needs to know, and asks you questions until it has enough to proceed. If your initial prompt already answered those questions, it gets straight to work.

No commands. No configuration files. No prior knowledge required.

---

## This Skill in Particular

CREATE-AISKILL is the origin point. It is the one AI Skill Package that was not itself created by an AI Skill Package — and from which every other AI Skill Package can be made.

When you run CREATE-AISKILL, it first asks whether you're building something new or bringing in a skill that already exists elsewhere.

If you're building something new, the agent asks about the skill you want to build: what it should do, who it's for, what kind of output it produces. You answer in plain language. The agent does the rest — creating the complete package structure, setting up version control, and leaving you with everything in place to start describing your skill's procedure.

If you're converting an existing skill — one built to the [Agent Skills specification](https://agentskills.io/specification), for example — the agent asks which repo and which skill (or skills), resolves each skill's own license before touching anything, and never carries forward a proprietary or ambiguous license without asking you directly first.

The result is your own AI Skill Package: structured, versioned, and ready to run. Something you can keep for personal use, share with a team, or publish publicly so that others can download, inspect, and trust it. Either way, the result is the same kind of package — checked, versioned, and ready to trust — whether it started as your own idea or as someone else's skill built for a different system.

If you have an idea for something an AI agent should be able to do repeatedly and reliably — this is where that idea becomes a package.

---

> ### AI Independence Day — 4 July 2026
>
> CREATE-AISKILL was first published on 4 July 2026, the date we mark as **AI Independence Day**.
>
> Packaging a procedure so an agent executes it rather than generates it isn't new on its own — function calling and the Model Context Protocol already let an agent invoke deterministic tools instead of reasoning its way through the computation each time. What AI Independence Day marks is narrower and, we think, more consequential: the moment an agent stopped being the sole judge of whether what it's about to run can be trusted.
>
> Every AI Skill Package carries `SYSTEM.md`, an invariant protocol the agent must follow before it executes anything else inside the package. It requires the agent to check the package against an independent registry — not the package's own bundled claims about itself — and to stop, unconditionally, if that check fails or can't be completed, even when running unattended. The agent no longer decides for itself whether to trust a skill. It follows a governance process it did not write and cannot skip.
>
> CREATE-AISKILL is the package that made every other package possible. It is the origin of that independence. Released on the 4th of July, not by coincidence.

---

## Prerequisites

If you are new to AI Skill Packages, you can ignore this section entirely and skip straight to Quick Start below. Nothing here needs installing by hand — your AI agent works out what a particular skill actually needs and asks your permission before installing anything that isn't already there. This section exists for the curious.

- **git** — every AI Skill Package is also an ordinary source-controlled repository under the hood. Source control keeps a permanent, ordered history of every change ever made — who changed what, and when — so nothing is ever silently lost or overwritten, and any earlier version can always be recovered. It's the same tool almost all software in the world is built with. Your agent uses it automatically; you'll never need to type a git command yourself.
- **The `gh` command-line tool** — *optional*. git can push code to a repository that already exists, but creating a new GitHub repository, or publishing a finished version as a GitHub Release, aren't git actions at all — they're GitHub-platform features. `gh` is how your agent does those two things without you needing to click through GitHub's website by hand. Decline it and do those two steps yourself in your browser instead — everything else works exactly the same either way.
- **Your own GitHub account** — needed only if you want to publish your skill so others can find, register, and download it. This isn't a requirement of the `.aiskill` format itself — it's a requirement of the [Cup and Ring Registry](https://cupandringregistry.com), the registry this ecosystem uses to list and verify published skills. The registry deliberately ties every published skill to a real GitHub account: that's what makes whoever published a skill accountable for it, and what proves a real connection between a specific skill and a specific person, rather than an anonymous upload. If you don't have one, accounts are free at [github.com/signup](https://github.com/signup) — an email address and a username is all it takes.

---

## Quick Start

Give your AI agent this prompt — nothing more is needed to begin:

> _Run the Skill Package at /path/to/CREATE-AISKILL-2.5.0.aiskill_

That is the complete minimal prompt. The agent opens the package, reads its entry point, and starts a conversation with you to gather what it needs. It will typically ask:

- What do you want to call your skill?
- What should it do — describe it in your own words
- Who is it for, and what will they give it as input?
- Do you want to connect it to a GitHub repository so others can find and trust it? (You can say no — a local-only skill works just as well)
- Your name and contact email, so the package can be properly attributed

You can answer in any order and in any amount of detail. If your opening prompt already covered some of these, the agent skips straight past them. If you'd rather talk than type, press record and describe your idea out loud — the agent will work with whatever it receives.

**A fuller prompt — for illustration:**

> _Run the Skill Package at /path/to/CREATE-AISKILL-2.5.0.aiskill — I want to create a skill that helps a home cook plan a week of dinners based on what's in season and any dietary restrictions in the household._

With a prompt like that, the agent already knows the name, the purpose, and the audience. It may only need to ask one or two follow-up questions before it gets to work.

**Converting a skill from the Agent Skills format:**

> _Run the Skill Package at /path/to/CREATE-AISKILL-2.5.0.aiskill — I found a skill built to the [Agent Skills specification](https://agentskills.io/specification) that I'd like turned into a proper [AI Skill Package](https://openaiskillpackage.com/)._

The agent will ask which skill (or skills) you mean, check what license the original was released under, and only proceed on anything unclear or restricted once you've confirmed you're allowed to.

---

## Under the Bonnet

Think of buying a car. You want to sit in it, feel comfortable, and go touring. How much you need to know about the engine is entirely up to you — most drivers never lift the bonnet, and they never need to. This section is the bonnet. Read on if you're curious; skip ahead to the specification link if you're not.

When CREATE-AISKILL finishes, it has produced a directory containing everything a skill package needs:

- A **manifest** — the identity card: name, version, unique ID, author, licence
- A **SKILL.md** — the entry point the AI agent reads first; this is where the procedure lives
- **Scripts** — executable files (Python, or whatever language fits the task) that do the actual work
- **Templates** — reusable file skeletons the scripts can stamp out
- **Tests** — unit tests that verify the scripts behave correctly before the package is shipped
- **Checksums** — a record of every file's fingerprint, so anyone can verify the package hasn't been tampered with
- **A schema** — a formal definition of what inputs the skill accepts
- **A changelog and README** — so humans know what it does and what has changed

Once all of those are in place, turning that folder into an AI Skill Package takes exactly two steps: zip it up, and rename the file extension from `.zip` to `.aiskill`. That is all the format is — a ZIP with a name that says what it contains.

When an agent receives an `.aiskill` file, it reverses that process: unpacks the archive into a temporary working area, opens `SKILL.md`, and follows the instructions inside like a flowchart. Each branch either continues the task or returns to the user with a question. Eventually every branch leads to the same place — the completed output the skill was built to produce.

If you're converting a skill built to the [Agent Skills specification](https://agentskills.io/specification) — the format used by tools like Claude Code's own skills, among others — into this [AI Skill Package specification](https://openaiskillpackage.com/), you get more than a straight conversion. The result still runs on the same AI agents, but gains capabilities the original format doesn't have: built-in unit tests, a verifiable record of exactly where it came from, and a security model — checksums, license tracking, and registry-based verification — built to catch tampering or license problems before anyone downstream runs the skill.

**Converting an existing skill works differently under the bonnet.** Instead of starting from an empty folder, CREATE-AISKILL fetches the skill you pointed it at and works through it:

1. **Finds the license.** It looks for a license file in the skill's own folder first, then falls back to the one covering the whole repository, then treats "genuinely couldn't find one" as its own case rather than assuming the best.
2. **Sorts skills into three groups** based on that license — clearly open, unclear, or restrictive. A clearly open license (like MIT or Apache) needs no further input from you. Anything else stops the process and asks you to confirm you're allowed to proceed, and permanently records that confirmation, with your name attached, inside the finished package.
3. **Rebuilds the file layout to match the AI Skill Package structure**, and — this is the detail that's easy to get wrong by hand — rewrites every internal reference to a moved file, so a line like "see `references/pricing.md`" still points somewhere real once that file has been relocated into its new home.
4. **Names the result consistently**, so a converted package is recognisable as both an AI Skill Package *and* a conversion, and so the account it came from and the repository it came from are never ambiguous.
5. **Records where it came from**, permanently, inside the package: the original repository, the exact file path within it, the date of conversion, and — if your confirmation was needed — your name and what you approved.

When you're converting a whole repository at once, the skills with a clearly open license are finished immediately; anything needing your confirmation is set aside and handled with you afterward, so a few unclear cases never hold up the rest.

The parts that make an AI Skill Package trustworthy — the manifest, the checksums, the invariant `SYSTEM.md` verification protocol described above — are added the same way regardless of whether the package was built from scratch or converted. Only `capabilities` and `permissions` are always left for a human to fill in afterward: no format this tool has been checked against declares anything CREATE-AISKILL could read those off automatically, for a package built from scratch or converted from elsewhere.

---

## On Public Distribution

For personal or internal use, a local-only skill works just as well — no GitHub account, no repository, no configuration. The skill lives on your machine and runs when you point an agent at it.

If you intend to share your skill publicly, a public repository is strongly recommended — not for convenience, but for trust. When users can read the source, they can verify the package does what it says and nothing it shouldn't. The open `.aiskill` format exists precisely so that inspection is always possible.

This matters even more for a converted skill: the Origin section and license confirmation CREATE-AISKILL adds aren't just internal bookkeeping — they're exactly what a stranger needs to see, before trusting a package that didn't originate with you, to know it's being redistributed properly.

---

## Specification

The full Open AI Skill Package specification is at [openaiskillpackage.com](https://openaiskillpackage.com/). If you're converting a skill, the format it's converting *from* — the Agent Skills specification — is at [agentskills.io/specification](https://agentskills.io/specification).

---

## License

MIT

**Author:** Anthony Harrison — widgets@penrithbeacon.com
