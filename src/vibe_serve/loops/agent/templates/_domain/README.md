# Domains — pointing vibeserve at your problem space

A **domain** bundles the cross-cutting context the agents need for whatever
you're building: the background knowledge the implementer must read, the
correctness/performance/integrity gates the judge must enforce, and the same for
the single-agent ablation. It's the answer to *"what kind of system is this, and
what does 'good' mean here?"* — kept separate from the neutral prompt skeleton.

Pick one with `--domain` (agent loop):

```bash
vibe-serve --outer-loop agent --domain llm-serving ...   # default
vibe-serve --outer-loop agent --domain generic ...       # no domain context
vibe-serve --outer-loop agent --domain ./my-domain ...   # your own (a path)
```

`--domain` accepts either a **built-in name** (a directory under this `_domain/`)
or a **path** to your own domain directory anywhere on disk. Built-ins:

| Domain        | What it does |
|---------------|--------------|
| `llm-serving` | The default. LLM inference server context: the `serving-systems` skill/references, `/model` weights, the accuracy + benchmark + reward-hack judge gates. |
| `generic`     | Empty — no domain prose injected. The neutral baseline; copy it to start your own. |

## Anatomy of a domain pack

A domain is just a directory with up to four files. All are optional except
`domain.md`; a missing role file means "inject nothing for that role".

```
my-domain/
├── domain.md          ← human label + one-line "use for…" description (required)
├── implementer.j2     ← what the builder must know/read for this domain
├── judge.j2           ← what the reviewer must check for this domain
└── single_agent.j2    ← combined builder+reviewer context (single-agent ablation)
```

The `.j2` files are dropped into the base prompts at a single, clearly-labelled
injection point per role (`{{ domain_implementer }}`, `{{ domain_judge }}`,
`{{ domain_single_agent }}`). Write normal Markdown prose with your own `##`
section headers — the base template owns the surrounding structure (task, pass
criteria, workspace, output contract); your file owns the domain content.

### Variables available to a role file

Role files are rendered with Jinja, so you can branch on the run's context. The
useful variables:

| Variable | Meaning |
|----------|---------|
| `modality` | The `--modality` value (e.g. `text_generation`). |
| `reference_path` | Path to the reference implementation. |
| `bench_path` | Benchmark harness dir, if a benchmark is attached (else falsy). |
| `accuracy_checker_path` | Accuracy checker dir, if attached (else falsy). |
| `runtime_notes` | Runtime-environment notes for the round. |

Example (`judge.j2`):

```jinja
## Correctness gates

1. `pytest` passes.
{% if bench_path is defined and bench_path %}
2. Run `{{ bench_path }}/benchmark.py` and confirm it succeeds.
{% endif %}
```

## How to author your own

1. Copy `generic/` to a new directory (in-repo `_domain/<name>/`, or anywhere on
   disk you'll point `--domain` at).
2. Edit `domain.md` with a title and a one-line "use for…" line.
3. Fill `implementer.j2` (what to read / what "done" means here) and `judge.j2`
   (what to check). Leave a file empty to inject nothing for that role.
4. Optionally fill `single_agent.j2` for the `--inner-loop single-agent` ablation.
5. Run `vibe-serve --outer-loop agent --domain <name-or-path> ...`.

That's it — no code change. A new built-in domain is just a new directory here; a
private domain is just a path you pass.

## Scope

Domains cover **implementer + judge (+ single-agent) context**. Two adjacent
concerns are deliberately *not* part of a domain pack:

- **Language/tooling** (e.g. "use `uv`/`pytest`") lives in the base prompt and is
  the job of the (separate) language-selection work, not the domain.
- **Profiling** (nsys/torch GPU capture) is selected by `--profiler` and rendered
  by the profiler prompts, not the domain. Domain-specific profiling is future
  work tied to pluggable profilers.
