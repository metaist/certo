"""LLM probe - config, probe, and fact."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Self

from certo.probe.core import Fact, ProbeConfig, ProbeContext, ProbeResult, generate_id


@dataclass
class LLMConfig(ProbeConfig):
    """Configuration for an LLM probe."""

    kind: str = "llm"
    id: str = ""
    status: str = "enabled"
    files: list[str] = field(default_factory=list)
    prompt: str | None = None

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse an LLM probe config from TOML data."""
        config = cls(
            kind="llm",
            id=data.get("id", ""),
            status=data.get("status", "enabled"),
            files=data.get("files", []),
            prompt=data.get("prompt"),
        )
        if not config.id and config.files:
            config.id = generate_id("k", f"llm:{','.join(config.files)}")
        return config

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[probes]]",
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


class LLMProbe:
    """Probe that uses LLM for verification."""

    def run(self, ctx: ProbeContext, rule: Any, config: Any) -> ProbeResult:
        """Verify using LLM.

        If rule is provided, verifies rule.text against files.
        If rule is None (top-level probe), uses config.prompt or skips.
        """
        from certo.llm.provider import LLMError, NoAPIKeyError
        from certo.llm.verify import FileMissingError, FileTooLargeError, verify_concern

        rule_id = rule.id if rule else ""
        rule_text = rule.text if rule else ""
        probe_id = getattr(config, "id", "") or rule_id

        # Determine what to verify
        text_to_verify = rule_text or getattr(config, "prompt", "")
        if not text_to_verify:
            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=False,
                message="LLM probe has no rule text or prompt to verify",
                kind="llm",
            )

        files = getattr(config, "files", [])
        if not files:
            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=False,
                message="LLM probe has no files specified",
                kind="llm",
            )

        if ctx.offline:
            evidence_dir = ctx.spec_path.parent / "evidence"
            evidence_file = evidence_dir / f"{probe_id}.json" if probe_id else None

            if evidence_file and evidence_file.exists():
                import json

                try:
                    evidence = json.loads(evidence_file.read_text())
                    msg = evidence.get("message", "cached result")
                    return ProbeResult(
                        rule_id=rule_id,
                        rule_text=rule_text,
                        passed=evidence.get("passed", False),
                        message=f"{msg} (cached)",
                        kind="llm",
                        output=evidence.get("reasoning", ""),
                    )
                except (json.JSONDecodeError, OSError):
                    pass

            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=True,
                message="skipped (offline mode)",
                kind="llm",
                skipped=True,
                skip_reason="offline mode",
            )

        try:
            result = verify_concern(
                concern_id=probe_id,
                claim=text_to_verify,
                context_patterns=files,
                project_root=ctx.project_root,
                no_cache=ctx.no_cache,
                model=ctx.model,
            )

            if probe_id:  # pragma: no branch - always true since we set it above
                import json

                evidence_dir = ctx.spec_path.parent / "evidence"
                evidence_dir.mkdir(parents=True, exist_ok=True)
                evidence_file = evidence_dir / f"{probe_id}.json"
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

            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=result.passed,
                message=message,
                kind="llm",
                output=result.explanation,
            )

        except NoAPIKeyError:
            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=True,
                message="skipped (no API key)",
                kind="llm",
                skipped=True,
                skip_reason="no API key configured",
            )
        except FileMissingError as e:
            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=False,
                message=f"File not found: {e}",
                kind="llm",
            )
        except FileTooLargeError as e:
            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=False,
                message=f"File too large: {e}",
                kind="llm",
            )
        except LLMError as e:
            return ProbeResult(
                rule_id=rule_id,
                rule_text=rule_text,
                passed=False,
                message=f"LLM error: {e}",
                kind="llm",
            )


@dataclass
class LLMFact(Fact):
    """Fact from an LLM probe."""

    kind: str = "llm"
    verdict: bool = False
    reasoning: str = ""
    model: str = ""
    tokens: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = super().to_dict()
        d["verdict"] = self.verdict
        d["reasoning"] = self.reasoning
        d["model"] = self.model
        d["tokens"] = self.tokens
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        timestamp = data.get("timestamp", "")
        return cls(
            probe_id=data["probe_id"],
            kind=data.get("kind", "llm"),
            timestamp=datetime.fromisoformat(timestamp) if timestamp else None,
            duration=data.get("duration", 0.0),
            probe_hash=data.get("probe_hash", ""),
            verdict=data.get("verdict", False),
            reasoning=data.get("reasoning", ""),
            model=data.get("model", ""),
            tokens=data.get("tokens", {}),
        )
