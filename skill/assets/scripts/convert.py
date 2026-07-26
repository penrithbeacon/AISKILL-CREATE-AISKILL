#!/usr/bin/env python3
"""
convert.py — CREATE-AISKILL v2.4.0
Converts an existing skill (or several) from a foreign "Agent Skills" format repo
(agentskills.io) into one or more AISKILL-{origin}-{SLUG} repository structures
(Track B). For scaffolding a brand-new, originally-authored package, see
scaffold.py (Track A) instead.

Discovery modes:
  --source-path <path>              single skill
  --skills <path1,path2,...>        cherry-picked list
  (neither given)                   batch — every directory under the repo
                                     containing a SKILL.md is discovered

License handling is deliberately NOT fully automated: this script classifies a
*provisional* tier per skill (see classify_license_tier) and always surfaces the
actual license text as evidence — the AI/user reviews it, tier 2/3 skills always
require a human attestation before they're finalized (see --attestation-for).
capabilities/permissions are never inferred either; every generated manifest.yaml
leaves them as an explicit placeholder for the AI to author by hand.

Processing order for batch/cherry-pick runs: every tier-1 (clean license) skill is
generated and committed immediately, in one pass, with no interruption. Every
tier-2/3 skill is generated with PENDING attestation placeholders and left
uncommitted, collected into a deferred list printed at the end — resolve each with
a separate --attestation-for call once the user has decided.

Ends at a local commit only. Never creates a GitHub repo, never pushes — review
with the user before either of those, same discipline as every converted package
shipped so far.
"""

from __future__ import annotations  # keeps `str | None` annotations valid on Python 3.8/3.9

import argparse
import re
import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ── Conventions ──────────────────────────────────────────────────────────────

REPO_PREFIX = "AISKILL"
HOMEPAGE = "https://penrithbeacon.com/"
MINIMUM_RUNTIME = "1.0.0"
DEFAULT_VERSION = "1.0.0"
SYSTEM_PROTOCOL_VERSION = "1.0.0"
AISKILL_SPEC_VERSION = "v2.3.0"
ATTESTATION_PENDING = "PENDING"
SYNOPSIS_PLACEHOLDER = (
    "TODO: author a synopsis by hand before packaging -- never auto-extracted from "
    "source content. Recommended structure: what it does, when to reach for it, and "
    "why to trust this package (see the .aiskill spec's synopsis field). When "
    "converting a batch or cherry-picked list, every skill gets this same placeholder "
    "-- write each one's real synopsis afterward, same as capabilities/permissions."
)

# Source-format directory name -> .aiskill destination. "evals" is deliberately
# absent -- excluded from the package entirely (authoring-time aid only, per the
# v2.1.0 spec's evals rule), left as a local, unpackaged reference.
DIR_MAP = {
    "scripts": "assets/scripts",
    "references": "assets/references",
    "examples": "assets/references",
    "templates": "assets/templates",
    "assets": "assets/templates",
}

LICENSE_FILENAMES = ["LICENSE.txt", "LICENSE", "LICENSE.md"]


# ── Slug / naming helpers (mirrors scaffold.py + the v2.2.1 spec rule) ───────

def slug_from_path(source_path: str) -> str:
    """'01-model-architecture/nanogpt' -> 'NANOGPT'; 'skills/seo-audit' -> 'SEO-AUDIT'"""
    basename = source_path.rstrip("/").split("/")[-1]
    cleaned = re.sub(r"[^A-Za-z0-9\s-]", "", basename)
    return re.sub(r"[\s_-]+", "-", cleaned).strip("-").upper()


def origin_segment(source_owner: str, source_repo: str) -> str:
    """Always lowercase, regardless of actual GitHub casing -- v2.2.1 spec rule,
    keeps the boundary with the UPPER-KEBAB-CASE slug unambiguous."""
    return f"{source_owner}_{source_repo}".lower()


def repo_name_from_origin_and_slug(origin: str, slug: str) -> str:
    return f"{REPO_PREFIX}-{origin}-{slug}"


