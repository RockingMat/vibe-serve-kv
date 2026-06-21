# Generic (no language tooling)

**Use for:** a target whose language/toolchain needs no special instructions
beyond what the task, modality contract, and domain pack already supply — or
when you want the agent to pick its own toolchain.

This language pack injects **no** prose into the base prompts — there are no role
sections below, so the neutral base prompts render unchanged. It is the
recommended starting point to copy when authoring your own language pack: add
`## implementer`, optionally `## judge` (a lint/build gate), and optionally
`## single_agent`. See `./README.md`.
