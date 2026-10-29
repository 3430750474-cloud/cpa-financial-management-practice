"""Content audit. Text uniqueness is not pedagogical uniqueness or correctness."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def normalized(text: str, mask_numbers=False) -> str:
    text = re.sub(r"[甲乙丙丁]公司|某企业|某公司", "企业", text)
    if mask_numbers:
        text = re.sub(r"\d+(?:[,，.]\d+)*(?:%|％)?", "数值", text)
    return re.sub(r"[\s，。；：、！？（）()“”‘’\-—]", "", text)

def audit(data_dir: Path):
    manifest = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    questions = [q for c in manifest["chapters"] for q in json.loads((data_dir / c["file"]).read_text(encoding="utf-8"))["questions"]]
    groups = {key: collections.defaultdict(list) for key in ["exact_stem", "number_masked_stem", "same_options_and_answer", "same_teaching_target"]}
    cross_stems = collections.defaultdict(list)
    cross_options = collections.defaultdict(list)
    cross_numeric_inputs = collections.defaultdict(list)
    chapter_by_id = {q["id"]: q["chapterId"] for q in questions}
    scaffolded = []
    for q in questions:
        stem = q.get("stem", q.get("material", ""))
        chapter = q["chapterId"]
        groups["exact_stem"][(chapter, normalized(stem))].append(q["id"])
        groups["number_masked_stem"][(chapter, q["type"], normalized(stem, True))].append(q["id"])
        cross_stems[(q["type"], normalized(stem, True))].append(q["id"])
        if q["type"] == "calculation" and isinstance(q.get("numericAnswer"), (int, float)):
            values = tuple(sorted(float(s.replace(",", "").replace("，", "")) for s in re.findall(r"\d[\d,，]*(?:\.\d+)?", stem)))
            if len(values) >= 2:
                cross_numeric_inputs[(values, q["numericAnswer"], q.get("unit", ""))].append(q["id"])
        if q.get("options"):
            # Ignore option letters/order and irrelevant filler in the stem, but retain
            # the expected selected propositions. A match is an audit candidate.
            options = tuple(sorted(normalized(o["text"], True) for o in q["options"]))
            answer = tuple(sorted(normalized(o["text"], True) for o in q["options"] if o["key"] in q["answer"]))
            groups["same_options_and_answer"][(chapter, options, answer)].append(q["id"])
            cross_options[(options, answer)].append(q["id"])
        match = re.search(r"考点：(.*?)。答案为", q.get("explanation", ""), re.S)
        if match and stem.startswith(("在复核「", "某企业复核", "审阅")):
            scaffolded.append(q["id"])
            groups["same_teaching_target"][(chapter, normalized(match[1]))].append(q["id"])
    reports = {}
    for name, buckets in groups.items():
        repeated = [{"fingerprint": hashlib.sha256(repr(key).encode()).hexdigest()[:16], "chapter": key[0], "size": len(ids), "ids": ids, "sample": str(key[1:])[:600], "disposition": "unresolved"} for key, ids in buckets.items() if len(ids) > 1]
        repeated.sort(key=lambda g: (-g["size"], g["fingerprint"]))
        reports[name] = {"groups": len(repeated), "affectedQuestions": sum(g["size"] for g in repeated), "excessQuestions": sum(g["size"] - 1 for g in repeated), "details": repeated}
    for name, buckets in (("cross_chapter_number_masked_stem", cross_stems), ("cross_chapter_same_options_and_answer", cross_options), ("cross_chapter_same_numeric_inputs_and_answer", cross_numeric_inputs)):
        repeated = []
        for key, ids in buckets.items():
            chapters = sorted({chapter_by_id[qid] for qid in ids})
            if len(chapters) < 2:
                continue
            repeated.append({"fingerprint": hashlib.sha256(repr(key).encode()).hexdigest()[:16],
                             "chapter": ",".join(chapters), "size": len(ids), "ids": ids,
                             "sample": str(key)[:600], "disposition": "unresolved"})
        repeated.sort(key=lambda g: (-g["size"], g["fingerprint"]))
        reports[name] = {"groups": len(repeated), "affectedQuestions": sum(g["size"] for g in repeated),
                         "excessQuestions": sum(g["size"] - 1 for g in repeated), "details": repeated}
    return {"version": manifest["version"], "total": len(questions), "scope": "Full bank; deterministic candidate detection, not a claim of complete semantic review", "metricsAreOverlapping": True,
            "interpretation": {"same_options_and_answer": "Same options and selected propositions after normalization; review stem conditions before disposition", "same_teaching_target": "Same extracted teaching target in the legacy scaffold generator; not automatically an exact duplicate", "number_masked_stem": "Same problem text after removing parameter values and generic company names", "cross_chapter_number_masked_stem": "Candidate question text after masking numbers that appears across chapters", "cross_chapter_same_options_and_answer": "Same normalized options and selected propositions across chapters; review context", "cross_chapter_same_numeric_inputs_and_answer": "Same displayed numbers, numeric answer and unit across chapters; coincidence is possible and requires review"},
            "legacyScaffoldQuestions": len(scaffolded), "legacyScaffoldIds": scaffolded, "checks": reports,
            "qualityReleasePassed": not scaffolded and all(not r["groups"] for r in reports.values())}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "dist/data")
    parser.add_argument("--output", type=Path, default=ROOT / "review/content-quality-audit.json")
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()
    report = audit(args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"total": report["total"], "legacyScaffoldQuestions": report["legacyScaffoldQuestions"], "qualityReleasePassed": report["qualityReleasePassed"], "checks": {k: {n:v for n,v in r.items() if n != "details"} for k,r in report["checks"].items()}}, ensure_ascii=False))
    if args.enforce and not report["qualityReleasePassed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
