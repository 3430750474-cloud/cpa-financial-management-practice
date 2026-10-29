"""Independent arithmetic and keyed-option checks for new chapter 3 questions."""
from decimal import Decimal as D
from curated_ch03_decisions import chapter_three_decisions


def keyed(topic, texts):
    q = next(q for q in chapter_three_decisions() if q["decisionTask"] == topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]} == set(texts)


assert (D('1.04') ** 2 - 1) * 100 == D('8.1600')
keyed("复利频次与比较口径", ["甲的有效年利率为8.16%", "甲的有效年利率高于乙", "甲每半年利率为4%"])
assert round(D(2) / (D('.10') - D('.04')), 2) == D('33.33')
keyed("永续增长模型适用", ["估计价值为33.33元", "2元作为下一年股利，不需要再乘以1.04", "在其他条件不变时，提高必要报酬率会降低估值"])
assert D(6) / D('1.08') + D(106) / (D('1.08') ** 2) < 100
keyed("债券估值与市场收益率", ["价值为6÷1.08+106÷1.08²", "债券价值低于面值", "必要报酬率下降且其他条件不变时，价值上升"])
assert D('.5') * D('.2') + D('.5') * D('-.1') == D('.05')
keyed("期望收益不等于实际收益", ["期望报酬率为5%", "实际报酬率可能为负"])
assert D('.4') * D('.08') + D('.6') * D('.13') == D('.11')
keyed("组合期望报酬率", ["组合期望收益率为11%", "组合期望收益率是两个资产期望收益率的加权平均"])
assert D('.03') + D('1.2') * (D('.09') - D('.03')) == D('.102')
keyed("资本资产定价模型计算", ["市场风险溢价为6%", "股票必要报酬率为10.2%", "股票的风险溢价为7.2%"])
assert D('.6') * D('.5') + D('.4') * D('1.5') == D('.9')
keyed("贝塔与组合权重", ["组合贝塔为0.9", "组合对市场变动的敏感度低于贝塔为1的市场组合"])
print("Chapter 3 numerical decisions independently checked")
