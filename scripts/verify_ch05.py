"""Recalculate chapter 5 exercises from their visible inputs."""
import re


def numbers(text):
    return [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]


def annuity(rate, years):
    return sum(1/(1+rate/100)**t for t in range(1, int(years)+1))


def visible_ch05(q):
    x = numbers(q["stem"]); task = q["decisionTask"]
    if task == "净现值":
        investment, years, cash, rate=x; return -investment+cash*annuity(rate,years)
    if task == "现值指数":
        investment, present=x; return present/investment
    if task == "静态回收期跨年估计":
        investment, cash, final_year=x
        assert final_year==3; return 2+(investment-2*cash)/cash
    if task == "营业现金流量":
        sales, costs, depreciation, tax=x; return (sales-costs-depreciation)*(1-tax/100)+depreciation
    if task == "折旧税盾":
        depreciation, tax=x; return depreciation*tax/100
    if task == "资产处置税后现金流":
        sale, basis, tax=x; return sale-(sale-basis)*tax/100
    if task == "营运资本回收":
        working_capital,=x; return working_capital
    if task == "等额年金成本":
        cost, years, rate=x; return cost/annuity(rate,years)
    raise ValueError(f"Unknown chapter 5 calculation: {task}")


def visible_case05(q):
    x = numbers(q["material"]); task=q["decisionTask"]
    if task == "净现值与回收期":
        investment, years, cash, rate=x; return [investment/cash, -investment+cash*annuity(rate,years)]
    if task == "折旧与营业现金流":
        sales, variable, fixed, depreciation, tax=x; profit=sales-variable-fixed-depreciation
        return [profit, profit*(1-tax/100)+depreciation]
    if task == "机会成本与项目现金流":
        rent, cash, years, rate=x; return [rent*annuity(rate,years), cash-rent]
    if task == "营运资本与终结流量":
        equipment, working_capital, sale, basis, tax=x; return [equipment+working_capital, sale-(sale-basis)*tax/100+working_capital]
    if task == "设备更新初始投资":
        new, sale, basis, tax=x; proceeds=sale-(sale-basis)*tax/100; return [proceeds,new-proceeds]
    if task == "产品替代效应":
        new, lost, fixed=x; return [new-lost,new-lost-fixed]
    if task == "不同期限设备比较":
        a, ayears, b, byears, rate=x; return [a/annuity(rate,ayears),b/annuity(rate,byears)]
    if task == "价格敏感性分析":
        quantity, price, variable, fixed, decline=x; return [quantity*(price-variable)-fixed,quantity*(price*(1-decline/100)-variable)-fixed]
    raise ValueError(f"Unknown chapter 5 case: {task}")
