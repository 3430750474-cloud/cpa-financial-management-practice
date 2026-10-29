"""Recalculate authored chapter 15 answers from numbers in the visible stem."""
import re


def visible_ch15(q):
    x = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", q["stem"])]
    task = q["decisionTask"]
    if task == "批次作业成本率":
        cost, batches=x; return cost/batches
    if task == "产品批次作业分配":
        rate, batches=x; return rate*batches
    if task == "检验作业成本率差异":
        cost, inspections, budget=x; return cost/inspections-budget
    if task == "检验作业成本节约":
        original, reduction, cost=x; return reduction*cost
    if task == "单位级作业成本率":
        cost, hours=x; return cost/hours
    if task == "产品级设计成本分配":
        cost, products=x; return cost/products
    if task == "生产维持成本分配率":
        cost, hours=x; return cost/hours
    if task == "多作业成本归集":
        hours, setups, inspections, h_rate, setup_rate, inspection_rate=x
        return hours*h_rate+setups*setup_rate+inspections*inspection_rate
    if task == "传统法与作业成本法比较":
        total, hours, product_hours, abc=x; return abc-total/hours*product_hours
    if task == "单位产品作业成本":
        materials, labor, overhead, units=x; return (materials+labor+overhead)/units
    if task == "未折现生命周期成本":
        acquisition, years, annual, disposal=x; return acquisition+years*annual+disposal
    if task == "未来处置成本现值":
        years, disposal, rate=x; return disposal/(1+rate/100)**years
    raise ValueError(f"Unknown chapter 15 task: {task}")
