# Design: Per-target prompt abstractions (neutral base + additive hints)

**Status:** Draft / for review
**Branch:** `prompt-abstractions-per-target`
**Related:** `language-agnostic-policy` (depends on this — see *Relationship to the other branch*)
**Scope of this PR series:** prompt/template refactor only. No new runtime behavior, no language
selection mechanism (that is the sibling branch). kv-store specifics are deferred.

---

## Context / Problem

VibeServe adapts the inner loop (Implementer → Accuracy Judge → Performance Evaluator) to a
domain via **modalities** — template directories selected by `--modality` and pulled in with a
Jinja `{% include %}` at the top of each base prompt
(`src/vibe_serve/loops/agent/templates/implementer_prompt.j2:1-2`).

The mechanism is sound, but the **base templates are not neutral**: they bake in LLM-serving and
Python assumptions. The implementer base references `/model`, `uv`, and `VibeServeModel`
(`implementer_prompt.j2:22-24`); the profiler base assumes nsys/torch; the judge base assumes an
HTTP `/health` endpoint and a model interface.

Because the base is opinionated, every non-LLM modality must **negate** it rather than extend it.
`_modality/kv_store/implementer.j2:3` literally says *"This is NOT an LLM serving task… Ignore any
references to those in the base template,"* and the kv_store judge/profiler do the same. This is
fragile: any edit to the base's LLM/Python prose silently desyncs every negating modality, and
new targets (queues, KV stores, …) start by fighting the framework instead of describing
themselves.

We want to **invert the polarity**: a domain-neutral base skeleton, with LLM-serving, Python, and
(later) language specifics expressed as **additive layers** that supplement — never contradict —
the base.

## Goals

- Base implementer/judge/profiler templates contain **zero** domain- or language-specific prose.
- Each modality layer is **purely additive**: it adds its contract, never says "ignore the base."
- LLM-serving + Python specifics move into `_modality/text_generation/` (and reusable fragments),
  so `text_generation` is just another modality, not the privileged default baked into the base.
- Introduce a `_language/<lang>/` hint layer parallel to `_modality/<name>/`, so the sibling
  `language-agnostic-policy` branch has a clean seam to plug language hints into.
- The rendered prompt for the existing `text_generation` (Python) path stays **semantically
  identical** — this is a refactor, not a behavior change.

## Non-goals

- No machine-readable run contract / target manifest (sibling branch).
- No `allowed_languages` config, no profiler pluggability, no sandbox/toolchain work.
- No retrofit of the `plain` loop's separate template tree (see *Open decisions*).
- No new modality content for kv-store or any new target (deferred).

## Current coupling (evidence)

| Location | Coupling |
|---|---|
| `loops/agent/templates/implementer_prompt.j2:22-24` | `/model` path, `uv` package manager, `VibeServeModel` baked into base |
| `loops/agent/templates/judge_prompt.j2` | `/health` HTTP endpoint + model-interface assumptions in base review criteria |
| `loops/agent/templates/profiler_prompt_{nsys,torch}.j2` | base assumes GPU/torch/nsys profiling workflow |
| `loops/agent/templates/_modality/kv_store/implementer.j2:3` | negates the base ("ignore the base template") |
| `loops/agent/templates/_modality/kv_store/{judge,profiler}.j2` | negate base `/health` + nsys/torch |
| `src/vibe_serve/prompts.py:95-186` | `ComputeBackendFragment` — the **clean** pattern to emulate: per-backend text injected as Jinja **variables** (`{{ device_dtype }}`, `{{ profiling_workflow }}`, `{{ judge_device_correctness }}`) from `src/vibe_serve/templates/_backend/{cuda,metal}/` |
| `cli.py:37-45` | `_MODALITIES` tuple is the modality registry (hardcoded) |
| `loops/plain/templates/_serving_constraints.j2` | separate template tree, no modality system, deeply PyTorch/`VibeServeModel`-coupled |

Two composition mechanisms already coexist in the repo, and we keep both with a clear rule:
- **`{% include %}`** for whole *sections* that vary by modality/language (the current modality
  pattern).
- **Variable injection** (`{{ name }}`) for *substitutions* that vary by backend (the
  `ComputeBackendFragment` pattern, `prompts.py:95-186`, convention documented in
  `src/vibe_serve/templates/_backend/README.md`).

## Proposed design

### 1. Strip the base to a neutral skeleton

