# -*- coding: utf-8 -*-

import datetime
import numpy

class MemberSharesCurve(object):
    """ Provides the shares that are active at a give
        day, or either daily or hourly in a date span.
        You need to feed this object with an investment
        provider.
    """
    def __init__(self, investments):
        self._provider = investments

    def atDay(self, day, member=None):
        return sum(
            investment.shares
            for investment in self._provider.shareContracts()
            if (member is None or investment['member'] == member)
            and investment.activationEnd >= day
            and investment.activationStart <= day
        )

    def hourly(self, start, end, member=None):
        if end<start:
            return numpy.array([], dtype=int)

        hoursADay=25
        nDays=(end-start).days+1
        result = numpy.zeros(nDays*hoursADay, dtype=numpy.int)
        for i in xrange(nDays):
            day=start+datetime.timedelta(days=i)
            result[i*hoursADay:(i+1)*hoursADay] = self.atDay(day, member=member)
        return result

class PlantSharesCurve(MemberSharesCurve):
    def __init__(self,shares):
        self.shares = shares

    def atDay(self, day, member=None):
        return self.shares

    def hourly(self, start, end):
        return super(PlantSharesCurve, self).hourly(start,end,None)

# vim: ts=4 sw=4 et
