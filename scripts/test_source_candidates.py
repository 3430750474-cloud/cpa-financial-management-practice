"""Regression tests for the review-only source question index."""
from extract_source_candidates import candidates


def test_contiguous_answers_and_question_boundaries():
    paragraphs = [
        "例题·单选题·2013年　旧题", "A.旧甲", "B.旧乙", "C.旧丙", "D.旧丁",
        "【答案】A", "【解析】旧解释。",
        "例题·多选题·2023年　新题", "A.新甲　B.新乙", "C.新丙  D.新丁",
        "【答案】ABCD", "【解析】新解释。",
        "例题·单选题　第三题", "A.甲", "B.乙", "C.丙", "D.丁", "【答案】C", "【解析】第三题解释。",
    ]
    rows = candidates(paragraphs, "02", "test.docx")
    assert len(rows) == 3
    assert rows[1]["answer"] == list("ABCD")
    assert rows[1]["options"] == [["A", "新甲"], ["B", "新乙"], ["C", "新丙"], ["D", "新丁"]]
    assert rows[1]["followingParagraphs"] == ["【解析】新解释。"]
    assert rows[1]["flags"] == []


def test_ambiguous_and_unheaded_answers_are_not_accepted():
    paragraphs = ["无标题", "【答案】A", "例题·单选题　表格如下表：", "A.甲", "B.乙", "【答案】AC", "结束"]
    rows = candidates(paragraphs, "02", "test.docx")
    assert len(rows) == 1
    assert "选项不完整或顺序异常" in rows[0]["flags"]
    assert "题型与答案数量不符" in rows[0]["flags"]
    assert "表格需核查原文" in rows[0]["flags"]
    assert "解析边界需核查" in rows[0]["flags"]


if __name__ == "__main__":
    test_contiguous_answers_and_question_boundaries()
    test_ambiguous_and_unheaded_answers_are_not_accepted()
    print("source candidate regression tests passed")
