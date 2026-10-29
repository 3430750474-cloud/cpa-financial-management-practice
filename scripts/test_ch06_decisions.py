"""Independently verify numerical claims and keyed option answers."""
from decimal import Decimal as D
from curated_ch06_decisions import chapter_six_decisions


def keyed(topic, texts):
    q = next(q for q in chapter_six_decisions() if q["decisionTask"] == topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]} == set(texts)


assert max(53-50,0)-4 == -1
keyed("看涨多头到期损益", ["到期价值为3元", "期权净损益为−1元", "期权有正到期价值，但投资者仍亏损"])
assert 30+max(45-30,0)-(50+3) == -8
keyed("保护性看跌下限", ["组合初始支出为53元", "到期股价跌至30元时组合到期价值为45元", "该情形下净损益为−8元"])
assert 70-max(70-55,0)-(50-2) == 7
keyed("备兑看涨上限", ["到期组合价值为55元", "初始净支出为48元", "组合净收益为7元"])
assert round(D(6)+D(50)/D('1.1')-50,2)==D('1.45')
keyed("看涨看跌平价计算", ["执行价格现值约为45.45元", "相应看跌期权价值约为1.45元", "看涨加执行价现值与看跌加股票现价相等"])
p=(D('1.05')-D('.8'))/(D('1.2')-D('.8'))
assert p==D('.625') and round(p*20/D('1.05'),2)==D('11.90')
assert round(D('.5')*100-D(40)/D('1.05'),2)==D('11.90')
keyed("二叉树看涨期权估值", ["上行和下行状态的期权到期价值分别为20元和0元", "风险中性上行概率为62.5%", "期权当前价值约为11.90元"])
keyed("复制组合与借款", ["复制组合持有0.5股股票", "复制组合期末应偿还40元无风险借款", "组合当前价值约为11.90元"])
assert max(150-100,0)==50 and max(60-100,0)==0
assert max(30,50)-30==20
keyed("放弃期权与比较基础", ["高价值状态下继续经营价值80万元高于出售所得", "低价值状态下出售比继续经营多20万元", "低价值状态下含选择权的项目价值为50万元"])
print("Chapter 6 numerical decisions independently checked")
