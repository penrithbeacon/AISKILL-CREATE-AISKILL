#!/usr/bin/env python3
"""
scaffold.py — CREATE-AISKILL v2.4.0
Creates a complete AISKILL-{SLUG} repository structure for a new, originally-authored
.aiskill package (Track A). For converting an existing skill from another format, see
convert.py (Track B) instead.
"""

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


# ── Conventions (baked in per spec) ─────────────────────────────────────────

REPO_PREFIX = "AISKILL"
HOMEPAGE = "https://penrithbeacon.com/"
MINIMUM_RUNTIME = "1.0.0"
DEFAULT_VERSION = "1.0.0"
SYSTEM_PROTOCOL_VERSION = "1.0.0"  # must match SYSTEM.md's own "Protocol Version" header
DEFAULT_LICENSE = "UNLICENSED"
DEFAULT_CAPABILITIES = "filesystem.read,filesystem.write,process.exec"


# ── Slug and identity helpers ────────────────────────────────────────────────

def slug_from_name(name: str) -> str:
    """'WCAG Contrast Audit' → 'WCAG-CONTRAST-AUDIT'"""
    cleaned = re.sub(r"[^A-Za-z0-9\s-]", "", name)
    return re.sub(r"[\s-]+", "-", cleaned).strip("-").upper()


def repo_name_from_slug(slug: str) -> str:
    """'WCAG-CONTRAST-AUDIT' → 'AISKILL-WCAG-CONTRAST-AUDIT'"""
    return f"{REPO_PREFIX}-{slug}"


def id_from_domain_and_slug(domain: str, slug: str) -> str:
    """('com.openaiskillpackage', 'WCAG-CONTRAST-AUDIT') → 'com.openaiskillpackage.wcag-contrast-audit'"""
    return f"{domain}.{slug.lower()}"


def tags_from_slug(slug: str) -> list:
    """'MY-COOL-SKILL' → ['my', 'cool', 'skill']"""
    return [w.lower() for w in slug.split("-")]


def capabilities_to_yaml_list(capabilities_str: str) -> str:
    caps = [c.strip() for c in capabilities_str.split(",") if c.strip()]
    return "\n".join(f"  - {c}" for c in caps)


def tags_to_yaml_inline(tags: list) -> str:
    return "[" + ", ".join(tags) + "]"


def synopsis_to_yaml_block(synopsis: str) -> str:
    """Indents a multi-paragraph synopsis two spaces per line, for embedding
    under manifest.yaml's `synopsis: |` block scalar."""
    lines = synopsis.strip("\n").split("\n")
    return "\n".join(f"  {line}" if line else "" for line in lines)


def yaml_quote(value: str) -> str:
    """Returns value as a YAML-safe double-quoted scalar. manifest.yaml.template
    substitutes NAME/DESCRIPTION as bare, unquoted scalars (`name: <<<NAME>>>`) --
    a name or description containing a colon (e.g. "X: a subtitle") breaks that
    plain substitution, since YAML reads "X: Y" as a nested mapping key/value
    rather than plain text. Same class of bug convert.py's own NAME/DESCRIPTION
    substitution had (caught converting transformer-lens); fixed here too since
    Track A's --name/--description are just as free-form."""
    return yaml.dump(value, default_style='"', width=float("inf")).strip()


# ── Template substitution ────────────────────────────────────────────────────

def substitute(template: str, tokens: dict) -> str:
    """Replace <<<TOKEN>>> markers in template with values from tokens dict."""
    result = template
    for key, value in tokens.items():
        result = result.replace(f"<<<{key}>>>", str(value))
    return result


# ── Directory and file creation ──────────────────────────────────────────────

def create_tree(repo_root: Path) -> None:
    dirs = [
        repo_root,
        repo_root / "skill" / "assets" / "scripts",
        repo_root / "skill" / "assets" / "templates",
        repo_root / "skill" / "assets" / "tests",
        repo_root / "skill" / "inputs",
        repo_root / "dist",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"  wrote  {path.relative_to(path.parents[len(path.parts) - 2])}")


# ── Git operations ───────────────────────────────────────────────────────────

