"""Tests for the additive `_language/<lang>/` prompt hint layer.

The agent base prompts (`implementer_prompt.j2`,
`single_agent_round_prompt.j2`) pull language-specific build/run tooling
prose from `_language/<target_language>/implementer.j2`, falling back to
`_language/_default/implementer.j2`. These tests pin that behaviour:

- the Python path still emits the exact `uv` tooling prose (regression guard),
- an unmodelled language degrades to the neutral default (no `uv` leak),
- `target_language` defaults to ``python`` when the caller omits it.
"""

from pathlib import Path

import pytest

from vibe_serve.prompts import render_template

_TEMPLATE_DIR = (
    Path(__file__).resolve().parents[3]
    / "src" / "vibe_serve" / "loops" / "agent" / "templates"
)

_PYTHON_TOOLING = (
    "Use `uv` for Python package management. Run `uv init` if "
    "`pyproject.toml` doesn't exist yet, and `uv add` for new dependencies. "
    "Always execute scripts via `uv run`."
)
_DEFAULT_TOOLING_MARKER = "standard build and dependency tooling"


def _impl(**kwargs) -> str:
    base = dict(
        modality="text_generation",
        reference_path="reference/seed.py",
        task="Implement /v1/completions.",
        pass_criteria="Returns 200.",
        retry=1,
        feedback=None,
        runtime_notes="Local CUDA.",
        env_kind="local",
    )
    base.update(kwargs)
    return render_template(
        "implementer_prompt.j2", template_dir=_TEMPLATE_DIR, **base
    )


def test_python_emits_uv_tooling():
    out = _impl(target_language="python")
    assert _PYTHON_TOOLING in out
    assert _DEFAULT_TOOLING_MARKER not in out


def test_target_language_defaults_to_python():
    # Omitting target_language must behave exactly like passing "python".
    assert _impl() == _impl(target_language="python")


@pytest.mark.parametrize("lang", ["rust", "go", "zig-not-a-real-dir"])
def test_unmodelled_language_falls_back_to_default(lang):
    out = _impl(target_language=lang)
    assert "uv" not in out  # no Python tooling leaks into other languages
    assert _DEFAULT_TOOLING_MARKER in out


def test_language_layer_applies_across_modalities():
    # The language layer lives in the base, so it applies regardless of modality.
    for modality in ("text_generation", "image_generation", "speech_to_text"):
        out = _impl(modality=modality, target_language="python")
        assert _PYTHON_TOOLING in out


def test_single_agent_prompt_uses_language_layer():
    out = render_template(
        "single_agent_round_prompt.j2",
        template_dir=_TEMPLATE_DIR,
        modality="text_generation",
        target_language="python",
        reference_path="reference/seed.py",
        task="t",
        pass_criteria="p",
        retry=1,
        feedback=None,
        runtime_notes="n",
        env_kind="local",
        objective="Headline metric: median_tok_per_sec",
        profile_focus="decode",
        profiler_kind="nsys",
        bench_path="bench",
        accuracy_checker_path="acc_checker",
    )
    assert _PYTHON_TOOLING in out
    # default fallback prose should not appear on the python path
    assert _DEFAULT_TOOLING_MARKER not in out
