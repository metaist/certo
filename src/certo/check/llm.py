"""LLM check - config and runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

from certo.check.core import Check, CheckContext, CheckResult, generate_id


@dataclass
class LLMCheck(Check):
    """A check that uses LLM verification."""

    kind: str = "llm"
    id: str = ""
    status: str = "enabled"
    files: list[str] = field(default_factory=list)
    prompt: str | None = None

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse an LLM check from TOML data."""
        check = cls(
            kind="llm",
            id=data.get("id", ""),
            status=data.get("status", "enabled"),
            files=data.get("files", []),
            prompt=data.get("prompt"),
        )
        if not check.id and check.files:
            check.id = generate_id("k", f"llm:{','.join(check.files)}")
        return check

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[claims.checks]]",
            f'id = "{self.id}"',
            'kind = "llm"',
        ]
        if self.status != "enabled":
            lines.append(f'status = "{self.status}"')
        if self.files:
            lines.append(f"files = {self.files}")
        if self.prompt:
            escaped = self.prompt.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'prompt = "{escaped}"')
        return "\n".join(lines)


class LLMRunner:
    """Runner for LLM-based checks."""

    def run(self, ctx: CheckContext, claim: Any, check: Any) -> CheckResult:
        """Verify a claim using LLM."""
        from certo.llm.provider import LLMError, NoAPIKeyError
        from certo.llm.verify import FileMissingError, FileTooLargeError, verify_concern

        if not claim.text:
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message="Claim has no text to verify",
                kind="llm",
            )

        files = getattr(check, "files", [])
        if not files:
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message="LLM check has no files specified",
                kind="llm",
            )

        if ctx.offline:
            evidence_dir = ctx.spec_path.parent / "evidence"
            check_id = getattr(check, "id", "")
            evidence_file = evidence_dir / f"{check_id}.json" if check_id else None

            if evidence_file and evidence_file.exists():
                import json

                try:
                    evidence = json.loads(evidence_file.read_text())
                    msg = evidence.get("message", "cached result")
                    return CheckResult(
                        claim_id=claim.id,
                        claim_text=claim.text,
                        passed=evidence.get("passed", False),
                        message=f"{msg} (cached)",
                        kind="llm",
                        output=evidence.get("reasoning", ""),
                    )
                except (json.JSONDecodeError, OSError):
                    pass

            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=True,
                message="skipped (offline mode)",
                kind="llm",
                skipped=True,
                skip_reason="offline mode",
            )

        try:
            check_id = getattr(check, "id", "") or claim.id
            result = verify_concern(
                concern_id=check_id,
                claim=claim.text,
                context_patterns=files,
                project_root=ctx.project_root,
                no_cache=ctx.no_cache,
                model=ctx.model,
            )

            if check_id:
                import json

                evidence_dir = ctx.spec_path.parent / "evidence"
                evidence_dir.mkdir(parents=True, exist_ok=True)
                evidence_file = evidence_dir / f"{check_id}.json"
                evidence_file.write_text(
                    json.dumps(
                        {
                            "passed": result.passed,
                            "message": result.explanation,
                            "reasoning": result.explanation,
                            "model": result.model,
                        },
                        indent=2,
                    )
                )

            message = result.explanation
            if result.cached:
                message = f"{message} (cached)"

            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=result.passed,
                message=message,
                kind="llm",
                output=result.explanation,
            )

        except NoAPIKeyError:
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=True,
                message="skipped (no API key)",
                kind="llm",
                skipped=True,
                skip_reason="no API key configured",
            )
        except FileMissingError as e:
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message=f"File not found: {e}",
                kind="llm",
            )
        except FileTooLargeError as e:
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message=f"File too large: {e}",
                kind="llm",
            )
        except LLMError as e:
            return CheckResult(
                claim_id=claim.id,
                claim_text=claim.text,
                passed=False,
                message=f"LLM error: {e}",
                kind="llm",
            )
