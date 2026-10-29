"""Independently recalculate chapter 3 authored answers from displayed data."""
import math
import re


def visible_ch03(q):
    x = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", q["stem"])]
    task = q["decisionTask"]
    if task == "普通年金现值":
        years, payment, rate=x; return sum(payment/(1+rate/100)**t for t in range(1,int(years)+1))
    if task == "普通年金终值":
        years, payment, rate, end=x; assert years==end; return sum(payment*(1+rate/100)**t for t in range(int(years)))
    if task == "预付年金现值":
        years, payment, rate=x; return sum(payment/(1+rate/100)**t for t in range(int(years)))
    if task == "预付年金终值":
        years, payment, rate, end=x; assert years==end; return sum(payment*(1+rate/100)**t for t in range(1,int(years)+1))
    if task == "永续年金现值":
        payment, rate=x; return payment/(rate/100)
    if task == "递延永续年金现值":
        first, payment, rate=x; return payment/(rate/100)/(1+rate/100)**(first-1)
    if task == "名义利率分期复利":
        principal, rate, years=x; return principal*(1+rate/400)**(4*years)
    if task == "名义与实际利率":
        nominal, inflation, *_=x; return ((1+nominal/100)/(1+inflation/100)-1)*100
    if task == "期望报酬率":
        p1, r1, p2, r2=x; return (p1*r1+p2*r2)/100
    if task == "离散报酬率标准差":
        r1,r2,p=x; mean=(p*r1+(100-p)*r2)/100; return math.sqrt((p*(r1-mean)**2+(100-p)*(r2-mean)**2)/100)
    if task == "报酬率变异系数":
        sigma, mean=x; return sigma/mean
    if task == "投资组合期望报酬率":
        w1,r1,w2,r2=x; return (w1*r1+w2*r2)/100
    if task == "投资组合贝塔系数":
        w1,b1,w2,b2=x; return (w1*b1+w2*b2)/100
    if task == "两资产协方差":
        sigma1,sigma2,rho=x; return sigma1/100*sigma2/100*rho
    if task == "不相关组合标准差":
        weight,sigma1,sigma2,rho=x; w=weight/100; return math.sqrt((w*sigma1)**2+((1-w)*sigma2)**2+2*w*(1-w)*rho*sigma1*sigma2)
    if task == "资本资产定价模型":
        riskfree,market,beta=x; return riskfree+beta*(market-riskfree)
    if task == "市场风险溢价":
        market,riskfree=x; return market-riskfree
    if task == "固定增长股票价值":
        dividend,growth,required=x; return dividend/((required-growth)/100)
    raise ValueError(f"Unknown chapter 3 task: {task}")
