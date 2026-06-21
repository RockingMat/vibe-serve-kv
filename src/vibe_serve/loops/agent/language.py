"""Language packs — pluggable, per-implementation-language prompt context.

A *language* tells the agent loop which implementation language and toolchain to
build the target in: the package manager, how to run scripts, and any
language-specific review gates (e.g. a linter the judge should require). It is
selected with ``--language`` and authored as a **single Markdown file** whose
``##`` role sections are injected into the neutral base prompts as
``{{ language_<role> }}``.

Language is one of two axes built on the shared single-file pack mechanism in
:mod:`vibe_serve.loops.agent.pack` (the other is ``domain``); this module just
binds that machinery to the ``_language/`` directory and the ``python`` default.
The two axes are orthogonal — *domain* owns what you're building, *language*
owns the tooling — and compose: their sections inject at separate points in the
same base prompt. See ``loops/agent/templates/_language/README.md`` for the
authoring guide and ``pack.py`` for the file format.
"""

from __future__ import annotations

from pathlib import Path

from vibe_serve.loops.agent.pack import (
    ROLES,
    builtin_packs,
    render_pack_section,
    resolve_pack,
)

DEFAULT_LANGUAGE = "python"

# The roles a language pack can contribute to (shared across pack axes).
LANGUAGE_ROLES: tuple[str, ...] = ROLES

_BUILTIN_LANGUAGES_DIR = Path(__file__).resolve().parent / "templates" / "_language"


def builtin_languages() -> list[str]:
    """Names of the built-in language packs (``<name>.md`` files under ``_language/``)."""
    return builtin_packs(_BUILTIN_LANGUAGES_DIR)


def resolve_language(spec: str) -> Path:
    """Resolve a ``--language`` value to a language-pack Markdown file (name or path)."""
    return resolve_pack(spec, builtin_dir=_BUILTIN_LANGUAGES_DIR, kind="language")


def render_language_section(language_file: Path, role: str, **context: object) -> str:
    """Render a language file's ``## <role>`` section, or ``""`` if absent/empty."""
    return render_pack_section(language_file, role, **context)
