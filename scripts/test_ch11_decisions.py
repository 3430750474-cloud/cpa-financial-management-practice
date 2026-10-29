"""Recalculate working capital decisions and verify selected answers."""
from decimal import Decimal as D
from curated_ch11_decisions import chapter_eleven_decisions


def keyed(topic, texts):
    q=next(q for q in chapter_eleven_decisions() if q["decisionTask"]==topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]}==set(texts)


assert 40+180-150-50==20 and 30-20==10
keyed("现金收支预算", ["未融资时月末现金为20万元", "达到最低现金余额需筹集10万元", "月末现金不足可通过事先安排融资或调整付款处理"])
assert (D(2)*1000*D('.5')/D('.1')).sqrt()==100
keyed("最佳现金持有量", ["最佳每次转换额为100万元", "平均现金余额为50万元", "每年转换10次"])
assert D(3600)/360*30*D('.6')==180
keyed("应收账款平均占用", ["平均应收账款余额为300万元", "按变动成本口径的平均资金占用为180万元", "若资金年成本率10%，年占用成本为18万元"])
assert round(D('.02')/D('.98')*D(360)/20*100,2)==D('36.73')
keyed("现金折扣成本", ["折扣期与信用期相差20天", "放弃折扣的20天成本约为2.04%", "简单年化成本约为36.73%"])
assert (D(2)*10000*200/4).sqrt()==1000
keyed("基本经济订货量", ["经济订货量为1,000件", "每年订货10次", "平均库存为500件"])
assert 1000*10+1500==11500 and 1000*9+2000==11000
keyed("数量折扣与总成本", ["方案甲相关总成本为11,500元", "方案乙相关总成本为11,000元", "方案乙成本低500元"])
assert D(8)/(100-20)==D('.1')
keyed("短期借款补偿性余额", ["可自由使用的资金为80万元", "按可用资金计算的一年期简单实际利率为10%", "该实际利率高于名义利率8%"])
print("Chapter 11 numerical decisions independently checked")
