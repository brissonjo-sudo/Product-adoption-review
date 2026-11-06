"""Generate a local review for each complete batch of usage events."""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from usage_log import (
    DEFAULT_THRESHOLD,
    _lock,
    _safe_text,
    append_jsonl,
    read_jsonl,
    state_dir,
)


SEVERITY_RANK = {"info": 0, "minor": 1, "major": 2, "blocker": 3}
DECISIONS = {"accepted", "rejected"}


def _finding_issue_id(finding: dict[str, Any]) -> str:
    if finding.get("issue_id"):
        return str(finding["issue_id"])
    legacy = f"{finding.get('category', '')}\0{finding.get('summary', '')}".casefold()
    return "legacy-" + hashlib.sha256(legacy.encode()).hexdigest()[:12]


def _most_common(values: list[str], fallback: str) -> str:
    return Counter(values).most_common(1)[0][0] if values else fallback


def _group_findings(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "categories": [],
            "severities": [],
            "summaries": [],
            "projects": [],
            "uses": set(),
            "evidence_statuses": [],
            "version_scopes": [],
            "target_stages": [],
            "reproducible": False,
            "reproducible_blocker": False,
            "changes": [],
            "tests": [],
        }
    )
    for event_index, event in enumerate(events):
        improvements = {
            item.get("issue_id"): item
            for item in event.get("improvements", [])
            if item.get("issue_id")
        }
        for finding in event.get("findings", []):
            issue_id = _finding_issue_id(finding)
            group = grouped[issue_id]
            group["uses"].add(event_index)
            group["categories"].append(str(finding.get("category", "unknown")))
            group["severities"].append(str(finding.get("severity", "info")))
            group["summaries"].append(str(finding.get("summary", "")))
            group["projects"].append(str(event.get("project_id", "unknown")))
            group["evidence_statuses"].append(
                str(finding.get("evidence_status", "unverified"))
            )
            group["version_scopes"].append(str(finding.get("version_scope", "unspecified")))
            group["target_stages"].append(str(event.get("target_stage", "unspecified")))
            group["reproducible"] = group["reproducible"] or bool(
                finding.get("reproducible", False)
            )
            group["reproducible_blocker"] = group["reproducible_blocker"] or (
                finding.get("severity") == "blocker"
                and bool(finding.get("reproducible", False))
            )
            improvement = improvements.get(issue_id)
            if improvement:
                group["changes"].append(str(improvement.get("minimal_change", "")))
                group["tests"].append(str(improvement.get("regression_test", "")))
    result = []
    for issue_id, group in grouped.items():
        severity = max(
            group["severities"], key=lambda value: SEVERITY_RANK.get(value, -1)
        )
        result.append(
            {
                "issue_id": issue_id,
                "category": _most_common(group["categories"], "unknown"),
                "severity": severity,
                "summary": _most_common(group["summaries"], "Résumé indisponible"),
                "occurrences": len(group["uses"]),
                "projects": len(set(group["projects"])),
                "evidence_statuses": sorted(set(group["evidence_statuses"])),
                "version_scopes": sorted(set(group["version_scopes"])),
                "target_stages": sorted(set(group["target_stages"])),
                "reproducible": group["reproducible"],
                "reproducible_blocker": group["reproducible_blocker"],
                "minimal_change": _most_common(
                    [value for value in group["changes"] if value], "À définir"
                ),
                "regression_test": _most_common(
                    [value for value in group["tests"] if value], "À définir"
                ),
            }
        )
    return sorted(
        result,
        key=lambda item: (
            -item["projects"],
            -item["occurrences"],
            -SEVERITY_RANK.get(item["severity"], -1),
            item["issue_id"],
        ),
    )


def _candidate_findings(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in _group_findings(events)
        if (item["occurrences"] >= 3 and item["projects"] >= 2)
        or item["reproducible_blocker"]
    ]


