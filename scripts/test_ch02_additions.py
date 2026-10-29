"""Independently check the results and keyed answers of recent chapter 2 exercises."""
from decimal import Decimal as D
from curated_ch02_multiple import chapter_two_multiple


def check(topic, expected):
    question = next(q for q in chapter_two_multiple() if q["decisionTask"] == topic)
    selected = {o["text"] for o in question["options"] if o["key"] in question["answer"]}
    assert selected == set(expected), (topic, selected)
    assert len(question["explanation"].split("；")) == 4


assert D(200) / D(100) * D('1.2') == D('2.4')
assert D(30) / D('2.4') == D('12.5')
check("市盈率与盈利增长", ["上年每股收益为2元", "以上年每股收益计算的市盈率为15倍", "按预计本年每股收益计算的市盈率为12.5倍"])
assert D(150) / D(90) > D(180) / D(120)
check("速动比率与偿债", ["用现金偿还30万元流动负债后速动比率提高", "用现金购买20万元存货后速动比率下降"])
assert D(240) / D(2000) - D(64) / D(800) == D('.04')
check("改进杜邦分析杠杆贡献", ["净经营资产净利率为12%", "税后利息率为8%", "经营差异率为4个百分点"])
assert D(300) - 40 - 60 == 200
assert 200 - (30 - 50) == 220
check("实体现金流与筹资流", ["实体现金流量为200万元", "债务现金流量为负20万元", "股权现金流量为220万元"])
assert D(500) - D(-30) - 80 == 450
check("经营营运资本变动", ["经营营运资本投资为负30万元", "实体现金流量为450万元", "经营营运资本下降对实体现金流量产生30万元正向影响"])
assert D(200) * (D('.7') - D('.2')) - D(1200) * D('.1') * D('.5') == 40
check("外部融资需求与留存", ["预计增加的净经营资产为100万元", "预计留存收益增加60万元", "外部融资需求为40万元"])
assert D(2000) * D('1.2') * D('.9') == 2160
check("预测收入与新增资金", ["预计销售收入为2,160万元", "销售收入增长率为8%", "新增融资需求为40万元"])
assert D(150) * D('.4') == 60
assert round(D(60) / D(940) * 100, 2) == D('6.38')
check("可持续增长率的期初期末口径", ["本年留存收益增加60万元", "期初权益为940万元", "以期初权益计算的增长率约为6.38%"])
print("Chapter 2 newly authored numerical choices independently checked")
