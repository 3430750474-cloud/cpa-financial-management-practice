"""Independent calculations and keyed answers for new capital-cost questions."""
from decimal import Decimal as D
from curated_ch04_decisions import chapter_four_decisions


def keyed(topic, texts):
    q = next(q for q in chapter_four_decisions() if q["decisionTask"] == topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]} == set(texts)


assert round((D(1045) / D(980) - 1) * 100, 2) == D('6.63')
keyed("税后债务成本与费用", ["发行净收入为980万元", "一年期税后现金流出的利息部分为45万元", "按净收入与税后期末现金流估计的年成本约为6.63%"])
assert (D('1.03')**2 - 1) * 100 == D('6.0900')
keyed("利率周期与债务成本", ["税前半年期利率为4%", "税后半年期利率为3%", "税后有效年利率为6.09%"])
assert D('1.5') / D(25) + D('.04') == D('.10')
assert D('.95') / (D(20) * D('.95')) + D('.04') == D('.09')
keyed("新股发行净额", ["每股筹资净额为19元", "新股资本成本为9%", "发行费用使每股筹资净额低于发行价"])
assert D('.025') + D('1.3') * (D('.085') - D('.025')) == D('.103')
keyed("资本资产定价模型权益成本", ["市场风险溢价为6个百分点", "权益资本成本为10.3%", "股票风险溢价为7.8个百分点"])
assert D('.4') * D('.08') * (1-D('.25')) + D('.6') * D('.12') == D('.096')
keyed("市场权重计算", ["债务市场价值权重为40%", "税后债务成本为6%", "加权平均资本成本为9.6%"])
assert round(D('1.2') / (1 + (1-D('.2')) * D('.5')), 3) == D('.857')
keyed("可比企业去杠杆", ["可比公司资产贝塔约为0.857", "使用可比公司贝塔前应考虑融资结构差异"])
print("Chapter 4 numerical decisions independently checked")
