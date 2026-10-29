"""Recalculate chapter 10 authored answers from their displayed inputs."""
import re


def visible_ch10(q):
    x = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", q["stem"])]
    task = q["decisionTask"]
    if task == "剩余股利政策":
        profit, investment, equity=x; return profit-investment*equity/100
    if task == "股利支付率":
        profit, dividend=x; return dividend/profit*100
    if task == "股东税后现金股利":
        shares, dividend, tax=x; return shares*dividend*(1-tax/100)
    if task == "留存收益增量":
        profit, dividend=x; return profit-dividend
    if task == "股票股利新增股数":
        shares, rate=x; return shares*rate/100
    if task == "股票股利除权参考价":
        price, old, extra=x; return old*price/(old+extra)
    if task == "股票分割后的股数":
        shares, old, new=x; return shares*new/old
    if task == "股票分割后的理论股价":
        price, old, new=x; return price*old/new
    if task == "回购股数":
        price, cash=x; return cash/price
    if task == "回购后每股收益":
        profit, original, repurchase=x; return profit/(original-repurchase)
    if task == "现金股利除息参考价":
        price, dividend=x; return price-dividend
    raise ValueError(f"Unknown chapter 10 task: {task}")
