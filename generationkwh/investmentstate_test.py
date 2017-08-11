# -*- coding: utf-8 -*-

from generationkwh.investmentstate import InvestmentState
import unittest
from yamlns import namespace as ns
from .isodates import isodate

# Readable verbose testcase listing
unittest.TestCase.__str__ = unittest.TestCase.id


class InvestmentState_Test(unittest.TestCase):

    user = "MyUser"
    timestamp = "2000-01-01 00:00:00.123435"
    logprefix = "[{} {}] ".format(timestamp, user)

    def assertNsEqual(self, dict1, dict2):
        def parseIfString(nsOrString):
            if type(nsOrString) in (dict, ns):
                return nsOrString
            return ns.loads(nsOrString)

        def sorteddict(d):
            if type(d) not in (dict, ns):
                return d
            return ns(sorted(
                (k, sorteddict(v))
                for k,v in d.items()
                ))
        dict1 = sorteddict(parseIfString(dict1))
        dict2 = sorteddict(parseIfString(dict2))

        return self.assertMultiLineEqual(dict1.dump(), dict2.dump())

    def assertLogEquals(self, log, expected):
        for x in log.splitlines():
            self.assertRegexpMatches(x,
                u'\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}.\\d+ [^]]+\\] .*',
                u"Linia de log con formato no estandard"
            )

        logContent = ''.join(
                x.split('] ')[1]+'\n'
                for x in log.splitlines()
                if u'] ' in x
                )
        self.assertMultiLineEqual(logContent, expected)

    def assertChangesEqual(self, inv, attr, expectedlog):
        changes=inv.changed()
        log = changes.pop('log','')
        self.assertNsEqual(changes, attr)
        if expectedlog is None: return
        self.assertMultiLineEqual(log,
            self.logprefix + expectedlog + u"previous log\n"
            )

    def test_changes_by_default_noChange(self):
        inv = InvestmentState()
        self.assertNsEqual(inv.changed(), """\
            {}
            """)

    def test_order(self):
        inv = InvestmentState("MyUser", "2000-01-01 00:00:00.123435")

        inv.order(
            date = isodate('2000-01-01'),
            ip = '8.8.8.8',
            amount = 300.0,
            iban = 'ES7712341234161234567890',
        )
        changes=inv.changed()
        log = changes.pop('log')
        self.assertNsEqual(inv.changed(), """\
            order_date: 2000-01-01
            purchase_date: False
            first_effective_date: False
            last_effective_date: False
            active: True
            nominal_amount: 300.0
            paid_amount: 0.0
            """)

        self.assertMultiLineEqual(log,
            self.logprefix + u"FORMFILLED: "
            u"Formulari omplert des de la IP 8.8.8.8, "
            u"Quantitat: 300 €, IBAN: ES7712341234161234567890\n")


    def test_order_withNoIban(self):
        inv = InvestmentState("MyUser", "2000-01-01 00:00:00.123435")

        inv.order(
            date = isodate('2000-01-01'),
            ip = '8.8.8.8',
            amount = 300.0,
            iban = '', # This changes
        )
        changes=inv.changed()
        log = changes.pop('log','')
        self.assertNsEqual(inv.changed(), """\
            order_date: 2000-01-01
            purchase_date: False
            first_effective_date: False
            last_effective_date: False
            active: True
            nominal_amount: 300.0
            paid_amount: 0.0
            """)

        self.assertMultiLineEqual(log,
            self.logprefix + u"FORMFILLED: "
            u"Formulari omplert des de la IP 8.8.8.8, "
            u"Quantitat: 300 €, IBAN: None\n")


    def test_pay(self):
        inv = InvestmentState("MyUser", "2000-01-01 00:00:00.123435", dict(
            nominal_amount = 300.0,
            paid_amount = 0.0,
            log = "previous log\n",
        ))

        inv.pay(
            date = isodate('2016-05-01'),
            amount = 300.0,
            iban = 'ES7712341234161234567890',
            move_line_id = 666,
        )
        self.assertChangesEqual(inv, """\
            purchase_date: 2016-05-01
            first_effective_date: 2017-05-01
            #last_effective_date: 2041-05-01 # TODO Add this
            paid_amount: 300.0
            """,
            u"PAID: Pagament de 300 € remesat "
            u"al compte ES7712341234161234567890 [666]\n"
            )

    def test_pay_alreadyPaid(self):
        inv = InvestmentState("MyUser", "2000-01-01 00:00:00.123435", dict(
            nominal_amount = 300.0,
            paid_amount = 300.0,
            log = "previous log\n",
        ))

        with self.assertRaises(Exception) as ctx:
            inv.pay(
                date = isodate('2016-05-01'),
                amount = 300.0,
                iban = 'ES7712341234161234567890',
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
            "Already paid")
        self.assertChangesEqual(inv, """\
            paid_amount: 600.0
            """,
            # TODO: Log the error!
            u"PAID: Pagament de 300 € remesat "
            u"al compte ES7712341234161234567890 [666]\n"
            )

    def test_pay_wrongAmount(self):
        inv = InvestmentState("MyUser", "2000-01-01 00:00:00.123435", dict(
            nominal_amount = 300.0,
            paid_amount = 0.0,
            log = "previous log\n",
        ))

        with self.assertRaises(Exception) as ctx:
            inv.pay(
                date = isodate('2016-05-01'),
                amount = 400.0, # Wrong!
                iban = 'ES7712341234161234567890',
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
            "Wrong payment")
        self.assertChangesEqual(inv, """\
            paid_amount: 400.0
            """,
            # TODO: Log the error!
            u"PAID: Pagament de 400 € remesat "
            u"al compte ES7712341234161234567890 [666]\n"
            )


    def test_fistEffectiveDate(self):
        self.assertEqual(isodate('2017-04-28'),
            InvestmentState.firstEffectiveDate(isodate('2016-04-28')))

    def test_fistEffectiveDate_pioners(self):
        self.assertEqual(isodate('2017-03-28'),
            InvestmentState.firstEffectiveDate(isodate('2016-04-27')))


    def test_unpay(self):
        inv = InvestmentState("MyUser", "2000-01-01 00:00:00.123435", dict(
            nominal_amount = 300.0,
            paid_amount = 300.0,
            log = "previous log\n",
        ))

        inv.unpay(
            amount = 300.0,
            move_line_id = 666,
        )
        self.assertChangesEqual(inv, """\
            purchase_date: False
            first_effective_date: False
            last_effective_date: False
            paid_amount: 0.0
            """,
            u"REFUNDED: Devolució del pagament remesat [666]\n"
            )


# vim: ts=4 sw=4 et
