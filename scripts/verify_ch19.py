"""Independently recompute authored chapter 19 answers from the visible stem."""
import re


def visible_ch19(question):
    x = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", question["stem"])]
    task = question["decisionTask"]
    if task == "责任成本差异":
        budget, actual = x; return actual-budget
    if task == "弹性预算差异":
        fixed, variable, hours, actual = x; return actual-(fixed+variable*hours)
    if task == "材料数量差异":
        actual, standard, price = x; return (actual-standard)*price
    if task == "材料价格差异":
        quantity, actual, standard = x; return quantity*(actual-standard)
    if task == "可控责任成本":
        total, excluded = x; return total-excluded
    if task == "边际贡献":
        sales, variable = x; return sales-variable
    if task == "可控边际贡献":
        margin, controllable, excluded = x; return margin-controllable
    if task == "部门边际贡献":
        controllable_margin, traceable_fixed = x; return controllable_margin-traceable_fixed
    if task == "停业决策增量利润":
        lost, saved = x; return saved-lost
    if task == "剩余产能":
        capacity, external = x; return capacity-external
    if task == "闲置产能转移价格下限":
        variable, transport = x; return variable+transport
    if task == "满负荷转移价格下限":
        outside, variable = x; return variable+(outside-variable)
    if task == "购入部门转移价格上限":
        outside, freight = x; return outside+freight
    if task == "内部转移的公司增量收益":
        variable, transport, outside = x; return outside-variable-transport
    if task == "投资报酬率":
        profit, capital = x; return profit/capital*100
    if task == "剩余收益":
        profit, capital, rate = x; return profit-capital*rate/100
    if task == "追加项目后的投资报酬率":
        profit, capital, added_profit, added_capital = x; return (profit+added_profit)/(capital+added_capital)*100
    if task == "项目增量剩余收益":
        added_profit, added_capital, rate = x; return added_profit-added_capital*rate/100
    if task == "目标剩余收益倒推利润":
        capital, rate, target = x; return target+capital*rate/100
    if task == "利润率与周转率分解":
        margin, turnover = x; return margin*turnover
    raise ValueError(f"Unsupported task: {task}")
