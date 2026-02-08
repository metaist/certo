"""URL probe - config, probe, and fact. Extends shell probe."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self

from certo.probe.core import Fact, ProbeContext, ProbeResult, generate_id
from certo.probe.shell import ShellConfig, ShellProbe


@dataclass
class UrlConfig(ShellConfig):
    """Configuration for a URL probe."""

    kind: str = "url"
    url: str = ""
    cache_ttl: int = 86400  # seconds (default: 1 day)

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        """Parse a URL probe config from TOML data."""
        config = cls(
            kind="url",
            id=data.get("id", ""),
            status=data.get("status", "enabled"),
            url=data.get("url", ""),
            cache_ttl=data.get("cache_ttl", 86400),
            cmd=data.get("cmd", ""),
            exit_code=data.get("exit_code", 0),
            matches=data.get("matches", []),
            not_matches=data.get("not_matches", []),
            timeout=data.get("timeout", 60),
        )
        if not config.id and config.url:
            config.id = generate_id("k", f"url:{config.url}")
        return config

    def to_toml(self) -> str:
        """Serialize to TOML."""
        lines = [
            "[[probes]]",
            f'id = "{self.id}"',
            'kind = "url"',
        ]
        if self.status != "enabled":
            lines.append(f'status = "{self.status}"')
        escaped_url = self.url.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'url = "{escaped_url}"')
        if self.cache_ttl != 86400:
            lines.append(f"cache_ttl = {self.cache_ttl}")
        if self.cmd:
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


class UrlProbe(ShellProbe):
    """Probe that fetches URL then pipes to shell."""

    kind_name = "url"

    def run(self, ctx: ProbeContext, rule: Any, config: Any) -> ProbeResult:
        """Fetch URL and pipe to shell command."""
        url = getattr(config, "url", "")
        if not url:
            return ProbeResult(
                rule_id=rule.id if rule else "",
                rule_text=rule.text if rule else "",
                passed=False,
                message="URL probe has no url",
                kind="url",
            )

        cache_ttl = getattr(config, "cache_ttl", 86400)
        timeout = getattr(config, "timeout", 60)

        # Cache path
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
        cache_dir = ctx.spec_path.parent / "cache" / "url"
        cache_file = cache_dir / f"{url_hash}.txt"
        cache_meta = cache_dir / f"{url_hash}.meta"

        # Check cache
        content: str | None = None
        from_cache = False
        if not ctx.no_cache and cache_file.exists() and cache_meta.exists():
            try:
                cached_time = float(cache_meta.read_text().split("\n")[0])
                if time.time() - cached_time < cache_ttl:
                    content = cache_file.read_text()
                    from_cache = True
            except (ValueError, OSError):
                pass

        # Fetch if not cached
        if content is None:
            if ctx.offline:
                return ProbeResult(
                    rule_id=rule.id if rule else "",
                    rule_text=rule.text if rule else "",
                    passed=True,
                    message="skipped (offline, no cache)",
                    kind="url",
                    skipped=True,
                    skip_reason="offline mode, no cached response",
                )

            try:
                import urllib.request

                with urllib.request.urlopen(url, timeout=timeout) as response:
                    fetched = response.read().decode("utf-8")

                # Cache it
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(fetched)
                cache_meta.write_text(f"{time.time()}\n{url}")
                content = fetched
            except Exception as e:
                return ProbeResult(
                    rule_id=rule.id if rule else "",
                    rule_text=rule.text if rule else "",
                    passed=False,
                    message=f"Failed to fetch URL: {e}",
                    kind="url",
                )

        # At this point content is guaranteed to be set
        assert content is not None

        # If no command, just verify URL was fetchable
        cmd = getattr(config, "cmd", "")
        if not cmd:
            msg = "URL fetched successfully"
            if from_cache:
                msg += " (cached)"
            return ProbeResult(
                rule_id=rule.id if rule else "",
                rule_text=rule.text if rule else "",
                passed=True,
                message=msg,
                kind="url",
                output=content[:1000] if len(content) > 1000 else content,
            )

        # Run shell command with content as stdin
        result = self.run_with_stdin(ctx, rule, config, stdin=content)
        if from_cache and "(cached)" not in result.message:
            result.message += " (cached)"
        return result


@dataclass
class UrlFact(Fact):
    """Fact from a URL probe."""

    kind: str = "url"
    status_code: int = 0
    body: str = ""
    json: dict[str, Any] | list[Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = super().to_dict()
        d["status_code"] = self.status_code
        d["body"] = self.body
        if self.json is not None:
            d["json"] = self.json
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        timestamp = data.get("timestamp", "")
        return cls(
            probe_id=data["probe_id"],
            kind=data.get("kind", "url"),
            timestamp=datetime.fromisoformat(timestamp) if timestamp else None,
            duration=data.get("duration", 0.0),
            probe_hash=data.get("probe_hash", ""),
            status_code=data.get("status_code", 0),
            body=data.get("body", ""),
            json=data.get("json"),
        )


# Aliases for backward compatibility during transition
UrlCheck = UrlConfig
UrlRunner = UrlProbe
UrlEvidence = UrlFact
