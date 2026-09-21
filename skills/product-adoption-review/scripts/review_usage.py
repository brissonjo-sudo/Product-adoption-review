"""Generate a local review for each complete batch of usage events."""

from __future__ import annotations

import argparse
import json
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from usage_log import DEFAULT_THRESHOLD, _lock, append_jsonl, read_jsonl, state_dir


def _candidate_findings(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    occurrences: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for event in events:
        for finding in event.get("findings", []):
            key = (finding["category"], finding["severity"], finding["summary"])
            occurrences[key].append(event["project_id"])
    candidates = []
    for (category, severity, summary), projects in occurrences.items():
        count = len(projects)
        project_count = len(set(projects))
        if severity == "blocker" or (count >= 3 and project_count >= 2):
            candidates.append(
                {
                    "category": category,
                    "severity": severity,
                    "summary": summary,
                    "occurrences": count,
                    "projects": project_count,
                }
            )
    return sorted(candidates, key=lambda item: (item["severity"] != "blocker", -item["occurrences"]))


def _render(batch_id: str, start: int, end: int, events: list[dict[str, Any]]) -> str:
    categories = Counter(
        finding["category"] for event in events for finding in event.get("findings", [])
    )
    severities = Counter(
        finding["severity"] for event in events for finding in event.get("findings", [])
    )
    candidates = _candidate_findings(events)
    lines = [
        f"# Bilan d'usage {batch_id}",
        "",
        f"Usages terminés couverts : {start} à {end}.",
        f"Projets pseudonymisés distincts : {len({event['project_id'] for event in events})}.",
        "",
        "## Répartition",
        "",
        f"- Catégories : {json.dumps(categories, ensure_ascii=False, sort_keys=True)}",
        f"- Sévérités : {json.dumps(severities, ensure_ascii=False, sort_keys=True)}",
        "",
        "## Candidats à l'amélioration officielle",
        "",
    ]
    if not candidates:
        lines.append("Aucun motif n'atteint le seuil de promotion dans ce lot.")
    else:
        for candidate in candidates:
            lines.append(
                f"- [{candidate['severity']}] {candidate['category']} — {candidate['summary']} "
                f"({candidate['occurrences']} occurrences, {candidate['projects']} projets)"
            )
    lines.extend(
        [
            "",
            "## Décision humaine requise",
            "",
            "Pour chaque candidat : conserver dans le journal, enrichir une référence, proposer une règle, ou rejeter.",
            "Aucun fichier du skill officiel n'a été modifié par ce bilan.",
            "",
        ]
    )
    return "\n".join(lines)


def generate(threshold: int = DEFAULT_THRESHOLD) -> dict[str, Any]:
    if threshold < 1:
        raise ValueError("threshold doit être positif")
    root = state_dir()
    root.mkdir(parents=True, exist_ok=True)
    completed = [item for item in read_jsonl(root / "usage.jsonl") if item.get("completed") is True]
    reviews = read_jsonl(root / "review-events.jsonl")
    reported = max((int(item.get("end_count", 0)) for item in reviews), default=0)
    if len(completed) - reported < threshold:
        return {"generated": False, "pending": len(completed) - reported, "threshold": threshold}
    batch = completed[reported : reported + threshold]
    start = reported + 1
    end = reported + threshold
    batch_id = f"{start:04d}-{end:04d}"
    report_dir = root / "reviews"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{batch_id}.md"
    report_path.write_text(_render(batch_id, start, end, batch), encoding="utf-8", newline="\n")
    review_event = {
        "schema_version": 1,
        "review_id": str(uuid.uuid4()),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "batch_id": batch_id,
        "start_count": start,
        "end_count": end,
        "status": "proposed",
        "report": str(report_path),
    }
    with _lock(root):
        append_jsonl(root / "review-events.jsonl", review_event)
    return {"generated": True, "report": str(report_path), "batch_id": batch_id}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()
    try:
        result = generate(args.threshold)
    except (OSError, TimeoutError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
