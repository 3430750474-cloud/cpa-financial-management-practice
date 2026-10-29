"""Independently recalculate long-term financing examples and keyed answers."""
from decimal import Decimal as D
from curated_ch09_decisions import chapter_nine_decisions


def keyed(topic, texts):
    q=next(q for q in chapter_nine_decisions() if q["decisionTask"]==topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]}==set(texts)


assert round((D(1060)/D(950)-1)*100,2)==D('11.58')
keyed("债券折价发行", ["期末现金流出为1,060元", "发行人的一年期税前成本约为11.58%", "税前成本高于票面利率6%"])
assert round((D(1050)/D(970)-1)*100,2)==D('8.25')
keyed("发行费用与净筹资额", ["实际筹资净额为970万元", "期末现金流出为1,050万元", "一年期税前成本约为8.25%"])
assert D(1000)/20*24==1200
keyed("可转换债券转换价值", ["转换比例为50股", "转换价值为1,200元", "若债券市价1,300元，转换价值低于债券市价"])
assert round(D(1000)/1100*100,2)==D('90.91')
keyed("转股稀释与债务", ["转换后普通股总数为1,100万股", "原股东合计持股比例约为90.91%", "转换可能降低原股东的持股比例"])
assert round((D(100)*10+D(20)*6)/120,2)==D('9.33')
keyed("配股除权价格", ["配股募集资金为120万元", "配股后总股数为120万股", "理论除权价格约为9.33元"])
assert D(100)*(1-D('.25'))==75
keyed("租赁税后现金流", ["每年租金税收节约为25万元", "每年税后租金净流出为75万元", "税后净流出依赖实际可利用税盾"])
assert 120-90==30
keyed("债券提前赎回判断", ["再融资净现值为30万元", "仅凭新债券票面利率更低不足以判断方案是否有利", "按题设净现值原则可考虑再融资"])
print("Chapter 9 numerical decisions independently checked")
