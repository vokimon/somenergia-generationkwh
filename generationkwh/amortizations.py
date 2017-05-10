# -*- coding:utf8 -*-

def pendingAmortization(purchase_date, current_date, investment_amount, amortized_amount):
    from plantmeter.isodates import isodate
    from dateutil.relativedelta import relativedelta

    current_date = isodate(current_date)
    purchase_date = isodate(purchase_date)
    years = relativedelta(current_date, purchase_date).years

    yearly_amortitzation = investment_amount / 25

    if years < 2:
        return 0

    if years >= 25:
        return investment_amount - amortized_amount

    return (years-1)*yearly_amortitzation - amortized_amount

# vim: et ts=4 sw=4
