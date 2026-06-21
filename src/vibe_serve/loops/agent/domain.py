"""Domain packs — pluggable, per-problem-space prompt context.

A *domain* tells the agent loop what kind of system it is building and what
"good" means there: the background knowledge the implementer must read, and the
correctness/performance/integrity gates the judge must enforce. It is selected
with ``--domain`` and authored as a **single Markdown file** whose ``##`` role
sections are injected into the neutral base prompts as ``{{ domain_<role> }}``.

Domain is one of two axes built on the shared single-file pack mechanism in
:mod:`vibe_serve.loops.agent.pack` (the other is ``language``); this module just
binds that machinery to the ``_domain/`` directory and the ``llm-serving``
default. See ``loops/agent/templates/_domain/README.md`` for the authoring guide
and ``pack.py`` for the file format (``## <role>`` sections, ``single_agent``
derivation, name-or-path resolution).
"""

from __future__ import annotations

from pathlib import Path

from vibe_serve.loops.agent.pack import (
    ROLES,
    builtin_packs,
    render_pack_section,
    resolve_pack,
)

DEFAULT_DOMAIN = "llm-serving"

# The roles a domain pack can contribute to (shared across pack axes).
DOMAIN_ROLES: tuple[str, ...] = ROLES

_BUILTIN_DOMAINS_DIR = Path(__file__).resolve().parent / "templates" / "_domain"


def builtin_domains() -> list[str]:
    """Names of the built-in domain packs (``<name>.md`` files under ``_domain/``)."""
    return builtin_packs(_BUILTIN_DOMAINS_DIR)


def resolve_domain(spec: str) -> Path:
    """Resolve a ``--domain`` value to a domain-pack Markdown file (name or path)."""
    return resolve_pack(spec, builtin_dir=_BUILTIN_DOMAINS_DIR, kind="domain")


def render_domain_section(domain_file: Path, role: str, **context: object) -> str:
    """Render a domain file's ``## <role>`` section, or ``""`` if absent/empty."""
    return render_pack_section(domain_file, role, **context)
