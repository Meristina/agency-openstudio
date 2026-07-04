"""Source verification for mission deliverables.

Pure stdlib gate: extract cited URLs, optionally HEAD-probe them, and assemble the
per-cycle report consumed by the mission loop.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as _FuturesTimeout
from dataclasses import dataclass
import ipaddress
import re
import socket
import ssl
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener


MAX_URLS_PER_CYCLE = 50
_MAX_WORKERS = 8
_PROBE_TIMEOUT = 5
_CYCLE_TIMEOUT = 60
# THE canonical cited-URL matcher — shared with cli_engine._extract_sources so the
# dossier's `sources` list and the verifier can never drift apart (a URL the dossier
# records but the gate never sees would hole the exact trust surface this gate
# hardens). A URL starts with an alphanumeric character and stops at whitespace and
# the markdown delimiters that wrap a link — ( ) [ ] < > " ' | ` .
SOURCE_URL_RE = re.compile(r"https?://[A-Za-z0-9][^\s<>()\[\]\"'|`]*")
_SOURCE_URL_RE = SOURCE_URL_RE  # internal alias


@dataclass(frozen=True)
class VerificationConfig:
    min_sources: int = 3
    resolve: bool = False

    def __post_init__(self) -> None:
        if self.min_sources < 0:
            raise ValueError("min_sources must be >= 0")


def coerce_config(value) -> VerificationConfig:
    if isinstance(value, VerificationConfig):
        return value
    if not isinstance(value, dict):
        return VerificationConfig()
    raw_min = value.get("min_sources", 3)
    if isinstance(raw_min, bool):   # bool is an int subclass: True would silently become 1
        raw_min = 3
    return VerificationConfig(
        min_sources=int(raw_min),
        resolve=bool(value.get("resolve", False)),
    )


def extract_urls(text: str) -> list[str]:
    """Cited URLs in ``text``, de-duplicated in first-seen order, trailing sentence
    punctuation stripped. The one extraction used by both the verifier and the
    dossier's ``sources`` field (via cli_engine._extract_sources)."""
    seen = {}
    for raw in SOURCE_URL_RE.findall(text or ""):
        url = raw.rstrip(".,;:!?")
        if url:
            seen.setdefault(url, None)
    return list(seen)


_urls = extract_urls  # internal alias


def extract_sources(dept_outputs: dict, delivered: str) -> list[dict]:
    records: dict[str, dict] = {}
    for dept, output in (dept_outputs or {}).items():
        for url in _urls(str(output)):
            record = records.setdefault(url, {"url": url, "depts": []})
            if dept not in record["depts"]:
                record["depts"].append(dept)
    for url in _urls(delivered or ""):
        records.setdefault(url, {"url": url, "depts": []})
    return list(records.values())


