# Language hint layers

This directory holds **per-language hint partials** — small Jinja snippets that
describe the build/dependency/run tooling idioms for the implementation language
the candidate is written in. They are an *additive* layer, parallel to
`_modality/<name>/`:

```
_language/
├── python/                 ← Python (uv) tooling prose
│   └── implementer.j2
└── _default/               ← language-agnostic fallback
    └── implementer.j2
```

## How they're used

Base prompts choose a language partial by name, falling back to `_default` when
no partial exists for the selected language:

```jinja
{% if target_language is not defined %}{% set target_language = "python" %}{% endif %}
...
{% include ["_language/" ~ target_language ~ "/implementer.j2",
            "_language/_default/implementer.j2"] ignore missing %}
```

`target_language` is passed in by the loop (the agent loop currently passes
`"python"`; the `language-agnostic-policy` branch will source it from the target
manifest). The `["…", "_default/…"] ignore missing` form renders the first
partial that exists, so adding a new language is *just* creating
`_language/<lang>/implementer.j2` — no code change, and unknown languages
degrade to the neutral `_default` prose rather than erroring.

## Conventions for adding a new language

1. Create `_language/<lang>/implementer.j2` with a self-contained snippet
   (a sentence or two) covering: project/manifest init, declaring
   dependencies, and how to run the server/scripts through the toolchain.
2. No document headers, no `{% block %}` — the parent template owns structure.
   The partial is dropped in where the base used to hardcode the tooling line.
3. Keep `_default` truly language-neutral; it is what every not-yet-modelled
   language falls back to.

## Scope

Only the **implementer-facing** tooling prose lives here today (the agent base
`implementer_prompt.j2` and `single_agent_round_prompt.j2`). Judge-side language
coupling (e.g. `uv run pytest`) is intentionally **not** abstracted yet — it is
entangled with protocol (`/health`) and domain (accuracy-checker) concerns in the
always-on correctness gates and is deferred to the domain-neutralization
follow-up. See `docs/design/prompt-abstractions-per-target.md`.
