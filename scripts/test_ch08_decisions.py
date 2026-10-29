"""Independently check capital-structure calculations and answer keys."""
from decimal import Decimal as D
from curated_ch08_decisions import chapter_eight_decisions


def keyed(topic, texts):
    q = next(q for q in chapter_eight_decisions() if q["decisionTask"] == topic)
    assert {o["text"] for o in q["options"] if o["key"] in q["answer"]} == set(texts)


assert (100-60)*D('1') == 40 and D(40)/(40-20)==2
keyed("边际贡献与经营杠杆", ["边际贡献为40万元", "息税前利润为20万元", "基期经营杠杆系数为2"])
assert D(60)/(1-D('.25')) == 80 and D(500)/(500-100-80)==D('1.5625')
keyed("优先股与财务杠杆", ["优先股股息的税前等价额为80万元", "普通股股东可分享的税前等价利润为320万元", "财务杠杆系数为1.5625"])
assert D(600)/(600-200-100)==2
keyed("总杠杆的乘积", ["经营杠杆系数为1.5", "财务杠杆系数约为1.33", "总杠杆系数为2"])
assert (D(240)-40)/100==(D(240)-80)/80
assert (D(400)-80)*D('.75')/80==3
keyed("每股收益无差别点", ["无差别点息税前利润为240万元", "息税前利润为400万元时乙方案每股收益为3元", "息税前利润为400万元时乙方案每股收益高于甲方案"])
assert round((D('.1')+(D('.1')-D('.06'))*D(400)/600)*100,2)==D('12.67')
keyed("无税MM与权益成本", ["权益价值为600万元", "权益成本约为12.67%", "加权平均资本成本仍为10%"])
assert D(1000)+D('.25')*400==1100
keyed("有税MM税盾价值", ["债务利息税盾价值为100万元", "有负债企业价值为1,100万元", "这一结论依赖特定理论假设"])
print("Chapter 8 numerical decisions independently checked")