def run(cmd: list, cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [warn] {' '.join(cmd)} exited {result.returncode}: {result.stderr.strip()}", file=sys.stderr)


# ── Main ─────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Scaffold a new AISKILL-{SLUG} repository for a .aiskill package."
    )
    p.add_argument("--aiskills-root", required=True,
                   help="Absolute path to the folder containing all AISKILL repos")
    p.add_argument("--name", required=True,
                   help="Human-readable skill name, e.g. 'WCAG Contrast Audit'")
    p.add_argument("--description", required=True,
                   help="One-line purpose statement")
    p.add_argument("--synopsis", required=True,
                   help="Multi-paragraph expansion of --description (recommended structure: "
                        "what it does, when to reach for it, why to trust this package). "
                        "Hand-authored, never derived from README.md")
    p.add_argument("--author", required=True,
                   help="Author name or organisation")
    p.add_argument("--author-email", required=True,
                   help="Contact email address")
    p.add_argument("--type", required=True,
                   choices=["procedural", "analytical", "generative"],
                   help="Skill type")
    p.add_argument("--id-domain", required=True,
                   help="Reverse-domain prefix, e.g. com.openaiskillpackage")
    p.add_argument("--github-org", required=True,
                   help="GitHub organisation or user, e.g. YourGitHubOrg")
    p.add_argument("--license", default=DEFAULT_LICENSE,
                   help=f"SPDX identifier, Proprietary, or UNLICENSED (default: {DEFAULT_LICENSE}) — "
                        "decide this via a conversation with the user, never guess it")
    p.add_argument("--capabilities", default=DEFAULT_CAPABILITIES,
                   help="Comma-separated capability tokens")
    p.add_argument("--slug",
                   help="UPPER-KEBAB-CASE slug (auto-derived from --name if omitted)")
    return p.parse_args()


