"""Regression checks for cross-chapter candidate detection."""
import json
import tempfile
from pathlib import Path
from audit_question_quality import audit


def main():
    with tempfile.TemporaryDirectory() as folder:
        data = Path(folder)
        manifest = {"version": "test", "chapters": [{"file": "a.json"}, {"file": "b.json"}]}
        (data / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        a = [{"id": "a1", "chapterId": "01", "type": "calculation", "stem": "企业本金100元，计算利息。"},
             {"id": "a2", "chapterId": "01", "type": "single", "stem": "条件甲下选择正确项目。",
              "options": [{"key": "A", "text": "正确"}, {"key": "B", "text": "错误"}], "answer": ["A"]},
             {"id": "a3", "chapterId": "01", "type": "calculation", "stem": "利率3%，市场9%，贝塔1.2，求报酬率。", "numericAnswer": 10.2, "unit": "%"}]
        b = [{"id": "b1", "chapterId": "02", "type": "calculation", "stem": "企业本金200元，计算利息。"},
             {"id": "b2", "chapterId": "02", "type": "single", "stem": "条件乙下选择正确项目。",
              "options": [{"key": "A", "text": "错误"}, {"key": "B", "text": "正确"}], "answer": ["B"]},
             {"id": "b3", "chapterId": "02", "type": "calculation", "stem": "贝塔1.2，无风险3%，市场收益9%，求资本成本。", "numericAnswer": 10.2, "unit": "%"}]
        for name, items in (("a.json", a), ("b.json", b)):
            (data / name).write_text(json.dumps({"questions": items}, ensure_ascii=False), encoding="utf-8")
        report = audit(data)["checks"]
        assert report["cross_chapter_number_masked_stem"]["groups"] == 1
        assert set(report["cross_chapter_number_masked_stem"]["details"][0]["ids"]) == {"a1", "b1"}
        assert report["cross_chapter_same_options_and_answer"]["groups"] == 1
        assert set(report["cross_chapter_same_options_and_answer"]["details"][0]["ids"]) == {"a2", "b2"}
        assert report["cross_chapter_same_numeric_inputs_and_answer"]["groups"] == 1
        assert set(report["cross_chapter_same_numeric_inputs_and_answer"]["details"][0]["ids"]) == {"a3", "b3"}
        assert report["number_masked_stem"]["groups"] == 0
        print("Cross-chapter masked stems, reordered answers and matching numeric inputs detected")


if __name__ == "__main__":
    main()
