"""Shell command check - config, runner, and evidence."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Self

from certo.check.core import Check, CheckContext, CheckResult, Evidence, generate_id


@dataclass
class ShellCheck(Check):
    """A check that runs a shell command."""

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
        """Parse a shell check from TOML data."""
        check = cls(
            kind="shell",
            id=data.get("id", ""),
            status=data.get("status", "enabled"),
            cmd=data.get("cmd", ""),
            exit_code=data.get("exit_code", 0),
            matches=data.get("matches", []),
            not_matches=data.get("not_matches", []),
            timeout=data.get("timeout", 60),
        )
        if not check.id and check.cmd:
            check.id = generate_id("k", f"shell:{check.cmd}")
        return check

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[claims.checks]]",
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


class ShellRunner:
    """Runner for shell command checks."""

    kind_name = "shell"

    def run(self, ctx: CheckContext, claim: Any, check: Any) -> CheckResult:
        """Run a shell command and verify the result."""
        return self.run_with_stdin(ctx, claim, check, stdin=None)

    def run_with_stdin(
        self,
        ctx: CheckContext,
        claim: Any,
        check: Any,
        stdin: str | None = None,
    ) -> CheckResult:
        """Run a shell command with optional stdin."""
        cmd = getattr(check, "cmd", "")
        if not cmd:
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message="Shell check has no command",
                kind=self.kind_name,
            )

        timeout = getattr(check, "timeout", 60)
        exit_code = getattr(check, "exit_code", 0)
        matches = getattr(check, "matches", [])
        not_matches = getattr(check, "not_matches", [])

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
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message=f"Command timed out after {timeout}s",
                kind=self.kind_name,
            )
        except Exception as e:
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message=f"Command failed: {e}",
                kind=self.kind_name,
            )

        output = result.stdout + result.stderr

        if result.returncode != exit_code:
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message=f"Expected exit code {exit_code}, got {result.returncode}",
                kind=self.kind_name,
                output=output,
            )

        for pattern in matches:
            if not re.search(pattern, output):
                return CheckResult(
                    claim_id=claim.id,
                    claim_text=claim.text,
                    passed=False,
                    message=f"Pattern not found: {pattern}",
                    kind=self.kind_name,
                    output=output,
                )

        for pattern in not_matches:
            if re.search(pattern, output):
                return CheckResult(
                    claim_id=claim.id,
                    claim_text=claim.text,
                    passed=False,
                    message=f"Forbidden pattern found: {pattern}",
                    kind=self.kind_name,
                    output=output,
                )

        return CheckResult(
            claim_id=claim.id,
            claim_text=claim.text,
            passed=True,
            message=f"{self.kind_name.title()} check passed",
            kind=self.kind_name,
            output=output,
        )


@dataclass
class ShellEvidence(Evidence):
    """Evidence from a shell command check."""

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
            check_id=data["check_id"],
            kind=data.get("kind", "shell"),
            timestamp=datetime.fromisoformat(timestamp) if timestamp else None,
            duration=data.get("duration", 0.0),
            check_hash=data.get("check_hash", ""),
            exit_code=data.get("exit_code", 0),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            json=data.get("json"),
        )
