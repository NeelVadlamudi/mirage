"""Append an audit eval result to docs/data/audit_eval.json and rebuild docs/data/audit_replay.json."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def now_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def publish(result_path: Path, site_dir: Path, questions_path: Path, scoring_changed: bool = False) -> None:
    res = json.loads(result_path.read_text())
    stamp = now_z()
    path = site_dir / "audit_eval.json"
    ev = json.loads(path.read_text()) if path.exists() else {"runs": []}
    run = {"model": res["model"], "date": res["date"], "summary": res["summary"]}
    if scoring_changed:
        run["scoring_changed"] = True
    ev["runs"].append(run)
    ev["run_at"] = stamp
    path.write_text(json.dumps(ev, indent=2) + "\n")
    questions = {q["id"]: q for q in yaml.safe_load(questions_path.read_text())["questions"]}
    rows = {r["id"]: r for r in res["rows"]}
    answers = [{"id": qid, "type": questions[qid]["type"], "question": questions[qid]["question"],
                "response": resp, "correct": bool(rows[qid]["correct"])}
               for qid, resp in res["responses"].items()]
    (site_dir / "audit_replay.json").write_text(json.dumps({"recorded_at": stamp, "answers": answers}, indent=1, default=str) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("result", type=Path)
    ap.add_argument("--site-dir", type=Path, default=ROOT / "docs" / "data")
    ap.add_argument("--questions", type=Path, default=ROOT / "evals" / "questions.yaml")
    ap.add_argument("--scoring-changed", action="store_true")
    args = ap.parse_args()
    publish(args.result, args.site_dir, args.questions, args.scoring_changed)
    print(f"published {args.result.name}")


if __name__ == "__main__":
    main()
