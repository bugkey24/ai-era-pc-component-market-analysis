"""Robots.txt compliance guard (RFC 9309).

Every scraper consults this guard before fetching a URL: disallowed URLs
are skipped and logged, never requested. Resolution order per origin:

1. Local snapshot ``docs/compliance/robots/{platform}.robots.txt`` (offline,
   deterministic — used in tests and as an audit trail)
2. Live ``{origin}/robots.txt`` fetch
3. Unreachable → **fail-closed** (block) unless ``fail_open: true`` in config

Status-code semantics mirror RFC 9309 §2.3: 404 → site places no
restrictions; 401/403 → full block.

The matching engine implements RFC 9309 §2.2.2 directly rather than using
``urllib.robotparser``, which (a) matches against the URL path only,
dropping the query string, and (b) mishandles ``$``-anchored patterns.
Both deviations wrongly permitted URLs that platforms disallow.

Matching rules (RFC 9309 / Google semantics):
- ``*`` matches any sequence of characters (including ``/`` and ``?``)
- a trailing ``$`` anchors the pattern to the end of the URL
- the target is the URL **path + query string**
- the longest matching pattern wins; ties go to the least restrictive
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import requests

logger = logging.getLogger("scrapers.robots")


# ---------------------------------------------------------------------------
# RFC 9309 matching engine
# ---------------------------------------------------------------------------


@dataclass
class _Group:
    """One ``User-agent`` rule group."""

    agents: set[str] = field(default_factory=set)
    rules: list[tuple[bool, str]] = field(default_factory=list)  # (allowance, pattern)
    crawl_delay: float | None = None

    def matches_agent(self, user_agent: str) -> bool:
        ua = user_agent.lower()
        return any(a != "*" and ua.startswith(a) for a in self.agents)


def _pattern_to_regex(pattern: str) -> str:
    """Translate an RFC 9309 path pattern into an anchored regex."""
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    parts = (".*" if ch == "*" else re.escape(ch) for ch in body)
    return "^" + "".join(parts) + ("$" if anchored else "")


class RobotsFile:
    """Parsed robots.txt with RFC 9309 longest-match evaluation."""

    def __init__(self, text: str) -> None:
        self.groups: list[_Group] = []
        self._parse(text)

    def _parse(self, text: str) -> None:
        current: _Group | None = None
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            key, _, value = line.partition(":")
            key, value = key.strip().lower(), value.strip()

            if key == "user-agent":
                if current is None or current.rules or current.crawl_delay is not None:
                    # Rules (or a delay) already collected → start a new group
                    current = _Group()
                    self.groups.append(current)
                current.agents.add(value.lower())
            elif key == "disallow" and current is not None:
                if value:  # empty Disallow: means "allow everything"
                    current.rules.append((False, value))
            elif key == "allow" and current is not None:
                if value:
                    current.rules.append((True, value))
            elif key == "crawl-delay" and current is not None:
                try:
                    current.crawl_delay = float(value)
                except ValueError:
                    logger.warning("Unparseable Crawl-delay: %s", value)

    def _group_for(self, user_agent: str) -> _Group | None:
        """Most specific group wins (longest agent token); fall back to ``*``."""
        specific = [g for g in self.groups if g.matches_agent(user_agent)]
        if specific:
            return max(specific, key=lambda g: max(len(a) for a in g.agents))
        wildcard = [g for g in self.groups if "*" in g.agents]
        return wildcard[0] if wildcard else None

    def can_fetch(self, user_agent: str, url: str) -> bool:
        group = self._group_for(user_agent)
        if group is None:
            return True  # no applicable rules

        target = self._target(url)
        matches = [
            (allowance, len(pattern))
            for allowance, pattern in group.rules
            if re.match(_pattern_to_regex(pattern), target)
        ]
        if not matches:
            return True  # nothing matches → allowed

        # Longest pattern wins; ties go to the least restrictive (allow)
        longest = max(length for _, length in matches)
        return any(allowance for allowance, length in matches if length == longest)

    def crawl_delay(self, user_agent: str) -> float | None:
        group = self._group_for(user_agent)
        return group.crawl_delay if group else None

    @staticmethod
    def _target(url: str) -> str:
        """Evaluation target: URL path + query string (fragment dropped)."""
        parts = urlsplit(url)
        path = parts.path or "/"
        return f"{path}?{parts.query}" if parts.query else path


# ---------------------------------------------------------------------------
# Guard
# ---------------------------------------------------------------------------


class RobotsGuard:
    """Check fetch permissions against a platform's robots.txt rules."""

    def __init__(self, config: dict) -> None:
        self.enabled: bool = config.get("enabled", True)
        self.fail_open: bool = config.get("fail_open", False)
        self.snapshot_dir: Path = Path(config.get("snapshot_dir", "docs/compliance/robots"))
        self.timeout: int = config.get("timeout", 10)
        self._files: dict[str, RobotsFile | None] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        """Return True only if *url* may be fetched by *user_agent*."""
        if not self.enabled:
            return True

        origin = self._origin(url)
        robots = self._get_file(origin)
        if robots is None:
            return self.fail_open
        return robots.can_fetch(user_agent, url)

    def crawl_delay(self, url: str, user_agent: str = "*") -> float | None:
        """Return the origin's Crawl-delay for *user_agent*, if declared."""
        if not self.enabled:
            return None
        origin = self._origin(url)
        robots = self._get_file(origin)
        return robots.crawl_delay(user_agent) if robots else None

    # ------------------------------------------------------------------
    # File resolution (cached per origin)
    # ------------------------------------------------------------------

    def _get_file(self, origin: str) -> RobotsFile | None:
        if origin in self._files:
            return self._files[origin]

        robots = self._load_from_snapshot(origin)
        source = "snapshot"
        if robots is None:
            robots, source = self._load_from_network(origin)

        self._files[origin] = robots
        logger.info("robots.txt for %s resolved from %s", origin, source)
        return robots

    def _load_from_snapshot(self, origin: str) -> RobotsFile | None:
        """Match an origin like ``www.tokopedia.com`` to ``tokopedia.robots.txt``."""
        if not self.snapshot_dir.is_dir():
            return None
        host = origin.split("://", 1)[-1]
        for candidate in sorted(self.snapshot_dir.glob("*.robots.txt")):
            stem = candidate.name.removesuffix(".robots.txt")
            if stem == host or host.endswith("." + stem) or stem in host:
                return RobotsFile(candidate.read_text(encoding="utf-8"))
        return None

    def _load_from_network(self, origin: str) -> tuple[RobotsFile | None, str]:
        robots_url = f"{origin}/robots.txt"
        try:
            resp = requests.get(robots_url, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.error("robots.txt unreachable (%s): %s", robots_url, exc)
            return None, "unreachable"

        if resp.status_code == 200:
            return RobotsFile(resp.text), "network"
        if resp.status_code == 404:
            return RobotsFile(""), "network-404"  # no robots.txt → no restrictions
        if resp.status_code in (401, 403):
            return RobotsFile("User-agent: *\nDisallow: /"), "network-blocked"

        logger.error("robots.txt fetch got HTTP %d — treating as unreachable", resp.status_code)
        return None, "unreachable"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _origin(url: str) -> str:
        parts = urlsplit(url)
        return f"{parts.scheme}://{parts.netloc}"