`implementer_prompt.j2`, `judge_prompt.j2`, `profiler_prompt_*.j2`, and
`single_agent_round_prompt.j2` keep only domain-neutral structure: task statement, pass criteria,
workspace location, progress tracking, skill-reading discipline, feedback handling, and the
`{% include "_modality/" ~ modality ~ "/<role>.j2" %}` seam.

All `/model`, `uv`, `VibeServeModel`, FastAPI/`/health`, and torch/nsys prose is **removed from
the base** and relocated (next step).

### 2. Demote LLM/Python specifics into `_modality/text_generation/`

Everything the base currently assumes about LLM serving and Python moves into the
`text_generation` modality layer (`_modality/text_generation/{implementer,judge,profiler}.j2`).
After this, `text_generation` is a normal modality and `_modality/kv_store/*` can **delete its
"ignore the base" preambles** because there is nothing left to ignore.

### 3. Add a `_language/<lang>/` hint layer (seam only in this branch)

Create `_language/` parallel to `_modality/`. The base templates gain a second include after the
modality include:

```jinja
{% include "_modality/" ~ modality ~ "/" ~ role ~ ".j2" %}
{% include "_language/" ~ target_language ~ "/" ~ role ~ ".j2" %}
```

In **this** branch we ship `_language/python/` (the current Python tooling prose, factored out of
the base) and a `_language/_default/` fallback (generic "use your language's standard tooling").
`target_language` defaults to `"python"` so behavior is unchanged. The sibling branch supplies the
real value (from the target manifest) and additional language dirs.

### 4. Where injection happens

- **Agent / evolve / openevolve loops** render via the bare `render_template(...)` helper
  (`prompts.py:79-92`; call sites e.g. `loops/agent/loop.py`), so `modality` and
  `target_language` are passed as explicit kwargs there. This matches how `modality` already
  flows today.
- **Plain loop** uses the `Prompt` class (`prompts.py:189-235`) with auto-injected backend
  fragments. If/when the plain loop is brought in scope, mirror the backend-fragment mechanism;
  out of scope here (see *Open decisions*).

### Resulting layering (per role)

```
base skeleton (neutral)
  └─ {% include _modality/<modality>/<role>.j2 %}   ← domain contract (additive)
  └─ {% include _language/<lang>/<role>.j2 %}        ← language tooling (additive)
  └─ {{ backend fragments }}                         ← device/profiler substitutions (existing)
```

## Backward compatibility

The default render — `modality="text_generation"`, `target_language="python"`, CUDA backend —
must produce a **semantically identical** prompt to today. Achieved by relocating prose, not
rewriting it, and defaulting `target_language` to `"python"`.

## Open decisions (record, don't resolve here)

1. **Loop scope.** Which loops get the neutral-base treatment: `agent`+`evolve`(+`openevolve`)
   vs `agent`-only vs all four. `plain` has its own template tree with no modality system and is
   the expensive retrofit. *Leaning: agent + evolve/openevolve (they already share the
   `_modality` include); leave `plain` Python-LLM-only initially.*
2. **`_language/` vs fragment variables.** Whether language hints are `{% include %}` sections
   (chosen above for symmetry with modality) or `ComputeBackendFragment`-style variables. Sections
   are simpler for prose; variables compose better for short substitutions. *Leaning: sections,
   with variables reserved for the run/health substitutions the sibling branch introduces.*
3. **Modality registry.** Keep the hardcoded `_MODALITIES` tuple (`cli.py:37-45`) or move to
   filesystem discovery of `_modality/*`. Out of scope but worth noting.

## Verification

- **Golden prompt snapshots (primary gate):** render implementer/judge/profiler/perf_eval prompts
  for `text_generation` (and, once it exists cleanly, `kv_store`) at the pre-refactor commit;
  assert exact match for the Python `text_generation` path after the refactor, and reviewed-diff
  for any reflowed text. Add these snapshots as tests so the refactor is provably behavior-stable.
- **Existing examples unchanged:** a `text_generation` example (e.g. `examples/Llama-3-8B`) runs
  with default flags and produces the same prompts/behavior.
- **Negation gone:** `grep -rn "ignore .*base template" src/vibe_serve/loops/*/templates` returns
  nothing after the refactor.

## Relationship to the other branch

This branch is the **foundation**. `language-agnostic-policy` injects per-target run/build/health
commands and real `target_language` values into the seams created here. Land this first; rebase
`language-agnostic-policy` on top. Both branch independently from `main` so each is a standalone PR.

## Out of scope / later

- Target manifest, language selection, profiler pluggability → `language-agnostic-policy`.
- Plain-loop modality/language retrofit.
- kv-store modality cleanup (revisit once the neutral base lands).
