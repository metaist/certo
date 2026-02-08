"""Shell command probe - config, probe, and fact."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Self

from certo.probe.core import Fact, ProbeConfig, ProbeContext, ProbeResult, generate_id


@dataclass
class ShellConfig(ProbeConfig):
    """Configuration for a shell command probe."""

    kind: str = "shell"
    id: str = ""
    status: str = "enabled"
    cmd: str = ""
    exit_code: int = 0
    matches: list[str] = field(default_factory=list)
    not_matches: list[str] = field(default_factory=list)
    timeout: int = 60

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a shell probe config from TOML data."""
        config = cls(
            kind="shell",
            id=data.get("id", ""),
            status=data.get("status", "enabled"),
            cmd=data.get("cmd", ""),
            exit_code=data.get("exit_code", 0),
            matches=data.get("matches", []),
            not_matches=data.get("not_matches", []),
            timeout=data.get("timeout", 60),
        )
        if not config.id and config.cmd:
            config.id = generate_id("k", f"shell:{config.cmd}")
        return config

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[probes]]",
            f'id = "{self.id}"',
            'kind = "shell"',
        ]
        if self.status != "enabled":
            lines.append(f'status = "{self.status}"')
        escaped_cmd = self.cmd.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'cmd = "{escaped_cmd}"')
        if self.exit_code != 0:
            lines.append(f"exit_code = {self.exit_code}")
        if self.matches:
            lines.append(f"matches = {self.matches}")
        if self.not_matches:
            lines.append(f"not_matches = {self.not_matches}")
        if self.timeout != 60:
            lines.append(f"timeout = {self.timeout}")
        return "\n".join(lines)


class ShellProbe:
    """Probe that runs shell commands."""

    kind_name = "shell"

    def run(self, ctx: ProbeContext, rule: Any, config: Any) -> ProbeResult:
        """Run a shell command and verify the result."""
        return self.run_with_stdin(ctx, rule, config, stdin=None)

    def run_with_stdin(
        self,
        ctx: ProbeContext,
        rule: Any,
        config: Any,
        stdin: str | None = None,
    ) -> ProbeResult:
        """Run a shell command with optional stdin."""
        rule_id = rule.id if rule else ""
        rule_text = rule.text if rule else ""

        cmd = getattr(config, "cmd", "")
        if not cmd:
            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=False,
                message="Shell probe has no command",
                kind=self.kind_name,
            )

        timeout = getattr(config, "timeout", 60)
        exit_code = getattr(config, "exit_code", 0)
        matches = getattr(config, "matches", [])
        not_matches = getattr(config, "not_matches", [])

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=ctx.root,
                input=stdin,
            )
        except subprocess.TimeoutExpired:
            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=False,
                message=f"Command timed out after {timeout}s",
                kind=self.kind_name,
            )
        except Exception as e:
            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=False,
                message=f"Command failed: {e}",
                kind=self.kind_name,
            )

        output = result.stdout + result.stderr

        if result.returncode != exit_code:
            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=False,
                message=f"Expected exit code {exit_code}, got {result.returncode}",
                kind=self.kind_name,
                output=output,
            )

        for pattern in matches:
            if not re.search(pattern, output):
                return ProbeResult(
                    rule_id=rule_id,
                    rule_text=rule_text,
                    passed=False,
                    message=f"Pattern not found: {pattern}",
                    kind=self.kind_name,
                    output=output,
                )

        for pattern in not_matches:
            if re.search(pattern, output):
                return ProbeResult(
                    rule_id=rule_id,
                    rule_text=rule_text,
                    passed=False,
                    message=f"Forbidden pattern found: {pattern}",
                    kind=self.kind_name,
                    output=output,
                )

        return ProbeResult(
            rule_id=rule_id,
            rule_text=rule_text,
            passed=True,
            message=f"{self.kind_name.title()} probe passed",
            kind=self.kind_name,
            output=output,
        )


@dataclass
class ShellFact(Fact):
    """Fact from a shell command probe."""

    kind: str = "shell"
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    json: dict[str, Any] | list[Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = super().to_dict()
        d["exit_code"] = self.exit_code
        d["stdout"] = self.stdout
        d["stderr"] = self.stderr
        if self.json is not None:
            d["json"] = self.json
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        timestamp = data.get("timestamp", "")
        return cls(
            probe_id=data["probe_id"],
            kind=data.get("kind", "shell"),
            timestamp=datetime.fromisoformat(timestamp) if timestamp else None,
            duration=data.get("duration", 0.0),
            probe_hash=data.get("probe_hash", ""),
            exit_code=data.get("exit_code", 0),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            json=data.get("json"),
        )