def _render(
    batch_id: str,
    start: int,
    end: int,
    events: list[dict[str, Any]],
    history: list[dict[str, Any]],
) -> str:
    categories = Counter(
        finding["category"] for event in events for finding in event.get("findings", [])
    )
    severities = Counter(
        finding["severity"] for event in events for finding in event.get("findings", [])
    )
    evidence_statuses = Counter(
        finding.get("evidence_status", "unverified")
        for event in events
        for finding in event.get("findings", [])
    )
    target_stages = Counter(event.get("target_stage", "unspecified") for event in events)
    grouped = _group_findings(events)
    batch_ids = {
        _finding_issue_id(finding) for event in events for finding in event.get("findings", [])
    }
    # Seuils évalués sur tout l'historique : un motif réparti sur deux lots reste promouvable.
    candidates = [
        item for item in _candidate_findings(history) if item["issue_id"] in batch_ids
    ]
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
        f"- États de preuve : {json.dumps(evidence_statuses, ensure_ascii=False, sort_keys=True)}",
        f"- Niveaux de diffusion : {json.dumps(target_stages, ensure_ascii=False, sort_keys=True)}",
        "",
        "Ces nombres décrivent les constats sélectionnés pour le journal. Ils ne représentent",
        "ni le nombre de projets affectés, ni un taux d'échec de la population auditée.",
        "",
        "## Motifs observés",
        "",
    ]
    for item in grouped:
        lines.append(
            f"- `{item['issue_id']}` — {item['occurrences']} occurrence(s), "
            f"{item['projects']} projet(s), sévérité maximale `{item['severity']}`"
        )
    lines.extend(["", "## Candidats à l'amélioration officielle", ""])
    if not candidates:
        lines.append("Aucun motif n'atteint le seuil de promotion dans ce lot.")
    else:
        for candidate in candidates:
            lines.extend(
                [
                    f"### `{candidate['issue_id']}`",
                    "",
                    f"- Catégorie / sévérité : `{candidate['category']}` / `{candidate['severity']}`",
                    f"- Occurrences / projets (cumul depuis l'usage 1) : "
                    f"{candidate['occurrences']} / {candidate['projects']}",
                    f"- Reproductible : {'oui' if candidate['reproducible'] else 'non établi'}",
                    f"- États de preuve : {', '.join(candidate['evidence_statuses'])}",
                    f"- Portées de version : {', '.join(candidate['version_scopes'])}",
                    f"- Niveaux de diffusion : {', '.join(candidate['target_stages'])}",
                    f"- Observation représentative : {candidate['summary']}",
                    f"- Changement minimal proposé : {candidate['minimal_change']}",
                    f"- Test de non-régression proposé : {candidate['regression_test']}",
                    "",
                ]
            )
    lines.extend(
        [
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
    report = _render(batch_id, start, end, batch, completed[:end])
    report_path.write_text(report, encoding="utf-8", newline="\n")
    review_event = {
        "schema_version": 2,
        "review_id": str(uuid.uuid4()),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "batch_id": batch_id,
        "start_count": start,
        "end_count": end,
        "status": "proposed",
        "report": report_path.relative_to(root).as_posix(),
    }
    with _lock(root):
        append_jsonl(root / "review-events.jsonl", review_event)
    return {"generated": True, "report": str(report_path), "batch_id": batch_id}


def decide(batch_id: str, decision: str, note: str) -> dict[str, Any]:
    """Enregistre la décision humaine sur un bilan, sans décaler le compteur."""
    if decision not in DECISIONS:
        raise ValueError(f"décision attendue : {', '.join(sorted(DECISIONS))}")
    safe_note = _safe_text(note, "note")
    root = state_dir()
    with _lock(root):
        reviews = read_jsonl(root / "review-events.jsonl")
        if not any(item.get("batch_id") == batch_id and "end_count" in item for item in reviews):
            raise ValueError(f"bilan inconnu : {batch_id}")
        event = {
            "schema_version": 2,
            "review_id": str(uuid.uuid4()),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "batch_id": batch_id,
            "status": decision,
            "note": safe_note,
        }
        append_jsonl(root / "review-events.jsonl", event)
    return {"decided": True, "batch_id": batch_id, "status": decision}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    parser.add_argument("--decide", metavar="LOT", help="identifiant du bilan, ex. 0001-0010")
    parser.add_argument("--status", choices=sorted(DECISIONS))
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    try:
        if args.decide:
            if not args.status:
                raise ValueError("--decide exige --status")
            result = decide(args.decide, args.status, args.note)
        else:
            result = generate(args.threshold)
    except (OSError, TimeoutError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