def id_from_dest_and_slug(dest_account: str, source_repo: str, slug: str) -> str:
    return f"com.{dest_account.lower()}.{source_repo.lower()}.{slug.lower()}"


def tags_from_slug(slug: str) -> list:
    return [w.lower() for w in slug.split("-")]


def capabilities_to_yaml_list(capabilities_str: str) -> str:
    caps = [c.strip() for c in capabilities_str.split(",") if c.strip()]
    if not caps:
        return "  []  # TODO: author capabilities by hand -- never auto-inferred"
    return "\n".join(f"  - {c}" for c in caps)


def tags_to_yaml_inline(tags: list) -> str:
    return "[" + ", ".join(tags) + "]"


def synopsis_to_yaml_block(synopsis: str) -> str:
    """Indents a multi-paragraph synopsis two spaces per line, for embedding
    under manifest.yaml's `synopsis: |` block scalar."""
    lines = synopsis.strip("\n").split("\n")
    return "\n".join(f"  {line}" if line else "" for line in lines)


def yaml_quote(value: str) -> str:
    """Returns value as a YAML-safe double-quoted scalar. manifest.yaml.converted
    .template substitutes NAME/DESCRIPTION as bare, unquoted scalars (`name:
    <<<NAME>>>`) -- a source skill whose title contains a colon (e.g.
    "TransformerLens: Mechanistic Interpretability for Transformers") breaks that
    plain substitution, since YAML reads "X: Y" as a nested mapping key/value
    rather than plain text. Caught converting transformer-lens, whose real title
    is exactly that shape."""
    return yaml.dump(value, default_style='"', width=float("inf")).strip()


def substitute(template: str, tokens: dict) -> str:
    result = template
    for key, value in tokens.items():
        result = result.replace(f"<<<{key}>>>", str(value))
    return result


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"    wrote  {path}")


