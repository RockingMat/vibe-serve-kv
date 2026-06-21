"""Prompt packs — pluggable, single-file Markdown context for the base prompts.

A *pack* is one Markdown file whose ``## <role>`` sections are injected into the
neutral base prompts at ``{{ <kind>_<role> }}`` points. Two axes use this exact
mechanism, differing only in their on-disk directory and variable prefix:

- **domain** (``--domain``, ``_domain/<name>.md`` → ``{{ domain_<role> }}``): what
  kind of system the agent is building and what "good" means there — the
  background the implementer must read and the gates the judge must enforce. See
  :mod:`vibe_serve.loops.agent.domain`.
- **language** (``--language``, ``_language/<name>.md`` → ``{{ language_<role> }}``):
  the implementation language's tooling and idioms (e.g. ``uv`` / ``uv run`` for
  Python). See :mod:`vibe_serve.loops.agent.language`.

This module is the shared machinery; ``domain.py`` and ``language.py`` are thin
per-axis wrappers that bind a built-in directory, a default, and a ``kind`` label
for error messages.

    _<kind>/<name>.md
    ├── (free-form prose / description — ignored by the loop)
    ├── ## implementer    ← injected as {{ <kind>_implementer }}
    ├── ## judge          ← injected as {{ <kind>_judge }}
    └── ## single_agent   ← injected as {{ <kind>_single_agent }}

The section heading *is* the address: a line that is exactly ``## <role>`` (for a
role in :data:`ROLES`) starts that role's section, which runs until the next role
heading. The section body is normal Markdown — it may use its own ``##``
sub-headings (those never match a role name) and may use ``{% if %}`` Jinja to
branch on the run's context. Any prose before the first role heading is human
documentation and is not injected.

A missing role section injects nothing. ``single_agent`` is special: if the file
has no ``## single_agent`` section, it is *derived* by concatenating the
``implementer`` and ``judge`` sections, so authors don't hand-maintain a third
copy.

A ``--domain`` / ``--language`` value is either a **built-in name** (a
``<name>.md`` under the axis's ``_<kind>/`` directory) or a **path** to a user's
own ``.md`` file anywhere on disk, so users can author their own without touching
vibeserve.
"""

from __future__ import annotations

from pathlib import Path

from vibe_serve.prompts import render_string

# The roles a pack can contribute to. Each maps to a ``## <role>`` section in the
# pack file and a ``{{ <kind>_<role> }}`` injection point in the corresponding
# base prompt. Shared by every pack axis (domain, language, …); ``orchestrator``
# is only injected for the domain axis, but recognizing it here is harmless for
# the others (an unused section is simply never rendered).
ROLES: tuple[str, ...] = ("implementer", "judge", "single_agent", "orchestrator")


def builtin_packs(builtin_dir: Path) -> list[str]:
    """Names of the built-in packs (``<name>.md`` files under ``builtin_dir``)."""
    if not builtin_dir.is_dir():
        return []
    return sorted(p.stem for p in builtin_dir.glob("*.md") if p.name != "README.md")


def resolve_pack(spec: str, *, builtin_dir: Path, kind: str) -> Path:
    """Resolve a pack selector to a pack Markdown file.

    ``spec`` is either a path to a ``.md`` file (used as-is) or the name of a
    built-in pack (``builtin_dir/<spec>.md``). ``kind`` is the axis label used in
    the error message. Raises ``ValueError`` with the list of built-ins if
    neither resolves.
    """
    candidate = Path(spec).expanduser()
    if candidate.is_file():
        return candidate.resolve()

    builtin = builtin_dir / f"{spec}.md"
    if builtin.is_file():
        return builtin

    raise ValueError(
        f"Unknown {kind} {spec!r}. Pass a built-in name "
        f"({', '.join(builtin_packs(builtin_dir))}) or a path to a {kind} .md file."
    )


def _role_heading(line: str) -> str | None:
    """Return the role name if ``line`` is exactly a ``## <role>`` heading.

    Only headings whose text matches a name in :data:`ROLES` delimit a section,
    so a body's own ``## Required: …`` sub-headings are left intact.
    """
    stripped = line.strip()
    if not stripped.startswith("##"):
        return None
    name = stripped.lstrip("#").strip()
    return name if name in ROLES else None


def _load_sections(pack_file: Path) -> dict[str, str]:
    """Parse a pack file into ``{role: raw_section_text}``.

    Lines before the first role heading (description prose) are ignored.
    """
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in pack_file.read_text().splitlines():
        heading = _role_heading(line)
        if heading is not None:
            current = heading
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return {role: "\n".join(lines).strip("\n") for role, lines in sections.items()}


def render_pack_section(pack_file: Path, role: str, **context: object) -> str:
    """Render a pack file's ``## <role>`` section, or ``""`` if absent/empty.

    The section is rendered through Jinja with ``context`` (e.g. ``modality``,
    ``bench_path``, ``accuracy_checker_path``) so pack authors can branch on the
    run. ``single_agent`` falls back to ``implementer`` + ``judge`` when the file
    has no explicit ``## single_agent`` section. Leading and trailing blank lines
    are stripped — the base template owns the spacing around the
    ``{{ <kind>_<role> }}`` injection point.
    """
    sections = _load_sections(pack_file)
    raw = sections.get(role)
    if raw is None and role == "single_agent":
        raw = "\n\n".join(
            text
            for text in (sections.get("implementer"), sections.get("judge"))
            if text
        )
    if not raw:
        return ""
    return render_string(raw, **context).strip("\n")
