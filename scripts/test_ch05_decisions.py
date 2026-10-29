"""Recalculate numerical claims and keyed answers for capital budgeting."""
from decimal import Decimal as D
from curated_ch05_decisions import chapter_five_decisions


def keyed(topic, texts):
    q = next(q for q in chapter_five_decisions() if q["decisionTask"] == topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]} == set(texts)


assert (D(500)-300-80)*(1-D('.25'))+80 == 170
keyed("增量营业现金流", ["新增息税前利润为120万元", "所得税为30万元", "营业现金流量为170万元"])
assert 100-140 + (140+60-100)*D('.25') == -15
keyed("亏损项目税盾", ["该项目当年税前经营亏损为100万元", "项目亏损产生25万元税收节约", "当年营业现金流量为−15万元"])
assert 200-(200-120)*D('.25') == 180
assert 80+(120-80)*D('.25') == 90
keyed("处置收益纳税", ["应税处置收益为80万元", "处置相关所得税为20万元", "税后处置现金流为180万元"])
keyed("处置损失税收节约", ["处置损失为40万元", "处置损失带来10万元税收节约", "税后处置现金流为90万元"])
assert round(-D(100)+D(60)/D('1.1')+D(66)/D('1.1')**2,2) == D('9.09')
keyed("净现值基本判断", ["第1年现金流现值约为54.55万元", "第2年现金流现值约为54.55万元", "净现值约为9.09万元"])
for rate in (D('1.1'), D('1.2')):
    assert abs(-D(100)+D(230)/rate-D(132)/rate**2) < D('1e-24')
keyed("内部报酬率符号变化", ["现金流发生两次符号变化", "在10%折现率下净现值为零", "在20%折现率下净现值也为零"])
assert round((D('1.1')/D('1.04')-1)*100,2) == D('5.77')
keyed("名义和实际利率换算", ["实际折现率约为5.77%", "实际现金流应使用与之匹配的实际折现率", "名义利率减通胀率得到6%只是近似值"])
print("Chapter 5 numerical decisions independently checked")
