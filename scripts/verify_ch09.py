"""Independent calculations from the numbers visible in the authored stems."""
import re


def manual_ch09_visible(question):
    nums = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", question["stem"])]
    task = question["decisionTask"]
    if task == "年度付息债券估值":
        face, coupon, years, rate = nums
        return sum(face*coupon/100/(1+rate/100)**t for t in range(1, int(years)+1)) + face/(1+rate/100)**years
    if task == "补偿性余额借款":
        loan, rate, balance = nums
        return loan*rate/100/(loan*(1-balance/100))*100
    if task == "半年付息债券估值":
        face, coupon, years, periods, rate = nums
        assert periods == years*2
        return sum(face*coupon/200/(1+rate/200)**t for t in range(1, int(periods)+1)) + face/(1+rate/200)**periods
    if task == "股票发行净筹资额":
        shares, price, fee = nums
        return shares*price*(1-fee/100)
    if task == "零息债券估值":
        face, years, rate = nums
        return face/(1+rate/100)**years
    if task == "配股除权价格":
        old, price, new, market = nums
        return (old*market+new*price)/(old+new)
    if task == "一次还本付息债券估值":
        face, coupon, years, rate = nums
        return face*(1+coupon/100*years)/(1+rate/100)**years
    if task == "可转换债券转换股数":
        face, price = nums
        return face/price
    if task == "到期收益率":
        face, coupon, years, price = nums
        low, high = 0.0, 1.0
        for _ in range(100):
            r = (low+high)/2
            present = sum(face*coupon/100/(1+r)**t for t in range(1, int(years)+1)) + face/(1+r)**years
            if present > price: low = r
            else: high = r
        return (low+high)/2*100
    if task == "租金现值":
        years, payment, rate = nums
        return sum(payment/(1+rate/100)**t for t in range(1, int(years)+1))
    if task == "债券持有期收益率":
        buy, face, coupon, sell = nums
        return (sell-buy+face*coupon/100)/buy*100
    if task == "可转换债券转换溢价率":
        price, shares, stock = nums
        return (price-shares*stock)/(shares*stock)*100
    if task == "等额租金":
        cost, rate, years = nums
        return cost/sum(1/(1+rate/100)**t for t in range(1, int(years)+1))
    if task == "配股权价值":
        old, market, old_again, price, new = nums
        assert old == old_again
        return market-(old*market+new*price)/(old+new)
    if task == "租赁保证残值与租金":
        cost, years, residual, rate = nums
        factor = sum(1/(1+rate/100)**t for t in range(1, int(years)+1))
        return (cost-residual/(1+rate/100)**years)/factor
    raise ValueError(f"Unsupported chapter 9 question: {task}")
