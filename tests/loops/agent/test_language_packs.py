"""Tests for language packs — the ``--language`` pluggable-toolchain mechanism.

Language packs reuse the shared single-file ``pack`` machinery (also exercised by
``test_domain_packs.py``); these tests cover the language axis specifically: its
resolver/defaults, the built-in ``python`` / ``generic`` packs, injection into
the base prompts, and the **byte-identical** guarantee that ``--language python``
(the default) reproduces the original hard-coded ``uv`` tooling prose on the
multi-agent implementer/judge path.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path

import pytest

from vibe_serve.loops.agent.pack import (
    DEFAULT_LANGUAGE,
    LANGUAGE_DIR,
    builtin_packs,
    resolve_pack,
)
from vibe_serve.loops.agent.pack import (
    render_pack_section as render_language_section,
)
from vibe_serve.prompts import render_template

# This module exercises only the language axis; bind it once.
resolve_language = partial(resolve_pack, builtin_dir=LANGUAGE_DIR, kind="language")

_TEMPLATE_DIR = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "vibe_serve"
    / "loops"
    / "agent"
    / "templates"
)

# The exact tooling prose the base prompts hard-coded before language packs. The
# `python` pack must reproduce these verbatim so the default run is unchanged.
_PY_IMPLEMENTER_LINE = (
    "Use `uv` for Python package management. Run `uv init` if `pyproject.toml` "
    "doesn't exist yet, and `uv add` for new dependencies. Always execute "
    "scripts via `uv run`."
)
_PY_SINGLE_AGENT_LINE = (
    "Use `uv` for Python packaging — `uv init` if needed, `uv add` for deps, "
    "`uv run` for execution."
)


# --------------------------------------------------------------------------- #
# resolver / defaults
# --------------------------------------------------------------------------- #
def test_builtins_present():
    names = builtin_packs(LANGUAGE_DIR)
    assert "python" in names
    assert "generic" in names
    assert "README" not in names  # the authoring guide is not a language
    assert DEFAULT_LANGUAGE == "python"


def test_resolve_builtin_name():
    lang = resolve_language("python")
    assert lang.is_file()
    assert lang.name == "python.md"


def test_resolve_path(tmp_path: Path):
    f = tmp_path / "rust.md"
    f.write_text("# Rust\n\n## implementer\nUse cargo.\n")
    assert resolve_language(str(f)) == f.resolve()


def test_resolve_unknown_raises():
    with pytest.raises(ValueError) as exc:
        resolve_language("does-not-exist-xyz")
    # error names the axis and lists built-ins to guide the user
    assert "language" in str(exc.value)
    assert "python" in str(exc.value)


# --------------------------------------------------------------------------- #
# section renderer
# --------------------------------------------------------------------------- #
def test_python_implementer_is_uv_prose():
    lang = resolve_language("python")
    impl = render_language_section(lang, "implementer", modality="text_generation")
    assert impl == _PY_IMPLEMENTER_LINE


def test_python_single_agent_is_explicit_not_derived():
    # python.md ships an explicit ## single_agent (terser than implementer); it
    # must be used verbatim rather than derived from implementer + judge.
    lang = resolve_language("python")
    sa = render_language_section(lang, "single_agent")
    assert sa == _PY_SINGLE_AGENT_LINE


def test_python_has_no_judge_section():
    lang = resolve_language("python")
    assert render_language_section(lang, "judge") == ""


def test_generic_injects_nothing():
    lang = resolve_language("generic")
    for role in ("implementer", "judge", "single_agent"):
        assert render_language_section(lang, role) == ""


# --------------------------------------------------------------------------- #
# end-to-end injection into base prompts
# --------------------------------------------------------------------------- #
def _render_implementer(language: str) -> str:
    section = render_language_section(
        resolve_language(language), "implementer", modality="text_generation"
    )
    return render_template(
        "implementer_prompt.j2",
        template_dir=_TEMPLATE_DIR,
        modality="text_generation",
        domain_implementer="",  # isolate the language axis
        language_implementer=section,
        task="TASK",
        pass_criteria="PC",
        reference_path="/ref",
        runtime_notes="",
        feedback=None,
    )


def test_python_default_reproduces_uv_line_byte_for_byte():
    """`--language python` injects the uv line exactly where the base hard-coded
    it: one blank line after the workspace paragraph, one blank line before the
    next section — no drift from the pre-language-pack output."""
    out = _render_implementer("python")
    expected_block = (
        "is at `/ref`.\n"
        "\n"
        f"{_PY_IMPLEMENTER_LINE}\n"
        "\n"
        "## Progress tracking"
    )
    assert expected_block in out


def test_generic_language_omits_uv_and_collapses_cleanly():
    out = _render_implementer("generic")
    assert "uv" not in out
    # empty injection must not leave a triple-newline gap at the seam
    idx = out.index("## Progress tracking")
    assert "\n\n\n" not in out[max(0, idx - 6) : idx]
    # base skeleton intact
    assert "## Progress tracking" in out


def test_language_and_domain_compose_independently():
    """Both axes inject into the same implementer prompt without interfering."""
    out = render_template(
        "implementer_prompt.j2",
        template_dir=_TEMPLATE_DIR,
        modality="text_generation",
        domain_implementer="DOMAIN-SENTINEL",
        language_implementer="LANG-SENTINEL",
        task="TASK",
        pass_criteria="PC",
        reference_path="/ref",
        runtime_notes="",
        feedback=None,
    )
    assert "LANG-SENTINEL" in out
    assert "DOMAIN-SENTINEL" in out
    # language (tooling) is injected before domain (problem-space context)
    assert out.index("LANG-SENTINEL") < out.index("DOMAIN-SENTINEL")
