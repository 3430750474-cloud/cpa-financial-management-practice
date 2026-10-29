"""Independently recalculate product-cost allocation examples."""
from decimal import Decimal as D
from curated_ch13_decisions import chapter_thirteen_decisions


def keyed(topic, texts):
    q=next(q for q in chapter_thirteen_decisions() if q["decisionTask"]==topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]}==set(texts)


assert D(12000)/(400+200)==20 and 400*20==8000
keyed("共同材料按耗用量分配", ["分配率为20元/千克", "甲产品分配8,000元", "乙产品分配4,000元"])
assert D(12000)/(400+200)==20 and 400*20==8000
keyed("辅助生产直接分配", ["对外分配的供电量为600度", "对外分配率为20元/度", "基本生产车间分配8,000元"])
assert 10000-D(10000)/1000*200+D(6000)/600*100==9000
keyed("辅助生产一次交互", ["供电交互分配率为10元/度", "供水交互分配率为10元/吨", "供电车间交互后的费用为9,000元"])
assert D(60000)/(800+400*D('.5'))==60 and 800*60==48000
keyed("约当产量加工费用", ["在产品加工约当产量为200件", "加工费用分配率为60元/约当件", "完工产品分配加工费用48,000元"])
assert D(60000)/(800+400)==50 and 400*50==20000 and 200*60==12000
keyed("一次投料与加工分别分配", ["材料分配率为50元/件", "在产品材料费用为20,000元", "在产品加工费用为12,000元"])
assert 100*(40+20)==6000 and 15000-6000==9000
keyed("定额成本法", ["期末在产品定额成本为6,000元", "完工产品成本为9,000元", "实际费用与定额存在差异时，本法下差异主要由完工产品承担"])
assert D(50000)*60000/100000==30000 and 65-50-8==7
keyed("联产品售价比例", ["甲产品分配30,000元联合成本", "乙产品分配20,000元联合成本", "两产品分配额合计50,000元"])
keyed("联产品继续加工", ["继续加工带来的增量收入为15万元", "继续加工的增量收益为7万元", "已发生的联合成本不改变两方案之间的增量比较"])
print("Chapter 13 numerical decisions independently checked")
