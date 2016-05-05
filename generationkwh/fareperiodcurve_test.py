# -*- coding: utf-8 -*-

from fareperiodcurve import FarePeriodCurve, libfacturacioatr
import unittest
import datetime
from .isodates import isodate

class HolidaysProvidersMockup(object):
    def get(self, start, stop):
        return self.holidays

    def set(self, holidays):
        self.holidays= [isodate(holiday) for holiday in holidays]

    def __init__(self, holidays=[]):
        self.set(holidays)

@unittest.skipIf(libfacturacioatr is None,
    'non-free libfacturacioatr module is not installed' )

class FarePeriodCurve_Test(unittest.TestCase):
    def setupCurve(self,start_date,end_date,fare,period,holidays=[]):
        
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup(holidays)
            )


        return p.mask(isodate(start_date), isodate(end_date), fare, period)

        
    def assertArrayEqual(self, result, expected):
        # TODO: Change this as we turn it into a numpy array
        return self.assertEqual(list(result), expected)

    def test_20A_singleMonth(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-12-01', '2015-12-31', '2.0A', 'P1')

        self.assertArrayEqual(mask, 
            + 31 * [ [1]*24+[0] ]
            )

    def test_30A_P1_singleMonth(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-12-01', '2015-12-31', '3.0A', 'P1')

        self.assertArrayEqual(mask,
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ]
            )

    def test_30A_P3_singleMonth(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-12-01', '2015-12-31', '3.0A', 'P3')

        self.assertArrayEqual(mask,
            + 4 * [ [1]*8 + [0]*17 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [1]*8 + [0]*17 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [1]*8 + [0]*17 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [1]*8 + [0]*17 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [1]*8 + [0]*17 ]
            )

    def test_30A_P1_singleMonth_withHolidays(self):
        holidays = HolidaysProvidersMockup([
            '2015-12-25',
        ])
        p = FarePeriodCurve(holidays=
            holidays
        )

        mask =self.setupCurve('2015-12-01', '2015-12-31', '3.0A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ] # Christmasts
            + 3 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ]
            )

    def test_30A_P1_startedMonth(self):
        holidays = HolidaysProvidersMockup([
            '2015-12-25',
        ])
        p = FarePeriodCurve(holidays=
            holidays,
        )

        mask = self.setupCurve('2015-12-7', '2015-12-31', '3.0A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ] # Christmasts
            + 3 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ]
            )

    def test_30A_P1_partialMonth(self):
        mask = self.setupCurve('2015-12-7', '2015-12-27', '3.0A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ] # Christmasts
            + 3 * [ [0]*25 ]
            )

    def test_30A_P1_singleDay(self):
        mask = self.setupCurve('2015-12-25', '2015-12-25', '3.0A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 1 * [ [0]*25 ]
            )

    def test_30A_P1_accrossMonths(self):

        mask = self.setupCurve('2015-11-25', '2015-12-25', '3.0A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 3 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ] # Christmasts
            + 1 * [ [0]*25 ]
            )

    def test_get_class_by_code(self):
        import libfacturacioatr.tarifes as tarifes
        for code, clss in [
            ('2.0A', tarifes.Tarifa20A),
            ('3.0A', tarifes.Tarifa30A),
            ('2.0DHA', tarifes.Tarifa20DHA),
            ]:
            self.assertEqual(
                tarifes.Tarifa.get_class_by_code(code), clss)

        with self.assertRaises(KeyError):
            tarifes.Tarifa.get_class_by_code("Bad")

    def test_get_class_by_code_fromPool(self):
        import libfacturacioatr.pool.tarifes as tarifespool
        for code, clss in [
            ('2.0A', tarifespool.Tarifa20APool),
            ('3.0A', tarifespool.Tarifa30APool),
            ('2.0DHA', tarifespool.Tarifa20DHAPool),
            ]:
            self.assertEqual(
                tarifespool.TarifaPool.get_class_by_code(code), clss)

        with self.assertRaises(KeyError):
            tarifespool.TarifaPool.get_class_by_code("Bad")

# vim: ts=4 sw=4 et
