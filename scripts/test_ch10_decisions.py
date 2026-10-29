"""Independent dividend and repurchase calculations with answer-key checks."""
from decimal import Decimal as D
from curated_ch10_decisions import chapter_ten_decisions


def keyed(topic, texts):
    q=next(q for q in chapter_ten_decisions() if q["decisionTask"]==topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]}==set(texts)


assert D(1200)*D('.6')==720 and 1000-720==280
keyed("剩余股利计算", ["投资所需权益资金为720万元", "剩余可供分配的利润为280万元", "本年利润中留存720万元用于满足权益资金需要"])
assert D(800)*D('.4')/400==D('.8') and D(1200)*D('.4')/400==D('1.2')
keyed("固定股利支付率计算", ["第一年每股股利为0.8元", "第二年每股股利为1.2元", "股利总额随利润从320万元增至480万元"])
assert 30/3==10 and 600/(200*3)==1
keyed("股票分割每股指标", ["拆分后普通股为600万股", "理论每股市价为10元", "按拆分后股数计算的每股收益为1元"])
assert 200/10==20 and (1000-200)/(100-20)==10
keyed("按市价回购注销", ["回购股份20万股", "注销后剩余80万股", "回购后权益总价值为800万元"])
assert round(D(1000-120)/90,2)==D('9.78')
keyed("高于内在价值回购", ["回购支付现金120万元", "回购后权益内在价值为880万元", "剩余每股内在价值约为9.78元"])
assert D(200)/(100-20)==D('2.5')
keyed("回购对每股收益的局限", ["回购前每股收益为2元", "按回购后股数简化计算的每股收益为2.5元", "每股收益提高不足以单独证明回购创造价值"])
print("Chapter 10 numerical decisions independently checked")