def main():
    args = parse_args()

    aiskills_root = Path(args.aiskills_root).expanduser().resolve()
    if not aiskills_root.exists():
        print(f"Error: --aiskills-root does not exist: {aiskills_root}", file=sys.stderr)
        sys.exit(1)

    slug = args.slug if args.slug else slug_from_name(args.name)
    repo_name = repo_name_from_slug(slug)
    skill_id = id_from_domain_and_slug(args.id_domain, slug)
    skill_uuid = str(uuid.uuid4())
    skill_tags = tags_from_slug(slug)
    today = date.today().isoformat()
    repo_root = aiskills_root / repo_name
    github_url = f"https://github.com/{args.github_org}/{repo_name}.git"

    if repo_root.exists():
        print(f"Error: target directory already exists: {repo_root}", file=sys.stderr)
        sys.exit(1)

    templates_dir = Path(__file__).parent.parent / "templates"

    print(f"\nScaffolding {repo_name}")
    print(f"  slug:   {slug}")
    print(f"  id:     {skill_id}")
    print(f"  uuid:   {skill_uuid}")
    print(f"  remote: {github_url}")
    print()

    # ── Tokens shared across all templates ──
    tokens = {
        "NAME": args.name,
        "SLUG": slug,
        "REPO_NAME": repo_name,
        "ID": skill_id,
        "UUID": skill_uuid,
        "VERSION": DEFAULT_VERSION,
        "DESCRIPTION": args.description,
        "SYNOPSIS": args.synopsis.strip(),
        "SYNOPSIS_BLOCK": synopsis_to_yaml_block(args.synopsis),
        "AUTHOR": args.author,
        "AUTHOR_EMAIL": args.author_email,
        "TYPE": args.type,
        "LICENSE": args.license,
        "MINIMUM_RUNTIME": MINIMUM_RUNTIME,
        "SYSTEM_PROTOCOL_VERSION": SYSTEM_PROTOCOL_VERSION,
        "CAPABILITIES_LIST": capabilities_to_yaml_list(args.capabilities),
        "TAGS": tags_to_yaml_inline(skill_tags),
        "TAGS_LIST": ", ".join(skill_tags),  # plain comma-joined, for README prose (not YAML)
        "HOMEPAGE": HOMEPAGE,
        "REPOSITORY": f"https://github.com/{args.github_org}/{repo_name}",
        "GITHUB_ORG": args.github_org,
        "DATE": today,
        "SKILL_NAME": args.name,
        "SKILL_DESCRIPTION": args.description,
        "SKILL_VERSION": DEFAULT_VERSION,
    }

    # ── Create directories ──
    create_tree(repo_root)

    # ── Write from templates ──
    template_map = {
        "manifest.yaml.template":      repo_root / "skill" / "manifest.yaml",
        "SKILL.md.template":           repo_root / "skill" / "SKILL.md",
        "CHANGELOG.md.template":       repo_root / "skill" / "CHANGELOG.md",
        "schema.json.template":        repo_root / "skill" / "inputs" / "schema.json",
        "gitignore.template":          repo_root / ".gitignore",
    }

    # manifest.yaml substitutes NAME/DESCRIPTION as bare YAML scalars -- quote just
    # for this one template. Every other template in the loop below (SKILL.md,
    # CHANGELOG.md) renders the same tokens as plain markdown prose, where a colon
    # is harmless, so the shared `tokens` dict itself must stay unquoted for those.
    manifest_tokens = {**tokens, "NAME": yaml_quote(args.name), "DESCRIPTION": yaml_quote(args.description)}

    for tmpl_name, dest_path in template_map.items():
        tmpl_path = templates_dir / tmpl_name
        if not tmpl_path.exists():
            print(f"  [warn] template not found: {tmpl_path}", file=sys.stderr)
            continue
        active_tokens = manifest_tokens if tmpl_name == "manifest.yaml.template" else tokens
        content = substitute(tmpl_path.read_text(encoding="utf-8"), active_tokens)
        write_file(dest_path, content)

    # README.md — one canonical template, rendered once and written identically to
    # both the repo root and skill/, since packaging only ever zips skill/'s contents
    # and skill/README.md is the only copy a recipient of the distributed .aiskill
    # file ever sees (.aiskill spec v2.3.0, #file-structure). The two copies must be
    # byte-identical, so both are written from the exact same rendered string.
    readme_content = substitute(
        (templates_dir / "README.repo.md.template").read_text(encoding="utf-8"), tokens
    )
    write_file(repo_root / "README.md", readme_content)
    write_file(repo_root / "skill" / "README.md", readme_content)

    # Repo-level CHANGELOG uses same template as skill-level
    repo_changelog = substitute(
        (templates_dir / "CHANGELOG.md.template").read_text(encoding="utf-8"), tokens
    )
    write_file(repo_root / "CHANGELOG.md", repo_changelog)

    # Placeholder checksums.yaml (pack.py will overwrite with real hashes)
    write_file(
        repo_root / "skill" / "checksums.yaml",
        "# Generated by pack.py — do not edit manually\nalgorithm: sha256\nfiles: {}\n"
    )

    # Placeholder CARD.md (build_card.py will overwrite from the real manifest.yaml)
    write_file(
        repo_root / "skill" / "CARD.md",
        f"# {args.name}\n\n_Placeholder — run build_card.py before packaging. Do not hand-edit._\n"
    )

    # SYSTEM.md is copied verbatim, never templated -- it's spec-mandated to be
    # byte-identical across every .aiskill package in existence (see the
    # .aiskill spec v2.2.0). The canonical source lives alongside the other
    # template files (assets/templates/SYSTEM.md) -- this repo's own top-level
    # skill/SYSTEM.md is itself just a verbatim copy of that same source
    # (required since this meta-skill is itself a .aiskill package), kept in
    # sync manually, the same as every other package's copy. pack.py enforces
    # the byte-match against the templates/ source at packaging time.
    canonical_system_md = templates_dir / "SYSTEM.md"
    write_file(repo_root / "skill" / "SYSTEM.md", canonical_system_md.read_text(encoding="utf-8"))

    # ── Git init and remote ──
    print("\nInitialising git repository...")
    run(["git", "init"], cwd=repo_root)
    run(["git", "remote", "add", "origin", github_url], cwd=repo_root)
    run(["git", "add", "-A"], cwd=repo_root)
    run(["git", "commit", "-m", f"chore: scaffold {repo_name} v{DEFAULT_VERSION}"], cwd=repo_root)
    print(f"  git remote: {github_url}")

    # ── Next steps ──
    print(f"""
{'='*60}
Scaffolded:  {repo_root}
UUID:        {skill_uuid}
Remote:      {github_url}

Next steps:
  1. Edit skill/SKILL.md — fill in the full procedure for your skill
  2. Write skill/assets/scripts/*.py + skill/assets/tests/test_*.py
  3. python3 skill/assets/scripts/build_card.py --skill-dir skill/
  4. python3 -m pytest skill/assets/tests/ -v   (must all pass)
  5. python3 skill/assets/scripts/pack.py \\
       --skill-dir skill/ --dist-dir dist/ \\
       --website-skills-dir /path/to/ai-skills
  6. git push origin main
  7. git tag v{DEFAULT_VERSION} && git push origin v{DEFAULT_VERSION}
  8. gh release create v{DEFAULT_VERSION} dist/{slug}-{DEFAULT_VERSION}.aiskill \\
       --title "v{DEFAULT_VERSION} — Initial release"
{'='*60}
""")


if __name__ == "__main__":
    main()
