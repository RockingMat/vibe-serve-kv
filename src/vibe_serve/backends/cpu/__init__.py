"""CPU backend: no GPU, local execution only.

For CPU-bound targets (KV stores, networking servers) there is no GPU to
select or monitor: ``selected_device`` stays ``None``, ``make_monitor``
returns ``None``, and ``reselect_device`` is a no-op. Like the Metal
backend it runs only via ``SandboxKind.LOCAL`` (the simple loop's local
runner); ``make_sandbox`` raises a clear error for ``DOCKER`` / ``MODAL``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from deepagents.backends import LocalShellBackend
from deepagents.backends.sandbox import BaseSandbox

from vibe_serve.backends.base import (
    ContentionMonitor,
    ModalOptions,
    SandboxKind,
    SetupFn,
)
from vibe_serve.constants import ComputeBackend


class CpuBackend:
    """CPU-only backend (local execution only) — all hardware hooks are no-ops."""

    name = ComputeBackend.CPU
    profiler_kind = "torch"

    def __init__(
        self,
        log_dir: Path,
        *,
        log: Callable[[str], None] | None = None,
        image: str | None = None,
    ) -> None:
        self.log_dir = Path(log_dir)
        self._lprint = log or print
        # No GPU to pick — kept for protocol parity with other backends
        # (e.g. _RunContext reads ``selected_device``).
        self.selected_device = None

    # -- ComputeBackendImpl protocol -----------------------------------------

    def make_sandbox(
        self,
        kind: SandboxKind,
        *,
        host_workspace: str,
        log_path: Path | str | None,
        bind_mounts: list[tuple[str, str, bool]] | None = None,
        passthrough_paths: list[str] | None = None,
        extra_env: dict[str, str] | None = None,
        extra_init_commands: list[str] | None = None,
        setup_fns: list[SetupFn] | None = None,
        modal_options: ModalOptions | None = None,
    ) -> BaseSandbox:
        if kind is not SandboxKind.LOCAL:
            raise ValueError(
                f"cpu backend only supports local execution; "
                f"SandboxKind.{kind.name} is unavailable (there is no GPU to "
                f"pass through to a Docker/Modal container)."
            )
        return LocalShellBackend(
            root_dir=host_workspace,
            virtual_mode=True,
            inherit_env=True,
            env=dict(extra_env or {}),
        )

    def make_monitor(self, log_dir: Path) -> ContentionMonitor | None:
        return None

    def reselect_device(self) -> None:
        return None
