"""Judge calibration: export a sheet for the user to label, then compare.

Usage:
    python -m evals.calibration export --run-id baseline-v0 [--n 10] [--force]
    python -m evals.calibration compare --run-id baseline-v0

Export picks items deterministically (round-robin across difficulties, by case id)
and writes evals/results/<run_id>/calibration.md: each item shows the dossier facts
and a blank "Your call" line; the judge's verdicts sit in a reference section at the
end so the sheet can be labelled blind. Compare parses the filled sheet and reports
agreement on the grounded yes/no call plus the mean absolute score difference.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from evals.summarize import RESULTS_DIR, load_label_meta, load_run

CALL_RE = re.compile(
    r"\*\*Your call:\*\*\s*(yes|no)\b[^\n]*?score[: ]*([1-5])", re.IGNORECASE
)
CALL_BLANK = "**Your call:** _yes or no; 1-5; note_"


def pick_items(run_id: str, n: int = 10, root: Path = RESULTS_DIR) -> list[str]:
    """Deterministic selection, most informative first: judge-flagged items (not grounded
    or score <= 4) lead; the rest round-robin across clean/boundary/failure, by case id."""
    meta = load_label_meta()
    run = load_run(run_id, root)
    flagged: list[str] = []
    groups: dict[str, list[str]] = {"clean": [], "boundary": [], "failure": []}
    for case_id, item in sorted(run.items()):
        if item["judge"] is None or case_id not in meta:
            continue
        judge = item["judge"]
        if not judge["grounded"] or judge["score"] <= 4:
            flagged.append(case_id)
        else:
            groups.setdefault(meta[case_id]["metadata"]["difficulty"], []).append(case_id)
    picked: list[str] = flagged[:n]
    while len(picked) < n and any(groups.values()):
        for name in list(groups):
            if groups[name] and len(picked) < n:
                picked.append(groups[name].pop(0))
    return picked


def _dossier_block(dossier: dict) -> str:
    lines = [f"Status: {dossier.get('status')}", ""]
    for check in dossier.get("checks", []):
        missing = (
            f" | missing: {', '.join(check['missing_items'])}"
            if check.get("missing_items")
            else ""
        )
        citations = ", ".join(check.get("citations") or [])
        lines.append(
            f"- {check.get('check_id')}: {check.get('outcome')} - "
            f"{check.get('rationale')} (cites: {citations}){missing}"
        )
    actions = dossier.get("required_actions") or []
    if actions:
        lines += ["", "Required actions:"] + [f"- {action}" for action in actions]
    lines += ["", f"Summary: {dossier.get('summary', '')}"]
    return "\n".join(lines)


def export(
    run_id: str, n: int = 10, *, force: bool = False, root: Path = RESULTS_DIR
) -> Path:
    out_dir = root / run_id
    sheet = out_dir / "calibration.md"
    if sheet.exists() and not force:
        raise SystemExit(
            f"{sheet} already exists - move it away or pass --force to overwrite "
            "(unsaved labels would be lost)"
        )
    meta = load_label_meta()
    run = load_run(run_id, root)
    items = pick_items(run_id, n, root)
    if not items:
        raise SystemExit(
            f"no judged cases found under {out_dir} - run the eval with the judge first"
        )
    (out_dir / "calibration_items.json").write_text(
        json.dumps(items, indent=2) + "\n", encoding="utf-8"
    )
    parts = [
        f"# Judge calibration sheet - {run_id}",
        "",
        "Label each item blind: read the dossier facts, decide grounded yes/no and a 1-5",
        "score, fill the line under each item in the form 'yes|no, score N, note', then",
        "check the reference section at the end.",
        "",
    ]
    for index, case_id in enumerate(items, 1):
        label = meta[case_id]
        dossier = run[case_id]["record"].get("submitted") or {}
        parts += [
            f"## Item {index} - {case_id} "
            f"({label['metadata']['difficulty']}, {label['metadata']['category']})",
            "",
            _dossier_block(dossier),
            "",
            CALL_BLANK,
            "",
            "---",
            "",
        ]
    parts += ["## Judge reference (do not read before labelling)", ""]
    for index, case_id in enumerate(items, 1):
        judge = run[case_id]["judge"]
        parts += [
            f"### Item {index} - {case_id}",
            f"grounded: {judge['grounded']} | score: {judge['score']}",
            f"comment: {judge['comment']}",
            "",
        ]
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet.write_text("\n".join(parts), encoding="utf-8")
    return sheet


def compare(run_id: str, root: Path = RESULTS_DIR) -> dict:
    out_dir = root / run_id
    sheet = out_dir / "calibration.md"
    items_path = out_dir / "calibration_items.json"
    if not sheet.exists() or not items_path.exists():
        raise SystemExit("no calibration sheet found - run `export` first")
    calls = CALL_RE.findall(sheet.read_text(encoding="utf-8"))
    items = json.loads(items_path.read_text(encoding="utf-8"))
    run = load_run(run_id, root)
    pairs = list(zip(items, calls))
    if not pairs:
        raise SystemExit("no filled 'Your call' lines found in the sheet")
    details = []
    agreement = 0
    deltas = []
    for case_id, (user_grounded, user_score) in pairs:
        judge = run[case_id]["judge"]
        judge_grounded = "yes" if judge["grounded"] else "no"
        match = judge_grounded == user_grounded.lower()
        agreement += match
        delta = abs(judge["score"] - int(user_score))
        deltas.append(delta)
        details.append(
            {
                "case_id": case_id,
                "judge_grounded": judge_grounded,
                "user_grounded": user_grounded.lower(),
                "judge_score": judge["score"],
                "user_score": int(user_score),
                "agree": match,
            }
        )
    result = {
        "run_id": run_id,
        "labelled": len(pairs),
        "agreement": agreement / len(pairs),
        "mean_abs_score_delta": sum(deltas) / len(deltas),
        "items": details,
    }
    (out_dir / "calibration_results.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    export_cmd = sub.add_parser("export", help="write the calibration sheet")
    export_cmd.add_argument("--run-id", required=True)
    export_cmd.add_argument("--n", type=int, default=10)
    export_cmd.add_argument("--force", action="store_true")
    compare_cmd = sub.add_parser("compare", help="score the filled sheet")
    compare_cmd.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if args.command == "export":
        path = export(args.run_id, args.n, force=args.force)
        print(f"calibration sheet written: {path}")
        return 0
    result = compare(args.run_id)
    print(
        f"labelled: {result['labelled']} | agreement: {result['agreement']:.0%} | "
        f"mean |judge-user| score delta: {result['mean_abs_score_delta']:.2f}"
    )
    for item in result["items"]:
        flag = "ok" if item["agree"] else "MISMATCH"
        print(
            f"- {item['case_id']}: judge {item['judge_grounded']}/{item['judge_score']} "
            f"vs user {item['user_grounded']}/{item['user_score']} [{flag}]"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
