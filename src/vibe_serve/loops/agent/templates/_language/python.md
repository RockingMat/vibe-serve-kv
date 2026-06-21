# Python

**Use for:** building the target in Python with the `uv` toolchain. This is the
default language (`--language python`); it reproduces vibeserve's original
Python tooling instructions, lifted out of the neutral base prompts.

The `implementer` and `single_agent` sections carry the same `uv` guidance the
base prompts used to hard-code; there is no language-specific `judge` gate.

## implementer
Use `uv` for Python package management. Run `uv init` if `pyproject.toml` doesn't exist yet, and `uv add` for new dependencies. Always execute scripts via `uv run`.

## single_agent
Use `uv` for Python packaging — `uv init` if needed, `uv add` for deps, `uv run` for execution.
