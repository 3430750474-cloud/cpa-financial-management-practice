"""Independently recalculate working-capital answers from displayed inputs."""
import math
import re


def values(text):
    return [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]


def visible_ch11(q):
    x = values(q["stem"]); task = q["decisionTask"]
    if task == "现金存货模式最佳转换额":
        demand, fee, rate=x; return math.sqrt(2*demand*fee/(rate/100))
    if task == "现金存货模式平均余额":
        balance,=x; return balance/2
    if task == "现金安全余额":
        daily, days, safety=x; return daily*days+safety
    if task == "收付款浮游量":
        payment, deposit=x; return payment-deposit
    if task == "信用政策增量损益":
        sales, variable, bad, collection, receivable, rate=x; return sales*(1-variable/100)-bad-collection-receivable*rate/100
    if task == "应收账款平均余额":
        sales, period, days=x; return sales/days*period
    if task == "应收账款机会成本":
        balance, variable, rate=x; return balance*variable/100*rate/100
    if task == "逾期应收比例":
        total, overdue=x; return overdue/total*100
    if task == "基本经济订货量":
        demand, fee, holding=x; return math.sqrt(2*demand*fee/holding)
    if task == "年度订货次数":
        demand, quantity=x; return demand/quantity
    if task == "订货与储存相关成本":
        demand, quantity, fee, holding=x; return demand/quantity*fee+quantity/2*holding
    if task == "有安全库存的再订货点":
        daily, lead, safety=x; return daily*lead+safety
    if task == "贴现法借款实际利率":
        loan, rate=x; interest=loan*rate/100; return interest/(loan-interest)*100
    if task == "补偿性余额借款利率":
        loan, rate, balance=x; return loan*rate/100/(loan*(1-balance/100))*100
    if task == "放弃现金折扣成本":
        discount, early, late, late_again, early_again, days=x
        assert early==early_again and late==late_again
        return discount/(100-discount)*days/(late-early)*100
    if task == "到期还本付息借款利率":
        loan, rate=x; return loan*rate/100/loan*100
    raise ValueError(f"Unknown chapter 11 task: {task}")


def visible_case11(q):
    x = values(q["material"]); task = q["decisionTask"]
    if task == "现金转换计划":
        demand, fee, rate, current=x; r=rate/100
        return [demand/current*fee+current/2*r, math.sqrt(2*demand*fee/r)]
    if task == "信用政策比较":
        sales, variable, bad, collection, receivable, rate=x; contribution=sales*(1-variable/100)
        return [contribution, contribution-bad-collection-receivable*rate/100]
    if task == "收款期变化":
        sales, year_days, old, new=x; return [sales/year_days*old, sales/year_days*(old-new)]
    if task == "经济订货量与成本":
        demand, fee, holding, current=x; return [demand/current*fee+current/2*holding, math.sqrt(2*demand*fee/holding)]
    if task == "再订货与安全库存":
        daily, lead, safety, current=x; return [daily*lead+safety, None]
    if task == "数量折扣方案":
        demand, fee, holding, qty_a, price_a, qty_b, price_b=x
        return [demand*price_a+demand/qty_a*fee+qty_a/2*holding, demand*price_b+demand/qty_b*fee+qty_b/2*holding]
    if task == "现金折扣决策":
        discount, early, late, early_again, late_again, days, rate=x
        assert early==early_again and late==late_again
        return [discount/(100-discount)*days/(late-early)*100, None]
    if task == "贴现法贷款":
        loan, rate, alternative=x; interest=loan*rate/100; return [loan-interest, interest/(loan-interest)*100]
    raise ValueError(f"Unknown chapter 11 case: {task}")
