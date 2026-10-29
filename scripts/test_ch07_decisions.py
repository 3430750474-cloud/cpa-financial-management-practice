"""Independently recalculate and check keyed enterprise valuation choices."""
from decimal import Decimal as D
from curated_ch07_decisions import chapter_seven_decisions


def keyed(topic, texts):
    q=next(q for q in chapter_seven_decisions() if q["decisionTask"] == topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]} == set(texts)


assert 1000+100-300 == 800 and 300-100 == 200
keyed("实体与股权价值桥", ["全部资产价值为1,100万元", "股权价值为800万元", "净债务为200万元"])
assert D(120)/(D('.1')-D('.04'))==2000
keyed("股权现金流折现", ["股权价值为2,000万元", "分子120万元是下一期现金流", "增长率必须低于折现率才能得到有限正的模型价值"])
assert 500-120 == 380 and 380-(40-20) == 360
keyed("实体现金流与融资", ["实体现金流为380万元", "债务现金流为20万元", "股权现金流为360万元"])
assert round(D(100)*D('1.04')/(D('.1')-D('.04')),2)==D('1733.33')
keyed("稳定期价值时点", ["第6年现金流为104万元", "第5年末的后续价值约为1,733.33万元", "第5年末后续价值须再折现5年回到第0时点"])
assert D(200)/1000*15==3 and 8*100-300+50==550
keyed("市盈率估值", ["预计每股收益为0.20元", "预计每股价值为3元", "普通股股权价值为3,000万元"])
keyed("企业价值倍数桥接", ["估计经营资产价值为800万元", "净债务为250万元", "估计股权价值为550万元"])
assert 1000+20-200-50==770
keyed("少数股东权益处理", ["合并全部资产价值为1,020万元", "归属于母公司普通股股东的价值为770万元", "需扣除少数股东权益以避免将其价值归给母公司股东"])
assert round(D(100)/(D('.11')-D('.04')),2)==D('1428.57')
keyed("估值结果敏感性", ["基准后续价值约为1,666.67万元", "折现率提高至11%时价值约为1,428.57万元", "折现率与增长率差距缩小时估值对假设变化更敏感"])
print("Chapter 7 numerical decisions independently checked")