def run(cmd: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


# ── Source repo fetch ─────────────────────────────────────────────────────────

def clone_source_repo(source_repo: str, scratch_dir: Path) -> Path:
    """git clone --depth 1 a public repo -- no token needed for the read side,
    matches exactly how Phase B's source content was pulled by hand."""
    dest = scratch_dir / source_repo.replace("/", "__")
    if dest.exists():
        print(f"  (using existing clone at {dest})")
        return dest
    url = f"https://github.com/{source_repo}.git"
    print(f"  cloning {url} ...")
    result = run(["git", "clone", "--depth", "1", url, str(dest)], cwd=scratch_dir)
    if result.returncode != 0:
        print(f"Error: git clone failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return dest


def discover_skills(repo_dir: Path, source_path: str | None, skills_list: str | None) -> list:
    """Returns a list of source_path strings, relative to repo_dir, each naming a
    directory containing a SKILL.md."""
    if source_path:
        candidate = repo_dir / source_path / "SKILL.md"
        if not candidate.exists():
            print(f"Error: no SKILL.md found at {source_path}", file=sys.stderr)
            sys.exit(1)
        return [source_path]

    if skills_list:
        paths = [p.strip() for p in skills_list.split(",") if p.strip()]
        for p in paths:
            if not (repo_dir / p / "SKILL.md").exists():
                print(f"Error: no SKILL.md found at {p}", file=sys.stderr)
                sys.exit(1)
        return paths

    # Batch: every directory containing a SKILL.md, path relative to repo_dir
    found = []
    for skill_md in sorted(repo_dir.rglob("SKILL.md")):
        if ".git" in skill_md.parts:
            continue
        found.append(str(skill_md.parent.relative_to(repo_dir)))
    return found


# ── Frontmatter parsing ───────────────────────────────────────────────────────

def parse_skill_md(skill_md_path: Path) -> tuple:
    """Splits SKILL.md into (frontmatter_dict, body_text). Agent Skills format:
    --- YAML --- followed by markdown body."""
    text = skill_md_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        # No frontmatter at all -- treat the whole file as body, empty frontmatter
        return {}, text.strip() + "\n"
    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return frontmatter, body


def humanize_slug(slug: str) -> str:
    """'seo-audit' -> 'Seo Audit' -- a reasonable default, not a guaranteed-correct
    one (acronyms like SEO won't get their real casing back). Flagged in SKILL.md
    Track B for the AI to sanity-check/fix, same spirit as capabilities/tags."""
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", slug) if w)


def derive_name(body: str, frontmatter: dict, source_path: str) -> str:
    """Prefers the source SKILL.md's own first H1 heading (human-authored prose,
    e.g. 'nanoGPT - Minimalist GPT Training') over frontmatter's machine slug
    ('nanogpt') or the raw path basename -- confirmed against a real shipped
    package (seo-audit) that the H1 is consistently the better name."""
    first_line = body.lstrip().split("\n", 1)[0].strip()
    match = re.match(r"^#\s+(.+)$", first_line)
    if match:
        return match.group(1).strip()
    if frontmatter.get("name"):
        return humanize_slug(frontmatter["name"])
    return humanize_slug(source_path.split("/")[-1])


# ── License resolution + provisional tier classification ────────────────────
# Deliberately provisional -- always returned with the actual evidence text so
# the AI/user can sanity-check it, never silently trusted, per the standing rule
# that even tier-1 classification can be wrong on an unusual license file.

def find_license_file(skill_dir: Path, repo_dir: Path) -> tuple:
    """Returns (text_or_None, source_description)."""
    for fname in LICENSE_FILENAMES:
        p = skill_dir / fname
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace"), f"skill-level ({fname})"
    for fname in LICENSE_FILENAMES:
        p = repo_dir / fname
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace"), f"repo-root ({fname})"
    return None, "not found"


def classify_license_tier(license_text: str | None) -> tuple:
    """Returns (tier: 1|2|3, label: str). Tier 1 = permissive, proceed with no
    gate. Tier 2 = absent/ambiguous, standing attestation may cover it. Tier 3 =
    explicit proprietary/all-rights-reserved, requires a fresh attestation every
    time -- never covered by a standing authorization."""
    if not license_text:
        return 2, "no license file found"

    text = license_text.strip()
    lower = text.lower()

    if "all rights reserved" in lower or "proprietary" in lower or "governed by your agreement" in lower:
        return 3, "explicit proprietary / all-rights-reserved notice"
    if re.search(r"\bmit license\b", lower) or "permission is hereby granted, free of charge" in lower:
        return 1, "MIT"
    if "apache license" in lower and "version 2.0" in lower:
        return 1, "Apache-2.0"
    if re.search(r"\bbsd\b", lower) and "redistribution and use in source and binary forms" in lower:
        return 1, "BSD"
    if "gnu general public license" in lower:
        return 1, "GPL"
    return 2, "unrecognized license text — needs manual review"


# ── Directory mapping + path-reference rewriting ─────────────────────────────

KNOWN_NON_ASSET_FILES = {"SKILL.md", "LICENSE.txt", "LICENSE", "LICENSE.md", "README.md"}


def copy_skill_assets(source_skill_dir: Path, dest_skill_dir: Path) -> list:
    """Copies scripts/references/examples/templates/assets subdirs per DIR_MAP,
    skipping evals/ entirely. Real-world source repos don't all follow that
    scripts/references/templates convention -- e.g. claude-api's per-language
    subdirectories (python/, typescript/, ...), slack-gif-creator's bare core/
    module + requirements.txt, theme-factory's themes/ + a loose showcase PDF.
    Any top-level directory or file not recognized by DIR_MAP (and not one of
    the known non-asset files) is preserved rather than silently dropped:
    unrecognized directories copy through to assets/templates/<original-name>/,
    unrecognized loose files copy straight into assets/templates/. This was a
    real bug caught converting claude-api/slack-gif-creator/theme-factory --
    those 3 packages were shipping with zero bundled files despite their
    SKILL.md explicitly referencing per-language docs, a Python module, and a
    themes directory, because copy_skill_assets only ever looked at 5 fixed
    names. Returns a list of (src_name, dest_rel) pairs for everything mapped,
    used both to rewrite path references and to build the SKILL.md asset tree.
    """
    mapped = []

    for src_name, dest_rel in DIR_MAP.items():
        src_dir = source_skill_dir / src_name
        if not src_dir.is_dir():
            continue
        dest_dir = dest_skill_dir / dest_rel
        dest_dir.mkdir(parents=True, exist_ok=True)
        for f in sorted(src_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(src_dir)
                target = dest_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(f.read_bytes())
        mapped.append((src_name, dest_rel))

    known_names = set(DIR_MAP) | {"evals"}
    for entry in sorted(source_skill_dir.iterdir()):
        if entry.name in known_names or entry.name in KNOWN_NON_ASSET_FILES:
            continue
        if entry.is_dir():
            dest_rel = f"assets/templates/{entry.name}"
            dest_dir = dest_skill_dir / dest_rel
            dest_dir.mkdir(parents=True, exist_ok=True)
            for f in sorted(entry.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(entry)
                    target = dest_dir / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(f.read_bytes())
            mapped.append((entry.name, dest_rel))
        elif entry.is_file():
            dest_rel = f"assets/templates/{entry.name}"
            dest_dir = dest_skill_dir / "assets" / "templates"
            dest_dir.mkdir(parents=True, exist_ok=True)
            (dest_dir / entry.name).write_bytes(entry.read_bytes())
            mapped.append((entry.name, dest_rel))

    return mapped


def rewrite_path_references(body: str, mapped_dirs: list) -> str:
    """Rewrites bare source-convention path references (references/foo.md,
    scripts/bar.py, templates/baz.html, examples/..., or a catch-all mapping
    like core/ or a loose theme-showcase.pdf) to their assets/-prefixed
    equivalents -- this is exactly the bug caught by hand in 5 of 6 Phase B
    packages before release. mapped_dirs is a list of (src_name, dest_rel)
    pairs, as returned by copy_skill_assets -- dest_rel is used directly rather
    than re-derived from DIR_MAP, since catch-all entries aren't in DIR_MAP at
    all. Note: this only rewrites path-shaped references (trailing slash or
    backtick-quoted) -- a bare Python import like `from core.gif_builder import
    X` in an example snippet is not path-shaped and is not rewritten; the file
    itself is still preserved (see copy_skill_assets), just at a moved path."""
    result = body
    for src_name, dest_rel in mapped_dirs:
        result = result.replace(f"{src_name}/", f"{dest_rel}/")
        result = result.replace(f"`{src_name}`", f"`{dest_rel}`")
    return result


# ── Package generation ────────────────────────────────────────────────────────

def build_readme(templates_dir: Path, tokens: dict, attestation_block: str) -> str:
    """One canonical README template, rendered once -- the same rendered string is
    written to both the repo root and skill/, since the two copies must be
    byte-identical (.aiskill spec v2.3.0, #file-structure)."""
    tmpl = (templates_dir / "README.repo.md.converted.template").read_text(encoding="utf-8")
    t = dict(tokens)
    t["LICENSE_ATTESTATION_SECTION"] = attestation_block
    return substitute(tmpl, t)


def attestation_manifest_block(tier: int, license_label: str, by: str = None, reasoning: str = None, attested_date: str = None) -> str:
    if tier == 1:
        return ""
    return (
        "license_attestation:\n"
        f"  license_status: \"{license_label}\"\n"
        f"  by: \"{by or ATTESTATION_PENDING}\"\n"
        f"  reasoning: \"{reasoning or ATTESTATION_PENDING}\"\n"
        f"  date: \"{attested_date or ATTESTATION_PENDING}\"\n"
    )


def attestation_readme_block(tier: int, license_label: str, by: str = None, reasoning: str = None, attested_date: str = None) -> str:
    if tier == 1:
        return ""
    status = "**PENDING** — this skill requires attestation before it can be committed or pushed. Re-run `convert.py --attestation-for <source_path> --attestation-by \"...\" --attestation-reasoning \"...\"`." \
        if (by or ATTESTATION_PENDING) == ATTESTATION_PENDING else "Resolved — see below."
    return f"""
## License Attestation

**Original license status:** {license_label}

**Attestation:** {status}
**Attested by:** {by or ATTESTATION_PENDING}
**Date:** {attested_date or ATTESTATION_PENDING}
**Reasoning:** {reasoning or ATTESTATION_PENDING}
"""


def generate_package(
    aiskills_root: Path,
    templates_dir: Path,
    source_repo_dir: Path,
    source_path: str,
    source_owner: str,
    source_repo: str,
    dest_account: str,
    author_email: str,
    github_org: str,
    synopsis: str = None,
) -> dict:
    """Generates one converted .aiskill repo on disk. Returns a result dict with
    tier/repo_root/etc for the caller to report and decide commit vs defer."""
    source_skill_dir = source_repo_dir / source_path
    skill_md_path = source_skill_dir / "SKILL.md"
    frontmatter, body = parse_skill_md(skill_md_path)

    name = derive_name(body, frontmatter, source_path)
    description = frontmatter.get("description", "").split(".")[0].strip()
    if not description:
        description = f"Converted from {source_owner}/{source_repo}"

    slug = slug_from_path(source_path)
    origin = origin_segment(source_owner, source_repo)
    repo_name = repo_name_from_origin_and_slug(origin, slug)
    skill_id = id_from_dest_and_slug(dest_account, source_repo, slug)
    skill_uuid = str(uuid.uuid4())
    skill_tags = tags_from_slug(slug)
    today = date.today().isoformat()
    repo_root = aiskills_root / repo_name

    license_text, license_source = find_license_file(source_skill_dir, source_repo_dir)
    tier, license_label = classify_license_tier(license_text)
    spdx_license = {1: license_label}.get(tier, "UNLICENSED" if tier == 2 and license_text is None else "Proprietary")
    if tier == 1:
        spdx_license = license_label

    print(f"\n  {source_path}")
    print(f"    slug:    {slug}")
    print(f"    repo:    {repo_name}")
    print(f"    license: {license_source} -> tier {tier} ({license_label})")

    repo_root.mkdir(parents=True, exist_ok=True)
    skill_root = repo_root / "skill"
    skill_root.mkdir(parents=True, exist_ok=True)

    mapped_dirs = copy_skill_assets(source_skill_dir, skill_root)
    rewritten_body = rewrite_path_references(body, mapped_dirs)
    # SKILL.md has no frontmatter in .aiskill -- title + rewritten body only
    title = f"# {name}\n\n" if not rewritten_body.lstrip().startswith("#") else ""
    write_file(skill_root / "SKILL.md", title + rewritten_body)

    if license_text:
        write_file(skill_root / "LICENSE.txt", license_text)
        write_file(repo_root / "LICENSE", license_text)

    canonical_system_md = templates_dir / "SYSTEM.md"
    write_file(skill_root / "SYSTEM.md", canonical_system_md.read_text(encoding="utf-8"))

    # Dedupe by dest_rel (DIR_MAP can send two different source names to the same
    # destination, e.g. references/ and examples/ both land in assets/references/)
    # and strip the "assets/" prefix the README template already renders as the
    # tree's own root line. A trailing slash marks directories; catch-all loose
    # files (copy_skill_assets) have a real extension in their basename instead.
    asset_tree_lines = []
    for dest_rel in sorted({dest for _, dest in mapped_dirs}):
        display = dest_rel[len("assets/"):] if dest_rel.startswith("assets/") else dest_rel
        is_file = "." in Path(display).name
        asset_tree_lines.append(f"    ├── {display}\n" if is_file else f"    ├── {display}/\n")

    tokens = {
        "NAME": name,
        "SLUG": slug,
        "REPO_NAME": repo_name,
        "ID": skill_id,
        "UUID": skill_uuid,
        "VERSION": DEFAULT_VERSION,
        "DESCRIPTION": f"{description}. Upgraded from a skill originally authored by @{source_owner} on GitHub.",
        "SYNOPSIS": (synopsis or SYNOPSIS_PLACEHOLDER).strip(),
        "SYNOPSIS_BLOCK": synopsis_to_yaml_block(synopsis or SYNOPSIS_PLACEHOLDER),
        "AUTHOR": dest_account,
        "AUTHOR_EMAIL": author_email,
        "TYPE": "instructional" if not any(src == "scripts" for src, _ in mapped_dirs) else "procedural",
        "LICENSE": spdx_license,
        "MINIMUM_RUNTIME": MINIMUM_RUNTIME,
        "SYSTEM_PROTOCOL_VERSION": SYSTEM_PROTOCOL_VERSION,
        "CAPABILITIES_LIST": capabilities_to_yaml_list(""),  # always a placeholder -- never auto-inferred
        "TAGS": tags_to_yaml_inline(skill_tags),
        "TAGS_LIST": ", ".join(skill_tags),  # plain comma-joined, for README prose (not YAML)
        "HOMEPAGE": HOMEPAGE,
        "REPOSITORY": f"https://github.com/{dest_account}/{repo_name}",
        "GITHUB_ORG": github_org,
        "DATE": today,
        "SOURCE_OWNER": source_owner,
        "SOURCE_REPO": source_repo,
        "SOURCE_PATH": source_path,
        "CONVERTED_AT": today,
        "AISKILL_SPEC_VERSION": AISKILL_SPEC_VERSION,
        "LICENSE_ATTESTATION_BLOCK": attestation_manifest_block(tier, license_label),
        "ASSET_TREE": "".join(asset_tree_lines) or "    (no assets)\n",
    }

    # manifest.yaml substitutes NAME/DESCRIPTION as bare YAML scalars -- quote just
    # for this template. README.md and CHANGELOG.md render the same tokens as plain
    # markdown prose (a colon in a heading is fine there), so the shared `tokens`
    # dict itself must stay unquoted for those.
    manifest_tokens = {**tokens, "NAME": yaml_quote(name), "DESCRIPTION": yaml_quote(tokens["DESCRIPTION"])}
    manifest_content = substitute(
        (templates_dir / "manifest.yaml.converted.template").read_text(encoding="utf-8"), manifest_tokens
    )
    write_file(skill_root / "manifest.yaml", manifest_content)

    readme_attestation = attestation_readme_block(tier, license_label)
    readme_content = build_readme(templates_dir, tokens, readme_attestation)
    write_file(skill_root / "README.md", readme_content)
    write_file(repo_root / "README.md", readme_content)

    changelog_content = substitute(
        (templates_dir / "CHANGELOG.md.converted.template").read_text(encoding="utf-8"), tokens
    )
    write_file(skill_root / "CHANGELOG.md", changelog_content)
    write_file(repo_root / "CHANGELOG.md", changelog_content)

    write_file(
        skill_root / "checksums.yaml",
        "# Generated by pack.py — do not edit manually\nalgorithm: sha256\nfiles: {}\n",
    )
    write_file(skill_root / "CARD.md", f"# {name}\n\n_Placeholder — run build_card.py before packaging. Do not hand-edit._\n")

    gitignore_src = templates_dir / "gitignore.template"
    if gitignore_src.exists():
        write_file(repo_root / ".gitignore", gitignore_src.read_text(encoding="utf-8"))

    (repo_root / "dist").mkdir(exist_ok=True)

    return {
        "source_path": source_path,
        "repo_name": repo_name,
        "repo_root": repo_root,
        "tier": tier,
        "license_label": license_label,
        "uuid": skill_uuid,
    }


def finalize_attestation(aiskills_root: Path, source_repo: str, source_path: str, source_owner: str,
                          by: str, reasoning: str) -> None:
    """Re-invocation path: fills in a previously-PENDING attestation for one
    already-generated (but uncommitted) skill, then commits it."""
    slug = slug_from_path(source_path)
    origin = origin_segment(source_owner, source_repo)
    repo_name = repo_name_from_origin_and_slug(origin, slug)
    repo_root = aiskills_root / repo_name
    manifest_path = repo_root / "skill" / "manifest.yaml"
    readme_path = repo_root / "skill" / "README.md"
    repo_readme_path = repo_root / "README.md"

    if not manifest_path.exists():
        print(f"Error: {repo_root} not found -- run a discover/convert pass first", file=sys.stderr)
        sys.exit(1)

    manifest_text = manifest_path.read_text(encoding="utf-8")
    if ATTESTATION_PENDING not in manifest_text:
        print(f"Error: {manifest_path} has no pending attestation to finalize", file=sys.stderr)
        sys.exit(1)

    today = date.today().isoformat()
    manifest_text = manifest_text.replace(f'by: "{ATTESTATION_PENDING}"', f'by: "{by}"')
    manifest_text = manifest_text.replace(f'reasoning: "{ATTESTATION_PENDING}"', f'reasoning: "{reasoning}"')
    manifest_text = manifest_text.replace(f'date: "{ATTESTATION_PENDING}"', f'date: "{today}"')
    manifest_path.write_text(manifest_text, encoding="utf-8")

    for readme_p in (readme_path, repo_readme_path):
        if readme_p.exists():
            text = readme_p.read_text(encoding="utf-8")
            text = text.replace(
                f"**Attestation:** **PENDING** — this skill requires attestation before it can be committed or pushed. Re-run `convert.py --attestation-for <source_path> --attestation-by \"...\" --attestation-reasoning \"...\"`.",
                "**Attestation:** Resolved — see below.",
            )
            text = text.replace(f"**Attested by:** {ATTESTATION_PENDING}", f"**Attested by:** {by}")
            text = text.replace(f"**Date:** {ATTESTATION_PENDING}", f"**Date:** {today}")
            text = text.replace(f"**Reasoning:** {ATTESTATION_PENDING}", f"**Reasoning:** {reasoning}")
            readme_p.write_text(text, encoding="utf-8")

    run(["git", "init"], cwd=repo_root)
    run(["git", "add", "-A"], cwd=repo_root)
    commit = run(["git", "commit", "-m", f"feat: complete {repo_name} v{DEFAULT_VERSION} (attestation resolved)"], cwd=repo_root)
    print(f"\nAttestation finalized and committed: {repo_root}")
    if commit.returncode != 0:
        print(f"  [warn] commit: {commit.stderr.strip()}", file=sys.stderr)
    print("Review with the user before creating a GitHub repo or pushing.")


# ── Main ─────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Convert skill(s) from a foreign Agent Skills repo into .aiskill package(s)."
    )
    p.add_argument("--aiskills-root", required=True)
    p.add_argument("--source-repo", required=True, help="owner/repo, e.g. anthropics/skills")
    p.add_argument("--source-path", help="Single skill path within the repo (mutually exclusive with --skills)")
    p.add_argument("--skills", help="Comma-separated cherry-picked skill paths (mutually exclusive with --source-path)")
    p.add_argument("--dest-account", help="Destination account, e.g. Xamtastic (required unless --attestation-for)")
    p.add_argument("--author-email", help="Required unless --attestation-for")
    p.add_argument("--synopsis",
                   help="Multi-paragraph expansion of the description, hand-authored by reading the "
                        "actual source skill (never auto-extracted). Only meaningful for a single-skill "
                        "--source-path conversion -- batch/cherry-pick runs get a TODO placeholder per "
                        "skill instead, to be filled in by hand afterward, same as capabilities/permissions")
    p.add_argument("--github-org", help="Defaults to --dest-account if omitted")
    p.add_argument("--scratch-dir", default="/tmp/aiskill-convert-scratch")
    p.add_argument("--attestation-for", help="source_path of a previously-deferred skill to finalize")
    p.add_argument("--attestation-by")
    p.add_argument("--attestation-reasoning")
    return p.parse_args()


def main():
    args = parse_args()
    aiskills_root = Path(args.aiskills_root).expanduser().resolve()
    if not aiskills_root.exists():
        print(f"Error: --aiskills-root does not exist: {aiskills_root}", file=sys.stderr)
        sys.exit(1)

    source_owner, source_repo = args.source_repo.split("/", 1)

    if args.attestation_for:
        if not args.attestation_by or not args.attestation_reasoning:
            print("Error: --attestation-for requires --attestation-by and --attestation-reasoning", file=sys.stderr)
            sys.exit(1)
        finalize_attestation(aiskills_root, source_repo, args.attestation_for, source_owner,
                              args.attestation_by, args.attestation_reasoning)
        return

    if not args.dest_account or not args.author_email:
        print("Error: --dest-account and --author-email are required unless --attestation-for is given", file=sys.stderr)
        sys.exit(1)
    github_org = args.github_org or args.dest_account

    if args.source_path and args.skills:
        print("Error: --source-path and --skills are mutually exclusive", file=sys.stderr)
        sys.exit(1)
    if args.synopsis and not args.source_path:
        print(
            "Error: --synopsis only applies to a single-skill --source-path conversion "
            "(it would be misapplied to every skill in a --skills/batch run). Omit it for "
            "batch/cherry-pick runs -- each generated package gets a TODO placeholder to "
            "fill in by hand afterward instead.",
            file=sys.stderr,
        )
        sys.exit(1)

    templates_dir = Path(__file__).parent.parent / "templates"
    scratch_dir = Path(args.scratch_dir).expanduser()
    scratch_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nConverting from {args.source_repo}")
    source_repo_dir = clone_source_repo(args.source_repo, scratch_dir)
    skill_paths = discover_skills(source_repo_dir, args.source_path, args.skills)
    print(f"  discovered {len(skill_paths)} skill(s): {', '.join(skill_paths)}")

    tier1_results, deferred_results = [], []
    for source_path in skill_paths:
        result = generate_package(
            aiskills_root, templates_dir, source_repo_dir, source_path,
            source_owner, source_repo, args.dest_account, args.author_email, github_org,
            synopsis=args.synopsis,
        )
        if result["tier"] == 1:
            run(["git", "init"], cwd=result["repo_root"])
            run(["git", "add", "-A"], cwd=result["repo_root"])
            run(["git", "commit", "-m", f"feat: complete {result['repo_name']} v{DEFAULT_VERSION}"],
                cwd=result["repo_root"])
            tier1_results.append(result)
        else:
            deferred_results.append(result)

    print(f"\n{'='*60}")
    print(f"Converted (tier 1, committed): {len(tier1_results)}")
    for r in tier1_results:
        print(f"  {r['source_path']:40s} -> {r['repo_name']}")
    print(f"\nDeferred (tier {2}/{3}, needs attestation): {len(deferred_results)}")
    for r in deferred_results:
        print(f"  {r['source_path']:40s} -> {r['repo_name']}  [tier {r['tier']}: {r['license_label']}]")
        print(f"    resolve with: python3 {Path(__file__).name} --aiskills-root {aiskills_root} "
              f"--source-repo {args.source_repo} --attestation-for {r['source_path']} "
              f"--attestation-by \"...\" --attestation-reasoning \"...\"")
    print(f"{'='*60}\n")
    if not args.synopsis:
        print("Every generated manifest.yaml/README.md has a TODO synopsis placeholder -- "
              "write each package's real 3-paragraph synopsis by hand before packaging.")
    print("Review with the user before creating any GitHub repo or pushing.")


if __name__ == "__main__":
    main()
