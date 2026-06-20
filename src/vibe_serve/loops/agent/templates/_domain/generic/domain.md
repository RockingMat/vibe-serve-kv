# Generic (no domain context)

**Use for:** a target that needs no special background knowledge or review gates
beyond the task statement, the modality contract, and the run's pass criteria.

The role files (`implementer.j2`, `judge.j2`, `single_agent.j2`) are intentionally
empty, so the base prompts render with **no** domain-specific prose injected. This
is the neutral baseline and the recommended starting point to copy when authoring
your own domain — see `../README.md`.
