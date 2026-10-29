"""Independently check calculations and keyed cost-management answers."""
from decimal import Decimal as D
from curated_ch12_decisions import chapter_twelve_decisions


def keyed(topic, texts):
    q=next(q for q in chapter_twelve_decisions() if q["decisionTask"]==topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]}==set(texts)


assert 60+30+20==110 and 20+110-30==100 and 40+100-25==115
keyed("产品成本与期间费用", ["生产成本合计为110万元", "销售费用15万元通常不计入制造产品成本", "直接材料和直接人工均属于制造成本项目"])
keyed("成本流转与存货", ["本期可分配生产成本为130万元", "本期完工产品成本为100万元", "期末在产品成本30万元保留在在产品中"])
keyed("销售成本与存货", ["本期可供销售产品成本为140万元", "本期销售产品成本为115万元", "期末未售产成品成本为25万元"])
assert D(1200000)/8000==150 and D(1200000)/6000==200
keyed("固定成本相关范围", ["在题设相关范围内租金总额为固定成本", "产量8,000件时单位租金为150元", "产量6,000件时单位租金为200元"])
assert D(18000-12000)/(2000-1000)==6 and 18000-6*2000==6000
keyed("高低点的业务量", ["应选择2,000小时和1,000小时作为高低业务量点", "单位变动成本为6元/小时", "固定成本估计为6,000元"])
assert 2000+3*1500==6500 and 3*8000==24000
keyed("混合成本分解", ["变动部分为4,500元", "总费用为6,500元", "模型可表示为总费用=2,000+3×公里数"])
keyed("阶梯式成本", ["至少需要3名管理员", "管理员工资总额为24,000元", "订单数在一定区间内变化时工资总额可能不变"])
assert 30-18-8==4
keyed("机会成本与闲置产能", ["订单的直接增量净收入为12万元", "放弃出租净收入8万元是接受订单的机会成本", "与出租相比接受订单的增量收益为4万元"])
print("Chapter 12 numerical decisions independently checked")
