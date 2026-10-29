"""Independently recalculate chapter 4 answers from visible question data."""
import re


def visible_ch04(q):
    x = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", q["stem"])]
    task = q["decisionTask"]
    if task == "税后债务资本成本":
        rate, tax=x; return rate*(1-tax/100)
    if task == "加权平均资本成本":
        debt, equity, kd, ke=x; return (debt*kd+equity*ke)/100
    if task == "杠杆调整与资本资产定价":
        unlevered, debt_equity, tax, riskfree, market=x
        beta=unlevered*(1+(1-tax/100)*debt_equity); return riskfree+beta*(market-riskfree)
    if task == "股利增长模型":
        price, dividend, growth=x; return dividend/price*100+growth
    if task == "发行费用与权益成本":
        price, fee, dividend, growth=x; return dividend/(price*(1-fee/100))*100+growth
    if task == "永续债税后成本":
        price, interest, tax=x; return interest*(1-tax/100)/price*100
    if task == "债券收益率风险调整法":
        bond, premium=x; return bond+premium
    if task == "优先股资本成本":
        dividend, price=x; return dividend/price*100
    if task == "目标权重加权成本":
        debt, equity, kd, ke=x; return (debt*kd+equity*ke)/100
    if task == "债券分期复利的有效年利率":
        rate,=x; return ((1+rate/400)**4-1)*100
    raise ValueError(f"Unknown chapter 4 task: {task}")