def _policy_refusal(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return "non-https"
    host = (parsed.hostname or "").lower().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        return "localhost"
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return None
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        return "private-address"
    return None


_USER_AGENT = "agency-openstudio-source-verifier/1.0"


class _RedirectRefused(URLError):
    """A redirect hop pointed outside the probe's security policy."""


class _PolicyRedirectHandler(HTTPRedirectHandler):
    """Re-check every redirect hop against the same pre-fetch policy as the original
    URL (https-only, no private/loopback/link-local hosts — Constitution VI), and keep
    the follow-up request a HEAD so no body is ever fetched."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        refusal = _policy_refusal(newurl)
        if refusal:
            raise _RedirectRefused(f"redirect refused: {refusal}")
        # S310 (audit URL scheme): newurl just passed _policy_refusal — https-only,
        # no private/loopback hosts — so no file:/ftp:/custom scheme can reach here.
        return Request(newurl, method="HEAD", headers={"User-Agent": _USER_AGENT})  # noqa: S310


_OPENER = build_opener(
    HTTPSHandler(context=ssl.create_default_context()), _PolicyRedirectHandler()
)

# Sentinel code for a policy-refused redirect: classified `unresolved` by probe_url —
# a chain leaving the secure public web can never be a verifiable public source.
_POLICY_REDIRECT = -1


def _head_probe(url: str) -> tuple[Optional[int], str]:
    # S310 (audit URL scheme): probe_url calls _policy_refusal BEFORE this function —
    # only https URLs to public hosts reach the opener, and every redirect hop is
    # re-checked by _PolicyRedirectHandler above.
    req = Request(url, method="HEAD", headers={"User-Agent": _USER_AGENT})  # noqa: S310
    try:
        with _OPENER.open(req, timeout=_PROBE_TIMEOUT) as response:  # noqa: S310
            return response.getcode(), f"HTTP {response.getcode()}"
    except _RedirectRefused as exc:
        return _POLICY_REDIRECT, f"policy: {exc.reason}"
    except HTTPError as exc:
        return exc.code, f"HTTP {exc.code}"
    except (URLError, socket.timeout, OSError) as exc:
        return None, str(getattr(exc, "reason", exc)).lower()


def probe_url(url: str) -> tuple[str, str, str]:
    refusal = _policy_refusal(url)
    if refusal:
        return "unresolved", f"policy: {refusal}", "policy"

    code, detail = _head_probe(url)
    if code == _POLICY_REDIRECT:
        return "unresolved", detail, "policy"
    if code is None:
        low = detail.lower()
        if any(s in low for s in ("dns", "name", "nodename", "getaddrinfo", "not known")):
            return "unresolved", detail, "nxdomain"
        return "ambiguous", detail, "connection"
    if 200 <= code < 400:
        return "resolved", detail, "http"
    if code in (404, 410):
        return "unresolved", detail, "http"
    return "ambiguous", detail, "http"


def _offline_sources(records: list[dict], detail: str = "resolution not enabled") -> list[dict]:
    return [{**r, "status": "unverified", "detail": detail} for r in records[:MAX_URLS_PER_CYCLE]]


def verify_cycle(
    iteration: int,
    route: list[str],
    dept_outputs: dict,
    delivered: str,
    config: VerificationConfig,
    *,
    cache: Optional[dict[str, tuple[str, str, str]]] = None,
    missing: Optional[list[str]] = None,
) -> dict:
    config = coerce_config(config)
    records = extract_sources(dept_outputs, delivered)
    cache = cache if cache is not None else {}

    if not config.resolve:
        truncated = max(0, len(records) - MAX_URLS_PER_CYCLE)
        sources = _offline_sources(records)
    else:
        visible, truncated = _fair_cap(records)
        sources = _resolve_sources(visible, cache)
        if sources and all(s.get("_kind") == "connection" for s in sources):
            sources = [{k: v for k, v in {**s, "status": "unverified", "detail": "network unavailable"}.items() if k != "_kind"} for s in sources]
        else:
            sources = [{k: v for k, v in s.items() if k != "_kind"} for s in sources]

    degraded = bool(sources) and all(s["status"] == "unverified" and s["detail"] == "network unavailable" for s in sources)
    # Strict counting when probes actually ran: only sources checked this cycle count
    # toward a department's minimum (resolved + ambiguous). Offline/degraded cycles
    # fall back to counting every cited URL — nothing was checkable, so nothing can be
    # held against the department. This closes the padding hole where citations beyond
    # the probe cap would count without ever being checked.
    per_dept = _per_dept(route, dept_outputs, sources, config.min_sources,
                         strict=config.resolve and not degraded)
    checkable = sum(1 for s in sources if s["status"] in {"resolved", "ambiguous", "unresolved"})
    resolved = sum(1 for s in sources if s["status"] == "resolved")
    rate = None if (not config.resolve or degraded or checkable == 0) else resolved / checkable
    ok = all(v["ok"] for v in per_dept.values())
    return {
        "iteration": iteration,
        "ok": ok,
        "resolve": config.resolve,
        "sources": sources,
        "per_dept": per_dept,
        "rate": rate,
        "missing": list(missing or []),
        "truncated": truncated,
    }


def _fair_cap(records: list[dict]) -> tuple[list[dict], int]:
    """Cap the probe list at MAX_URLS_PER_CYCLE with a round-robin over the first-citing
    department (synthesis-only URLs form their own pool), so one department's URL flood
    cannot starve another department's sources out of the probe budget — which matters
    now that only checked sources count toward a department's minimum."""
    if len(records) <= MAX_URLS_PER_CYCLE:
        return records, 0
    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for record in records:
        key = (record.get("depts") or ["(synthesis)"])[0]
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(record)
    picked: list[dict] = []
    rank = 0
    while len(picked) < MAX_URLS_PER_CYCLE:
        progressed = False
        for key in order:
            group = groups[key]
            if rank < len(group):
                picked.append(group[rank])
                progressed = True
                if len(picked) == MAX_URLS_PER_CYCLE:
                    break
        if not progressed:
            break
        rank += 1
    return picked, len(records) - len(picked)


def _resolve_sources(records: list[dict], cache: dict[str, tuple[str, str, str]]) -> list[dict]:
    out: list[Optional[dict]] = [None] * len(records)
    pending = {}
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        for index, record in enumerate(records):
            url = record["url"]
            if url in cache:
                status, detail, kind = cache[url]
                out[index] = {**record, "status": status, "detail": detail, "_kind": kind}
            else:
                pending[pool.submit(probe_url, url)] = (index, record)
        try:
            iterator = as_completed(pending, timeout=_CYCLE_TIMEOUT)
            for fut in iterator:
                index, record = pending[fut]
                status, detail, kind = fut.result()
                cache[record["url"]] = (status, detail, kind)
                out[index] = {**record, "status": status, "detail": detail, "_kind": kind}
        except _FuturesTimeout:
            pass
        for fut, (index, record) in pending.items():
            if out[index] is None:
                fut.cancel()
                # Deliberately NOT cached: a clamp-skip describes this cycle's time
                # budget, not the URL — a later cycle must be free to probe it.
                status, detail, kind = "unverified", "not probed - cap/time limit", "timeout"
                out[index] = {**record, "status": status, "detail": detail, "_kind": kind}
    return [r for r in out if r is not None]


def _per_dept(route: list[str], dept_outputs: dict, sources: list[dict], minimum: int,
              *, strict: bool = False) -> dict:
    result = {}
    if strict:
        # Probes ran: a source counts for a department only if it was checked this
        # cycle and came back resolved or ambiguous (benefit of the doubt — Q4).
        good_by_dept = {dept: 0 for dept in route}
        for source in sources:
            if source["status"] in {"resolved", "ambiguous"}:
                for dept in source.get("depts", []):
                    if dept in good_by_dept:
                        good_by_dept[dept] += 1
        for dept in route:
            counted = good_by_dept.get(dept, 0)
            result[dept] = {"counted": counted, "min": minimum, "ok": minimum == 0 or counted >= minimum}
        return result
    # Offline / degraded: nothing was checkable, so every cited URL counts (minus any
    # policy-refused unverifiable citation surfaced by a prior cache entry).
    bad_by_dept = {dept: 0 for dept in route}
    for source in sources:
        if source["status"] in {"unresolved", "unverifiable"}:
            for dept in source.get("depts", []):
                if dept in bad_by_dept:
                    bad_by_dept[dept] += 1
    for dept in route:
        extracted = len(_urls(str((dept_outputs or {}).get(dept, ""))))
        counted = max(0, extracted - bad_by_dept.get(dept, 0))
        result[dept] = {"counted": counted, "min": minimum, "ok": minimum == 0 or counted >= minimum}
    return result


__all__ = [
    "MAX_URLS_PER_CYCLE",
    "SOURCE_URL_RE",
    "VerificationConfig",
    "coerce_config",
    "extract_sources",
    "extract_urls",
    "probe_url",
    "verify_cycle",
]
