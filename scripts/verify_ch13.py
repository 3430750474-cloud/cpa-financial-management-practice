"""Independent recalculation of chapter 13 questions from visible inputs."""
import re


def visible_ch13(q):
    x = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", q["stem"])]
    task = q["decisionTask"]
    if task == "材料定额消耗量分配":
        aq, au, bq, bu, cost=x; return cost*aq*au/(aq*au+bq*bu)
    if task == "人工费用工时分配":
        cost, ah, bh=x; return cost*ah/(ah+bh)
    if task == "制造费用实际分配率":
        cost, hours=x; return cost/hours
    if task == "制造费用分配额":
        rate, hours=x; return rate*hours
    if task == "计划分配率下的未分配差额":
        actual, allocated=x; return actual-allocated
    if task == "辅助生产直接分配法":
        cost, total, auxiliary, basic=x; return cost/(total-auxiliary)*basic
    if task == "辅助生产交互分配":
        cost, total, auxiliary=x; return cost/total*auxiliary
    if task == "加工费用约当产量":
        complete, wip, rate=x; return complete+wip*rate/100
    if task == "约当产量单位加工成本":
        cost, units=x; return cost/units
    if task == "完工产品加工费用":
        cost, complete, wip, rate=x; return cost/(complete+wip*rate/100)*complete
    if task == "材料一次投料约当产量":
        complete, wip=x; return complete+wip
    if task == "联产品售价比例分配":
        a, b, cost=x; return cost*a/(a+b)
    if task == "副产品扣除法":
        cost, byproduct=x; return cost-byproduct
    raise ValueError(f"Unknown chapter 13 task: {task}")
