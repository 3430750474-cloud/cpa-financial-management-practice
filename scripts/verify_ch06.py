"""Independently recalculate chapter 6 authored answers from visible inputs."""
import re


def visible_ch06(q):
    x = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", q["stem"])]
    task = q["decisionTask"]
    if task == "看涨期权到期价值":
        strike, spot=x; return max(spot-strike,0)
    if task == "看跌期权到期价值":
        strike, spot=x; return max(strike-spot,0)
    if task == "看涨期权空头到期价值":
        strike, spot=x; return -max(spot-strike,0)
    if task == "看涨期权多头净损益":
        premium, strike, spot=x; return max(spot-strike,0)-premium
    if task == "看跌期权多头净损益":
        premium, strike, spot=x; return max(strike-spot,0)-premium
    if task == "备兑看涨组合损益":
        purchase, premium, strike, spot=x; return spot-purchase+premium-max(spot-strike,0)
    if task == "保护性看跌组合损益":
        purchase, premium, strike, spot=x; return spot-purchase+max(strike-spot,0)-premium
    if task == "期权时间溢价":
        price, spot, strike=x; return price-max(spot-strike,0)
    if task == "看涨看跌平价求看涨价值":
        spot, strike, put, rate=x; return put+spot-strike/(1+rate/100)
    if task == "看涨看跌平价求看跌价值":
        spot, strike, call, rate=x; return call-spot+strike/(1+rate/100)
    if task == "复制组合套期保值比率":
        start, up, down, strike, call_up, call_down=x; return (call_up-call_down)/(up-down)
    if task == "复制组合借款现值":
        delta, down, payoff, rate=x; return (delta*down-payoff)/(1+rate/100)
    if task == "风险中性上行概率":
        up, down, rate=x; return (1+rate/100-down)/(up-down)*100
    if task == "风险中性期权价值":
        probability, call_up, call_down, rate=x; return (probability/100*call_up+(1-probability/100)*call_down)/(1+rate/100)
    if task == "扩张期权行权收益":
        value, investment=x; return max(value-investment,0)
    if task == "放弃期权决策":
        salvage, continuation=x; return max(salvage,continuation)
    if task == "延迟投资权利":
        investment, high, low, probability, rate=x
        return (probability/100*max(high-investment,0)+(1-probability/100)*max(low-investment,0))/(1+rate/100)
    raise ValueError(f"Unknown chapter 6 task: {task}")
