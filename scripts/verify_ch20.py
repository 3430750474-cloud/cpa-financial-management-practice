"""Recalculate chapter 20 authored results from the visible question or case."""
import re


def numbers(text):
    return [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]


def visible_ch20(question):
    x = numbers(question["stem"])
    task = question["decisionTask"]
    if task == "经济增加值":
        profit, capital, rate = x; return profit-capital*rate/100
    if task == "加权平均资本成本":
        wd, we, kd, ke, tax = x; return wd/100*kd*(1-tax/100)+we/100*ke
    if task == "资本费用":
        capital, rate = x; return capital*rate/100
    if task == "税后营业利润":
        profit, tax = x; return profit*(1-tax/100)
    if task == "新增投资对经济增加值的影响":
        profit, capital, rate = x; return profit-capital*rate/100
    if task == "退出资产对经济增加值的影响":
        lost_profit, released_capital, rate = x; return -lost_profit+released_capital*rate/100
    if task == "收入增长率":
        prior, current = x; return (current-prior)/prior*100
    if task == "客户留存率":
        start, end, new = x; return (end-new)/start*100
    if task == "准时交付率":
        total, on_time = x; return on_time/total*100
    if task == "产品不良率":
        total, bad = x; return bad/total*100
    if task == "流程周期改善率":
        old, new = x; return (old-new)/old*100
    if task == "培训通过率":
        total, passed = x; return passed/total*100
    if task == "经营资产报酬率":
        profit, capital = x; return profit/capital*100
    if task == "剩余收益":
        profit, capital, rate = x; return profit-capital*rate/100
    if task == "目标经济增加值倒推利润":
        capital, rate, target = x; return target+capital*rate/100
    raise ValueError(f"Unknown chapter 20 calculation {task}")


def visible_case20(question):
    x = numbers(question["material"])
    task = question["decisionTask"]
    if task == "收入与利润质量":
        old_sales, old_profit, sales, profit = x; return [(sales-old_sales)/old_sales*100, profit/sales*100]
    if task == "客户留存与交付":
        start, end, new, total, ontime = x; return [(end-new)/start*100, ontime/total*100]
    if task == "质量改善":
        old_total, old_bad, total, bad = x; return [bad/total*100, old_bad/old_total*100-bad/total*100]
    if task == "培训与员工流失":
        total, passed, start, end, left = x; return [passed/total*100, left/((start+end)/2)*100]
    if task == "项目经济增加值比较":
        rate, profit_a, capital_a, profit_b, capital_b = x
        return [profit_a-capital_a*rate/100, profit_b-capital_b*rate/100]
    if task == "战略目标与指标":
        assert not x; return [None, None]
    if task == "标杆比较":
        output, hours, benchmark = x; return [output/hours, hours-output/benchmark]
    if task == "绩效综合评分":
        a, b, c, d, wa, wb, wc, wd = x; return [(a*wa+b*wb+c*wc+d*wd)/100, None]
    raise ValueError(f"Unknown chapter 20 case {task}")
