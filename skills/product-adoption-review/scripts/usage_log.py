"""Local, privacy-minimizing usage log for product-adoption-review."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 2
DEFAULT_THRESHOLD = 10
SEVERITIES = {"info", "minor", "major", "blocker"}
EVIDENCE_STATUSES = {"observed", "declared", "unverified", "contradictory"}
VERSION_SCOPES = {"current", "earlier", "unspecified", "not-applicable"}
TARGET_STAGES = {"assisted-pilot", "closed-beta", "public-beta", "stable-release"}
CATEGORIES = {
    "audience",
    "promise",
    "demo",
    "identity",
    "install",
    "compatibility",
    "discovery",
    "distribution",
    "measurement",
    "evidence",
}
ARTIFACT_KINDS = {
    "repository",
    "plugin",
    "application",
    "document",
    "release",
    "other",
}
SENSITIVE_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/]"),
    re.compile(r"/(?:Users|home)/", re.IGNORECASE),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\b(?:password|passwd|token|secret|api[_-]?key)\s*[:=]", re.IGNORECASE),
    re.compile(r"https?://\S+\?\S+"),
)
ISSUE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def state_dir() -> Path:
    override = os.environ.get("PRODUCT_ADOPTION_REVIEW_STATE_DIR")
    if override:
        return Path(override)
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Codex" / "product-adoption-review"
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "product-adoption-review"


def _safe_text(value: str, field: str) -> str:
    text = value.strip()
    if not text or len(text) > 500:
        raise ValueError(f"{field}: texte vide ou supérieur à 500 caractères")
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"{field}: contenu potentiellement sensible refusé")
    return text


def _install_id(root: Path) -> str:
    path = root / "install-id"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    value = str(uuid.uuid4())
    path.write_text(value + "\n", encoding="utf-8")
    return value


def project_id(project_root: str, root: Path) -> str:
    normalized = str(Path(project_root).resolve()).casefold()
    digest = hashlib.sha256(f"{_install_id(root)}\0{normalized}".encode()).hexdigest()
    return digest[:16]


@contextmanager
def _lock(root: Path, timeout: float = 5.0) -> Iterator[None]:
    lock = root / ".write.lock"
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError("journal verrouillé depuis plus de cinq secondes")
            time.sleep(0.05)
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def append_jsonl(path: Path, item: dict[str, Any]) -> None:
    payload = json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            if index == len(lines) - 1:
                break
            raise ValueError(f"JSONL invalide à la ligne {index + 1}: {path}") from None
        identity = str(item.get("usage_id") or item.get("review_id") or "")
        if identity and identity in seen:
            continue
        if identity:
            seen.add(identity)
        items.append(item)
    return items


def _issue_id(value: str) -> str:
    issue_id = _safe_text(value, "finding.issue_id")
    if not ISSUE_ID_PATTERN.fullmatch(issue_id):
        raise ValueError("finding.issue_id: utiliser un identifiant kebab-case stable")
    return issue_id


def parse_finding(value: str) -> dict[str, Any]:
    parts = value.split("|", 6)
    legacy = len(parts) == 3
    if legacy:
        category, severity, summary = parts
        safe_summary = _safe_text(summary, "finding.summary")
        issue_id = "legacy-" + hashlib.sha256(
            f"{category.casefold()}\0{safe_summary.casefold()}".encode()
        ).hexdigest()[:12]
        evidence_status = "unverified"
        version_scope = "unspecified"
        reproducible = False
    elif len(parts) == 7:
        (
            raw_issue_id,
            category,
            severity,
            evidence_status,
            version_scope,
            reproducible_text,
            summary,
        ) = parts
        issue_id = _issue_id(raw_issue_id)
        safe_summary = _safe_text(summary, "finding.summary")
        if reproducible_text not in {"true", "false"}:
            raise ValueError("finding.reproducible attendu: true ou false")
        reproducible = reproducible_text == "true"
    else:
        raise ValueError(
            "finding attendu: issue-id|categorie|severite|preuve|version|reproductible|resume"
        )
    if category not in CATEGORIES:
        raise ValueError(f"catégorie inconnue: {category}")
    if severity not in SEVERITIES:
        raise ValueError(f"sévérité inconnue: {severity}")
    if evidence_status not in EVIDENCE_STATUSES:
        raise ValueError(f"état de preuve inconnu: {evidence_status}")
    if version_scope not in VERSION_SCOPES:
        raise ValueError(f"portée de version inconnue: {version_scope}")
    return {
        "issue_id": issue_id,
        "category": _safe_text(category, "finding.category"),
        "severity": severity,
        "evidence_status": evidence_status,
        "version_scope": version_scope,
        "reproducible": reproducible,
        "summary": safe_summary,
        "legacy": legacy,
    }


def parse_improvement(value: str) -> dict[str, str]:
    parts = value.split("|", 2)
    if len(parts) != 3:
        raise ValueError("improvement attendu: issue-id|changement-minimal|test")
    issue_id, change, test = parts
    return {
        "issue_id": _issue_id(issue_id),
        "minimal_change": _safe_text(change, "improvement.minimal_change"),
        "regression_test": _safe_text(test, "improvement.regression_test"),
    }


def record(args: argparse.Namespace) -> dict[str, Any]:
    root = state_dir()
    root.mkdir(parents=True, exist_ok=True)
    if args.artifact_kind not in ARTIFACT_KINDS:
        raise ValueError(f"type de livrable inconnu: {args.artifact_kind}")
    findings = [parse_finding(value) for value in args.finding]
    improvements = [parse_improvement(value) for value in getattr(args, "improvement", [])]
    finding_ids = {finding["issue_id"] for finding in findings if not finding["legacy"]}
    improvement_ids = {improvement["issue_id"] for improvement in improvements}
    if improvement_ids - finding_ids:
        raise ValueError("improvement: identifiant absent des constats")
    if finding_ids - improvement_ids:
        raise ValueError("chaque constat v2 doit avoir un changement minimal et un test")
    target_stage = getattr(args, "target_stage", None)
    if target_stage not in TARGET_STAGES:
        raise ValueError(f"niveau de diffusion inconnu: {target_stage}")
    event = {
        "schema_version": SCHEMA_VERSION,
        "usage_id": str(uuid.uuid4()),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "project_id": project_id(args.project_root, root),
        "artifact_kind": args.artifact_kind,
        "trigger": _safe_text(args.trigger, "trigger"),
        "audience": _safe_text(args.audience, "audience"),
        "channel": _safe_text(args.channel, "channel"),
        "target_stage": target_stage,
        "findings": findings,
        "improvements": improvements,
        "decisions": [_safe_text(value, "decision") for value in args.decision],
        "verification": [_safe_text(value, "verification") for value in args.verification],
        "outcome": _safe_text(args.outcome, "outcome"),
        "completed": bool(args.completed),
    }
    with _lock(root):
        append_jsonl(root / "usage.jsonl", event)
    return event


def status(threshold: int = DEFAULT_THRESHOLD) -> dict[str, int | bool | str]:
    root = state_dir()
    usage = [item for item in read_jsonl(root / "usage.jsonl") if item.get("completed") is True]
    reviews = read_jsonl(root / "review-events.jsonl")
    reported = max((int(item.get("end_count", 0)) for item in reviews), default=0)
    pending = max(0, len(usage) - reported)
    return {
        "state_dir": str(root),
        "total_completed": len(usage),
        "reported_completed": reported,
        "pending_completed": pending,
        "threshold": threshold,
        "review_due": pending >= threshold,
        "next_review_at": reported + threshold,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--project-root", required=True)
    record_parser.add_argument("--artifact-kind", required=True, choices=sorted(ARTIFACT_KINDS))
    record_parser.add_argument("--trigger", required=True)
    record_parser.add_argument("--audience", required=True)
    record_parser.add_argument("--channel", required=True)
    record_parser.add_argument("--target-stage", required=True, choices=sorted(TARGET_STAGES))
    record_parser.add_argument("--finding", action="append", default=[])
    record_parser.add_argument("--improvement", action="append", default=[])
    record_parser.add_argument("--decision", action="append", default=[])
    record_parser.add_argument("--verification", action="append", default=[])
    record_parser.add_argument("--outcome", required=True)
    record_parser.add_argument("--completed", action="store_true")
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = record(args) if args.command == "record" else status(args.threshold)
    except (OSError, TimeoutError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
