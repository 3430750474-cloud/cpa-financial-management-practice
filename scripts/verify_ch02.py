"""Recalculate authored chapter 2 answers from the numeric inputs shown to learners."""
import re


def visible_ch02(question):
    x = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", question["stem"])]
    task = question["decisionTask"]
    if task == "速动资产的范围":
        assets, inventory, prepaid, debt = x; return (assets-inventory-prepaid)/debt
    if task == "现金比率":
        cash, securities, debt = x; return (cash+securities)/debt
    if task == "偿债交易对流动比率的影响":
        assets, debt, payment = x; return (assets-payment)/(debt-payment)
    if task == "赊购与营运资本":
        assets, debt, purchase = x; return (assets+purchase)-(debt+purchase)
    if task == "应收账款周转率":
        sales, beginning, end = x; return sales/((beginning+end)/2)
    if task == "应收账款周转天数":
        days, sales, receivables = x; return days/(sales/receivables)
    if task == "存货周转率的分子":
        revenue, cost, beginning, end = x; return cost/((beginning+end)/2)
    if task == "存货周转天数":
        cost, inventory, days = x; return days/(cost/inventory)
    if task == "应付账款周转率":
        purchase, beginning, end = x; return purchase/((beginning+end)/2)
    if task == "现金周转期":
        inventory_days, receivable_days, payable_days = x; return inventory_days+receivable_days-payable_days
    if task == "总资产周转率":
        sales, beginning, end = x; return sales/((beginning+end)/2)
    if task == "净利润率":
        sales, profit = x; return profit/sales*100
    if task == "杜邦分解":
        margin, turnover, multiplier = x; return margin*turnover*multiplier
    if task == "权益乘数":
        assets, equity = x; return assets/equity
    if task == "净经营资产":
        assets, liabilities = x; return assets-liabilities
    if task == "净负债率":
        debt, equity = x; return debt/equity*100
    if task in {"可持续增长率", "内含增长率"}:
        rate, retention = x; k=rate/100*retention/100; return k/(1-k)*100
    if task == "外部融资需求":
        increase, assets_rate, liability_rate, sales, margin, retention = x
        return increase*assets_rate/100-increase*liability_rate/100-sales*margin/100*retention/100
    if task == "敏感资产预测":
        sales, assets, next_sales = x; return assets/sales*next_sales
    if task == "利息保障倍数":
        ebit, interest = x; return ebit/interest
    if task == "杠杆与税盾后的权益收益":
        operating_profit, after_tax_interest, equity = x; return (operating_profit-after_tax_interest)/equity*100
    raise ValueError(f"Unknown chapter 2 calculation {task}")
