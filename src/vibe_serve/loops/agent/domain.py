"""Domain packs — pluggable, per-problem-space prompt context.

A *domain* tells the agent loop what kind of system it is building and what
"good" means there: the background knowledge the implementer must read, and the
correctness/performance/integrity gates the judge must enforce. It is selected
with ``--domain`` and bundled as a directory of small Jinja partials, one per
role:

    _domain/<name>/
    ├── domain.md          ← human label + "use for…" description
    ├── implementer.j2     ← injected as {{ domain_implementer }}
    ├── judge.j2           ← injected as {{ domain_judge }}
    └── single_agent.j2    ← injected as {{ domain_single_agent }}

The neutral base prompts carry zero domain prose; they render the selected pack's
role file into a single ``{{ domain_<role> }}`` variable (the same
variable-injection pattern :class:`vibe_serve.prompts.ComputeBackendFragment`
uses for backend fragments). A missing role file injects nothing.

``--domain`` accepts a **built-in name** (a directory under
``loops/agent/templates/_domain/``) or a **path** to a user's own domain
directory anywhere on disk, so users can author their own without touching
vibeserve. See ``loops/agent/templates/_domain/README.md`` for the authoring
guide.
"""

from __future__ import annotations

from pathlib import Path

from vibe_serve.prompts import render_template

DEFAULT_DOMAIN = "llm-serving"

# The roles a domain pack can contribute to, in (role file stem) form. Each maps
# to a ``{{ domain_<role> }}`` injection point in the corresponding base prompt.
DOMAIN_ROLES: tuple[str, ...] = ("implementer", "judge", "single_agent")

_BUILTIN_DOMAINS_DIR = Path(__file__).resolve().parent / "templates" / "_domain"


def builtin_domains() -> list[str]:
    """Names of the built-in domain packs (directories under ``_domain/``)."""
    if not _BUILTIN_DOMAINS_DIR.is_dir():
        return []
    return sorted(
        p.name for p in _BUILTIN_DOMAINS_DIR.iterdir() if p.is_dir()
    )


def resolve_domain(spec: str) -> Path:
    """Resolve a ``--domain`` value to a domain-pack directory.

    ``spec`` is either a path to a domain directory (used as-is) or the name of a
    built-in pack under ``_domain/``. Raises ``ValueError`` with the list of
    built-ins if neither resolves.
    """
    candidate = Path(spec).expanduser()
    if candidate.is_dir():
        return candidate.resolve()

    builtin = _BUILTIN_DOMAINS_DIR / spec
    if builtin.is_dir():
        return builtin

    raise ValueError(
        f"Unknown domain {spec!r}. Pass a built-in name "
        f"({', '.join(builtin_domains())}) or a path to a domain directory."
    )


def render_domain_section(domain_dir: Path, role: str, **context: object) -> str:
    """Render a domain pack's ``<role>.j2`` partial, or ``""`` if absent/empty.

    The partial is rendered with ``context`` (e.g. ``modality``, ``bench_path``,
    ``accuracy_checker_path``) so domain authors can branch on the run. Leading
    and trailing blank lines are stripped — the base template owns the spacing
    around the ``{{ domain_<role> }}`` injection point.
    """
    role_file = domain_dir / f"{role}.j2"
    if not role_file.is_file():
        return ""
    return render_template(
        f"{role}.j2", template_dir=domain_dir, **context
    ).strip("\n")
