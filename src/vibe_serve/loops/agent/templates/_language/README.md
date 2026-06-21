# Languages — choosing the implementation toolchain

A **language** bundles the implementation-language context the agents need: the
package manager and how to run code for the implementer, optionally a build/lint
gate for the judge. It's the answer to *"what language and toolchain is this
built in?"* — kept separate from both the neutral prompt skeleton and the
(orthogonal) `--domain` problem-space context.

Language packs use the **same single-file mechanism as domain packs** (see
`../_domain/README.md`); they differ only in directory (`_language/`) and
injection prefix (`{{ language_<role> }}`). The two axes compose: a run is
`--domain <what> --language <how>`, and each pack's sections inject at separate
points in the same base prompt.

Pick one with `--language` (agent loop):

```bash
vibe-serve --outer-loop agent --language python ...        # default (uv toolchain)
vibe-serve --outer-loop agent --language generic ...       # no tooling prose
vibe-serve --outer-loop agent --language ./my-lang.md ...  # your own (a path)
```

`--language` accepts either a **built-in name** (a `<name>.md` next to this file)
or a **path** to your own `.md` file anywhere on disk. Built-ins:

| Language  | What it does |
|-----------|--------------|
| `python`  | The default. The `uv` toolchain: `uv init` / `uv add` / `uv run`. Reproduces vibeserve's original (Python-only) tooling prose. |
| `generic` | Empty — no tooling prose injected. The neutral baseline; copy it to start your own (e.g. Rust + `cargo`, Go + `go`). |

## Anatomy of a language file

Identical to a domain file (the format is shared). The injected content lives
under `##` headings named for the agent roles; everything before the first role
heading is human documentation and is ignored by the loop.

```markdown
# My language
**Use for:** a one-line description of when to reach for this toolchain.

## implementer        ← injected as {{ language_implementer }}
Package manager, how to run scripts, idioms the builder must follow.

## judge              ← injected as {{ language_judge }} (optional)
A language-specific gate, e.g. "`cargo clippy` must pass with no warnings."

## single_agent       ← injected as {{ language_single_agent }} (optional)
Combined builder+reviewer tooling for the single-agent ablation.
```

Rules (same as domains):

- **The heading is the address.** Only the exact names `## implementer`,
  `## judge`, `## single_agent` delimit a section; your body may use its own
  `##` sub-headings.
- **A missing section injects nothing** for that role.
- **`## single_agent` is optional** — derived by concatenating `## implementer`
  and `## judge` when omitted. The built-in `python` pack ships an explicit one
  only because its single-agent phrasing is terser than the implementer's.
- Section bodies are rendered with Jinja and receive the same run-context
  variables as domain sections (`modality`, `reference_path`, `bench_path`,
  `accuracy_checker_path`, `runtime_notes`).

## How to author your own

1. Copy `generic.md` to a new file (in-repo `_language/<name>.md`, or anywhere on
   disk you'll point `--language` at).
2. Edit the title and "use for…" line.
3. Fill `## implementer` (package manager, run command, idioms). Optionally add
   `## judge` (a build/lint gate) and `## single_agent`.
4. Run `vibe-serve --outer-loop agent --language <name-or-path> ...`.

No code change — a new built-in language is just a new `.md` file here; a private
one is just a path you pass.

## Scope

Language packs cover **implementation toolchain + language-specific gates**.
They are deliberately orthogonal to:

- **Domain** (`--domain`) — the problem-space knowledge and correctness gates.
  A `python` language pack and an `llm-serving` domain pack inject independently.
- **Profiling** (`--profiler`) — GPU capture (nsys/torch) is selected separately
  and rendered by the profiler prompts.
