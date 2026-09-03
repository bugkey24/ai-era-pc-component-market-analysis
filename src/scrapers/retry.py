"""Shared retry-with-exponential-backoff for HTTP fetching.

Used by both the product and review scraper base classes. Retries
connection errors and timeouts, plus 5xx and 429 — client errors (4xx)
are raised immediately since backing off cannot heal a bad URL or a WAF.
"""

from __future__ import annotations

import logging
import time

import requests


def request_with_retry(
    url: str,
    headers: dict,
    timeout: int,
    retry_count: int,
    delay: float,
    logger: logging.Logger,
) -> str:
    """GET *url* with exponential backoff; returns response text.

    Raises the last exception after *retry_count* exhausted attempts.
    """
    last_exc: Exception | None = None
    for attempt in range(retry_count):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            # 4xx (except 429) will not heal with backoff — fail fast
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                resp.raise_for_status()
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            last_exc = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status is not None and 400 <= status < 500 and status != 429:
                raise  # non-retryable client error
            backoff = delay * (2**attempt)
            logger.warning(
                "Attempt %d/%d failed (%s) — backing off %.1fs",
                attempt + 1,
                retry_count,
                exc,
                backoff,
            )
            time.sleep(backoff)
    assert last_exc is not None  # for type-checkers
    raise last_exc
