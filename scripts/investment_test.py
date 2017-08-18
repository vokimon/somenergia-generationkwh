#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

dbconfig = None
try:
    import dbconfig
except ImportError:
    pass

from datetime import datetime, timedelta
from yamlns import namespace as ns
import erppeek_wst


@unittest.skipIf(not dbconfig, "depends on ERP")
class Investment_OLD_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Soci = self.erp.SomenergiaSoci
        self.Investment = self.erp.GenerationkwhInvestment
        self.AccountInvoice = self.erp.AccountInvoice
        self.PaymentLine = self.erp.PaymentLine
        self.Investment.dropAll()

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()

    #TODO: move this in a utils class (copy pasted from Investment_Amortization_Test
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

    #TODO: Implemented in Investment_Amortization_Test
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

    def test__effective_investments_tuple__noInvestments(self):
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [])

    def test__create_from_accounting__all(self):
        # Should fail whenever Gijsbert makes further investments
        # Update: We add the fiscal year closing investments

        self.Investment.create_from_accounting(1, None, None, 0, None)

        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
                #[1, '2016-05-19', False, -86], #Fiscal year closing
                #[1, '2016-05-19', False, 86]  #Fiscal year closing
            ])

    def test__create_from_accounting__restrictingFirst(self):
        self.Investment.create_from_accounting(1, '2015-07-01', '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__create_from_accounting__seesUnactivePartner(self):

        self.Soci.write(1, dict(active=False))
        self.Investment.create_from_accounting(1, '2015-07-01', '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__create_from_accounting__restrictingLast(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
            ])

    def test__create_from_accounting__noWaitingDays(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', None, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, False, False,  1],
                [1, False, False, 30],
                [1, False, False, 30],
            ])

    def test__create_from_accounting__nonZeroWaitingDays(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 1, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', False, 15],
                [1, '2015-07-01', False, 10],
                [1, '2015-07-30', False,  1],
                [1, '2015-11-21', False, 30],
                [1, '2015-11-21', False, 30],
            ])

    def test__create_from_accounting__nonZeroExpireYears(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 1, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, '2015-07-30', '2017-07-30',  1],
                [1, '2015-11-21', '2017-11-21', 30],
                [1, '2015-11-21', '2017-11-21', 30],
            ])

    def test__create_from_accounting__severalMembers(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 0, None)
        self.Investment.create_from_accounting(38, None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
                [38, '2015-06-30', False, 3],
                [38, '2015-10-13', False, 1],
                [38, '2015-10-20', False, -1],
            ])

    def test__create_from_accounting__severalMembersArray_reorderbyPurchase(self):
        self.Investment.create_from_accounting([1,38], None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [38, '2015-06-30', False, 3],
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [38, '2015-10-13', False, 1],
                [38, '2015-10-20', False, -1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__create_from_accounting__noMemberTakesAll(self):
        self.Investment.create_from_accounting(None, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(1, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])
        self.assertEqual(
            self.Investment.effective_investments_tuple(38, None, None),
            [
                [38, '2015-06-30', False, 3],
            ])

    def test__create_from_accounting__ignoresExisting(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', None, None)
        self.Investment.create_from_accounting(1, None, '2015-07-29', 0, None)
        self.Investment.create_from_accounting(1, None, '2015-11-20', 0, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', '2017-11-20', 30],
                [1, '2015-11-20', '2017-11-20', 30],
            ])

    def test__effective_investments_tuple__filtersByMember(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 0, None)
        self.Investment.create_from_accounting(38, None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(1, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__effective_investments_tuple__filtersByFirst_removesUnstarted(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', None, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '2017-07-20', None),
            [
                #[1, False, False, 15], # Unstarted
                #[1, False, False, 10], # Unstarted
            ])

    def test__effective_investments_tuple__filtersByFirst_keepsUnexpiredWhicheverTheDate(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '4017-07-20', None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])

    def test__effective_investments_tuple__filtersByFirst_passesNotYetExpired(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '2017-06-30', None),
            [
                [1, '2015-06-30', '2017-06-30', 15],
                [1, '2015-06-30', '2017-06-30', 10],

            ])

    def test__effective_investments_tuple__filtersByFirst_removesExpired(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '2017-07-01', None),
            [
                #[1, '2015-06-30', '2017-06-30', 15],
                #[1, '2015-06-30', '2017-06-30', 10],

            ])

    def test__effective_investments_tuple__filtersByLast_removesUnstarted(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', None, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, '2015-11-19'),
            [
                #[1, False, False, 15], # Unstarted
                #[1, False, False, 10], # Unstarted
            ])

    def test__effective_investments_tuple__filtersByLast_includesStarted(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, '2015-06-30'),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])

    def test__effective_investments_tuple__filtersByLast_excludesStartedLater(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, '2015-06-29'),
            [
                #[1, '2015-06-30', False, 15], # Not yet started
                #[1, '2015-06-30', False, 10], # Not yet started
            ])

    def test__effective_investments_tuple__deactivatedNotShown(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        toBeDeactivated=self.Investment.search([
            ('member_id','=',1),
            ('nshares','=',10),
            ])[0]
        self.Investment.deactivate(toBeDeactivated)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                #[1, '2015-06-30', False, 10], # deactivated
                [1, '2015-07-29', False,  1],
            ])

    def test__create_from_accounting__unactiveNotRecreated(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        toBeDeactivated=self.Investment.search([
            ('member_id','=',1),
            ('nshares','=',10),
            ])[0]
        self.Investment.deactivate(toBeDeactivated)
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                #[1, '2015-06-30', False, 10], # still deactivated
                [1, '2015-07-29', False,  1],
            ])

    def test__set_effective__wait(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, None, 1, None, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', False, 15],
                [1, '2015-07-01', False, 10],
                [1, '2015-07-30', False,  1],
            ])

    def test__set_effective__waitAndExpire(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, None, 1, 2, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, '2015-07-30', '2017-07-30',  1],
            ])

    def test__set_effective__purchasedEarlierIgnored(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective('2015-07-01', None, 1, 2, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, '2015-07-30', '2017-07-30',  1],
            ])

    def test__set_effective__purchasedLaterIgnored(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, '2015-06-30', 1, 2, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, False, False,  1],
            ])

    def test__set_effective__alreadySetIgnored(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, '2015-06-30', 1, 2, False)
        self.Investment.set_effective(None, None, 10, 4, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, '2015-08-08', '2019-08-08',  1],
            ])

    def test__set_effective__alreadySetForced(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, '2015-06-30', 1, 2, False)
        self.Investment.set_effective(None, None, 10, 4, True)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-10', '2019-07-10', 15],
                [1, '2015-07-10', '2019-07-10', 10],
                [1, '2015-08-08', '2019-08-08',  1],
            ])

    # TODO: extent to move expire

    def test__member_has_effective__noInvestments(self):
        self.assertFalse(
            self.Investment.member_has_effective(None, None, None))

    def test__member_has_effective__insideDates(self):
        self.Investment.create_from_accounting(1,'2010-01-01', '2015-07-03',
            1, None)
        self.assertTrue(
            self.Investment.member_has_effective(1,'2015-07-01','2015-07-01'))
    
@unittest.skipIf(not dbconfig, "depends on ERP")
class Investment_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Invoice = self.erp.AccountInvoice
        self.InvoiceLine = self.erp.AccountInvoiceLine
        self.Partner = self.erp.ResPartner
        self.Investment = self.erp.GenerationkwhInvestment
        self.PaymentLine = self.erp.PaymentLine
        self.PaymentMandate = self.erp.PaymentMandate
        self.ResPartnerAddress = self.erp.ResPartnerAddress
        self.ResPartner = self.erp.ResPartner
        self.MailMockup = self.erp.GenerationkwhMailmockup
        self.MailMockup.activate()

    def tearDown(self):
        self.MailMockup.deactivate()
        self.erp.rollback()
        self.erp.close()


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
        
    def test__create_from_form__allOk(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        self.assertTrue(id)

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        
        self.Investment.unlink(id)

        self.assertLogEquals(log,
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.123, Quantitat: 4000 €, IBAN: ES7712341234161234567890\n'
            )
        
        self.assertRegexpMatches(name,r'^GKWH[0-9]{5}$')
        self.assertNsEqual(investment, """
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: false
            first_effective_date: false
            last_effective_date: false
            nshares: 40
            amortized_amount: 0.0
            move_line_id: false
            active: true
            """.format(
                id=id,
                **self.personalData
                ))
            

    @unittest.skip('Not implemented')
    def test__create_from_form__whenBadOrderDate(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            'baddate', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.assertFalse(id) # ??

    @unittest.skip('Not implemented')
    def test__create_from_form__whenNotAMember(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.assertFalse(id) # ??

    def test__create_from_form__withNonDivisibleAmount(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4003,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.assertFalse(id)
    
    def test__mark_as_paid__singleInvestment(self):
    
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        self.Investment.mark_as_paid([id], '2017-01-03')

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        self.Investment.unlink(id)

        self.assertLogEquals(log,
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.123, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )
        
        self.assertNsEqual(investment, """
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: '2017-01-03' # Changed!
            first_effective_date: '2018-01-03'
            last_effective_date: '2042-01-03'
            nshares: 20
            amortized_amount: 0.0
            move_line_id: false
            active: true
            """.format(
                id=id,
                **self.personalData
                ))

    def test__mark_as_paid__samePurchaseDateSetToAll(self):
    
        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02', # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        self.Investment.mark_as_paid([id1,id2], '2017-01-03')
        
        result = self.Investment.read(
            [id1,id2],
            ['purchase_date'],
            order='id')
        
        self.assertNsEqual(ns(data=result), """\
            data:
            - purchase_date: '2017-01-03'
              id: {id1}
            - purchase_date: '2017-01-03'
              id: {id2}
            """.format(id1=id1, id2=id2))

    def test__mark_as_paid__oldLogKept(self):
    
        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02', # order_date
            2000,
            '10.10.23.2',
            'ES7712341234161234567890',
            )

        self.Investment.mark_as_paid([id1,id2], '2017-01-03')
        
        result = self.Investment.read([id1,id2], ['log'], order='id')
        
        self.assertLogEquals(result[0]['log'],
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.1, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )
        
        self.assertLogEquals(result[1]['log'],
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.2, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def test__mark_as_unpaid__singleInvestment(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        self.Investment.mark_as_paid([id], '2017-01-03')
        self.Investment.mark_as_unpaid([id])

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        self.Investment.unlink(id)

        self.assertLogEquals(log,
            u'REFUNDED: Devolució del pagament remesat de 2000 € [None]\n'
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.123, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
                             )

        self.assertNsEqual(investment, """
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: false # Changed!
            first_effective_date: false
            last_effective_date: false
            nshares: 20
            amortized_amount: 0.0
            move_line_id: false
            active: true
            """.format(
            id=id,
            **self.personalData
        ))

    def test__mark_as_unpaid__samePurchaseDateSetToAll(self):

        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02',  # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        self.Investment.mark_as_paid([id1, id2], '2017-01-03')
        self.Investment.mark_as_unpaid([id1, id2])

        result = self.Investment.read(
            [id1, id2],
            ['purchase_date'],
            order='id')

        self.assertNsEqual(ns(data=result), """\
            data:
            - purchase_date: false
              id: {id1}
            - purchase_date: false
              id: {id2}
            """.format(id1=id1, id2=id2))

    def test__mark_as_unpaid__oldLogKept(self):

        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02',  # order_date
            2000,
            '10.10.23.2',
            'ES7712341234161234567890',
        )

        self.Investment.mark_as_paid([id1, id2], '2017-01-03')
        self.Investment.mark_as_unpaid([id1, id2])

        result = self.Investment.read([id1, id2], ['log'], order='id')

        self.assertLogEquals(result[0]['log'],
            u'REFUNDED: Devoluci\xf3 del pagament remesat de 2000 € [None]\n'
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.1, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

        self.assertLogEquals(result[1]['log'],
            u'REFUNDED: Devoluci\xf3 del pagament remesat de 2000 € [None]\n'
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.2, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def assertInvoiceInfoEqual(self, invoice_id, expected):
        def proccesLine(line):
            line = ns(line)
            line.product_id = line.product_id[1]
            line.account_id = line.account_id[1]
            line.uos_id = line.uos_id[1]
            line.note = ns.loads(line.note) if line.note else line.note
            del line.id
            return line

        invoice = ns(self.Invoice.read(invoice_id, [
            'amount_total',
            'amount_untaxed',
            'partner_id',
            'type',
            'name',
            'journal_id',
            'account_id',
            'partner_bank',
            'payment_type',
            'date_invoice',
            'invoice_line',
            'check_total',
            'origin',
            'sii_to_send',
        ]))
        invoice.journal_id = invoice.journal_id[1]
        invoice.partner_bank = invoice.partner_bank[1] if invoice.partner_bank else "None"
        invoice.account_id = invoice.account_id[1]
        invoice.invoice_line = [
            proccesLine(line)
            for line in self.InvoiceLine.read(invoice.invoice_line, [])
            ]
        self.assertNsEqual(invoice, expected)

    def test__create_initial_invoices(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        invoice_ids, errs =  self.Investment.create_initial_invoices([id])

        self.assertFalse(errs)
        self.assertTrue(invoice_ids)

        investment = self.Investment.browse(id)

        self.assertInvoiceInfoEqual(invoice_ids[0], """\
            account_id: 410000{p.nsoci:0>6s} {p.surname}, {p.name}
            amount_total: 2000.0
            amount_untaxed: 2000.0
            check_total: 2000.0
            date_invoice: '{invoice_date}'
            id: {id}
            invoice_line:
            - origin: false
              uos_id: PCE
              account_id: 163500{p.nsoci:0>6s} {p.surname}, {p.name}
              name: 'Inversió {investment_name} '
              invoice_id:
              - {id}
              - 'CI:  {investment_name}-FACT'
              price_unit: 100.0
              price_subtotal: 2000.0
              invoice_line_tax_id: []
              note: false
              discount: 0.0
              account_analytic_id: false
              quantity: 20.0
              product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
            journal_id: Factures GenerationkWh
            name: {investment_name}-FACT
            origin: {investment_name}
            partner_bank: {iban}
            partner_id:
            - {p.partnerid}
            - {p.surname}, {p.name}
            payment_type:
            - 1
            - Recibo domiciliado
            sii_to_send: false
            type: out_invoice
            """.format(
            invoice_date=datetime.today().strftime("%Y-%m-%d"),
            id=invoice_ids[0],
            iban='ES77 1234 1234 1612 3456 7890',
            year=2018,
            investment_name=investment.name,
            p=self.personalData,
            investment_id=id
            ))

    def test__create_initial_invoices__twice(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        inv = self.Investment.read(id, ['name'])

        self.Investment.create_initial_invoices([id])

        result = self.Investment.create_initial_invoices([id])

        self.assertEqual(result, [[], [
            "Initial Invoice {name}-FACT already exists".format(**inv)
            ]])

    def test__create_initial_invoices__withUnnamedInvestment(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2016-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        self.Investment.write(id, dict(
            name=None)
            )

        invoice_ids, errs = self.Investment.create_initial_invoices([id])

        invoice = self.Invoice.browse(invoice_ids[0])
        self.assertEqual(invoice.name,
            "GENKWHID{}-FACT".format(id))

    def test__create_initial_invoices__errorWhenNoBank(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Partner.write(self.personalData.partnerid,dict(bank_inversions = False))
        result = self.Investment.create_initial_invoices([id])
        self.assertEqual(result, [[], [
            "Partner '{surname}, {name}' has no investment bank account"
                .format(**self.personalData).decode('utf-8')
            ]])

    def test__create_initial_invoices__investmentWithPurchaseDate(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2016-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        inv = self.Investment.read(id,['name'])

        self.Investment.mark_as_paid([id], '2016-01-04')
        result = self.Investment.create_initial_invoices([id])

        self.assertEquals(result, [[], [
            "Investment {name} was already paid".format(**inv),
            ]])

    def test__create_initial_invoices__inactiveInvestment(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2016-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        inv = self.Investment.read(id,['name'])

        self.Investment.write(id, {'active':False})

        result = self.Investment.create_initial_invoices([id])

        self.assertEquals(result, [[], [
            "Investment {name} is inactive".format(**inv),
            ]])


    def test__create_initial_invoices__multiInvestments(self):

        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02', # order_date
            500,
            '10.10.23.2',
            'ES7712341234161234567890',
            )

        invoice_ids, errs = self.Investment.create_initial_invoices([id1, id2])

        self.assertEqual(2,len(invoice_ids))


    def test__create_initial_invoices__OkAndKo(self):
        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-02-02', # order_date
            3000,
            '10.10.23.2',
            'ES7712341234161234567890',
            )
        investment = self.Investment.read(id1,['name'])
        self.Investment.write(id1, {'active':False})

        invoice_ids, errs = self.Investment.create_initial_invoices([id1,id2])

        self.assertEqual(errs, [
            "Investment {name} is inactive".format(**investment),
            ])
        self.assertEqual(len(invoice_ids), 1)


    def test__create_initial_invoices__twoErrors(self):
        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-02-02', # order_date
            3000,
            '10.10.23.2',
            'ES7712341234161234567890',
            )
        investment1 = self.Investment.read(id1,['name'])
        investment2 = self.Investment.read(id2,['name'])

        self.Investment.write(id1, {'active':False})
        self.Investment.mark_as_paid([id2], '2016-01-04')

        result = self.Investment.create_initial_invoices([id1,id2])

        self.assertEqual(result, [[],[
            "Investment {name} is inactive".format(**investment1),
            "Investment {name} was already paid".format(**investment2),
            ]])


    def test__create_initial_invoices__zeroInvestments(self):

        result  = self.Investment.create_initial_invoices([])

        self.assertEqual(result, [[],[]])


    def test__create_amortization_invoice(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        self.Investment.mark_as_paid([id], '2017-01-03')
        invoice_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24)
        self.assertTrue(invoice_id)

        investment = self.Investment.browse(id)

        self.assertInvoiceInfoEqual(invoice_id, """\
            account_id: 410000{p.nsoci:0>6s} {p.surname}, {p.name}
            amount_total: 80.0
            amount_untaxed: 80.0
            check_total: 80.0
            date_invoice: '{invoice_date}'
            id: {id}
            invoice_line:
            - origin: false
              uos_id: PCE
              account_id: 163500{p.nsoci:0>6s} {p.surname}, {p.name}
              name: 'Amortització fins a 30/01/2018 de {investment_name} '
              invoice_id:
              - {id}
              - 'SI:  {investment_name}-AMOR{year}'
              price_unit: 80.0
              price_subtotal: 80.0
              invoice_line_tax_id: []
              note:
                pendingCapital: 1920.0
                amortizationDate: '2018-01-30'
                amortizationNumber: 1
                amortizationTotalNumber: 24
                investmentId: {investment_id}
                investmentName: {investment_name}
                investmentPurchaseDate: '2017-01-03'
                investmentLastEffectiveDate: '2042-01-03'
                investmentInitialAmount: 2000
              discount: 0.0
              account_analytic_id: false
              quantity: 1.0
              product_id: '[GENKWH_AMOR] Amortització Generation kWh'
            journal_id: Factures GenerationkWh
            name: {investment_name}-AMOR{year}
            origin: {investment_name}
            partner_bank: {iban}
            partner_id:
            - {p.partnerid}
            - {p.surname}, {p.name}
            payment_type:
            - 2
            - Transferencia
            sii_to_send: false
            type: in_invoice
            """.format(
                invoice_date = datetime.today().strftime("%Y-%m-%d"),
                id = invoice_id,
                iban = 'ES77 1234 1234 1612 3456 7890',
                year = 2018,
                investment_name = investment.name,
                p = self.personalData,
                investment_id = id
            ))

    def test__create_amortization_invoice__twice(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        inv = self.Investment.read(id, ['name'])

        self.Investment.mark_as_paid([id], '2017-01-03')
        invoice_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24)

        invoice_id2, errors2 = self.Investment.create_amortization_invoice(
                id, '2018-01-30', 80, 1, 24)

        self.assertIn(
            "Inversió {id}: L'amortització {name}-AMOR2018 ja existeix".format(**inv),
            unicode(errors2).encode('utf-8'),
            )

    def test__create_amortization_invoice__errorWhenNoBank(self):
        #TODO: especificar l'excepció
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )       
        self.Partner.write(self.personalData.partnerid,dict(bank_inversions = False))
        invocie_id, errors = self.Investment.create_amortization_invoice(id, '2018-01-30' , 80, 1, 24)
        self.assertIn(
            "El partner {surname}, {name} no té informat un compte corrent\n".format(**dbconfig.personaldata),
            unicode(errors).encode('utf-8'))

    def test__create_amortization_invoice__withUnnamedInvestment(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2016-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        self.Investment.write(id, dict(
            name=None)
            )

        self.Investment.mark_as_paid([id], '2016-01-03')

        invoice_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-03', 80, 1, 24)
        invoice = self.Invoice.browse(invoice_id)
        self.assertEqual(invoice.name,
            "GENKWHID{}-AMOR2018".format(id))

    def test__amortization_invoice_report(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000, # amount_in_euros
            '10.10.23.1', # ip
            'ES7712341234161234567890', # iban
            )

        self.Investment.mark_as_paid([id], '2017-01-03')
        invoice_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24)

        inv = ns(self.Investment.read(id, [
            'name',
        ]))

        result = self.Invoice.investmentAmortization_notificationData_asDict([invoice_id])
        self.assertNsEqual(ns(result), """\
            inversionName: {inv.name}
            ownerName: {surname}, {name}
            ownerNif: {nif}
            receiptDate: '{today}'
            inversionInitialAmount: 2.000,00
            inversionPendingCapital: 1.920,00
            inversionPurchaseDate: '03/01/2017'
            inversionExpirationDate: '03/01/2042'
            amortizationAmount: 80,00
            amortizationName: {inv.name}-AMOR2018
            amortizationTotalPayments: 24
            inversionBankAccount: ES77 1234 1234 1612 3456 7890
            amortizationDate: '30/01/2018'
            amortizationNumPayment: 1
            """.format(
                today = datetime.today().strftime("%d/%m/%Y"),
                nif = self.personalData.nif,
                name = self.personalData.name,
                surname = self.personalData.surname,
                inv = inv,
        ))

    def test__create_from_form__ibanIsSet(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        partner = self.Partner.browse(self.personalData.partnerid)
        self.assertTrue(partner.bank_inversions)

    def test__amortize__writes_log(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )
        self.Investment.mark_as_paid([investment_id], '2000-01-05')
        self.Investment.amortize('2002-01-06', [investment_id])

        investment = self.Investment.read(investment_id, ['log'])
        self.assertLogEquals(investment['log'],
            u'AMORTIZATION: Generada amortització de 80.00 € pel 2002-01-05\n'
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.1, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def test__open_invoices__allOk(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )

        self.Investment.mark_as_paid([id], '2017-01-03')
        invoice_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24)
        self.assertTrue(invoice_id)

        self.Investment.open_invoices([invoice_id])

        date_due_dt = datetime.today() + timedelta(7)
        date_due = date_due_dt.strftime('%Y-%m-%d')
        invoices_changes = self.Invoice.read(invoice_id,
            ['state',
             'date_due',
             ])

        self.assertEqual(invoices_changes, dict(
            id = invoice_id,
            state = 'open',
            date_due = date_due,
            ))

    def test__open_invoices__multipleInvoices(self):

        ids = []
        ids.append(self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            1000,
            '10.10.23.1',
            'ES7712341234161234567890',
        ))
        ids.append(self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.2',
            'ES7712341234161234567890',
        ))

        invoice_ids,errs = self.Investment.create_initial_invoices(ids)

        self.Investment.open_invoices(invoice_ids)

        date_due_dt = datetime.today() + timedelta(7)
        date_due = date_due_dt.strftime('%Y-%m-%d')
        invoices_changes = self.Invoice.read(invoice_ids,
            ['state',
             'date_due',
             ],
            order='id')

        self.assertEqual(invoices_changes, [dict(
            id = invoice_ids[0],
            state = 'open',
            date_due = date_due,
            ), dict(
            id=invoice_ids[1],
            state='open',
            date_due=date_due,
        )])


    def test__invoices_to_payment_order(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        invoice_ids, errs =  self.Investment.create_initial_invoices([id])
        self.Investment.open_invoices(invoice_ids)
        self.Investment.invoices_to_payment_order(invoice_ids)
        invoice = self.Invoice.browse(invoice_ids[0])

        order_id = self.Investment.get_or_create_open_payment_order("GENERATION kWh")
        lines = self.PaymentLine.search([
            ('order_id','=', order_id),
            ('communication','like', invoice.origin),
            ])

        self.assertTrue(lines)

    def test__invoices_to_payment_order_multiple(self):

        ids=[]
        ids.append(self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.1',
            'ES7712341234161234567890',
            ))
        ids.append(self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02',  # order_date
            2000,
            '10.10.23.2',
            'ES7712341234161234567890',
        ))

        invoice_ids, err =  self.Investment.create_initial_invoices(ids)
        self.Investment.open_invoices(invoice_ids)
        self.Investment.invoices_to_payment_order(invoice_ids)

        invoices = self.Invoice.browse(invoice_ids)
        order_id = self.Investment.get_or_create_open_payment_order("GENERATION kWh")
        lines = [self.PaymentLine.search([
            ('order_id','=', order_id),
            ('communication','like', invoices[0].origin),
            ])]
        lines.append(self.PaymentLine.search([
            ('order_id','=', order_id),
            ('communication','like', invoices[1].origin),
            ]))
        self.assertEqual(len(invoice_ids), len(lines))

    def test__get_or_create_payment_mandate__calledTwiceReturnsSame(self):
        iban = 'ES8901825726580208779553'
        purpose = 'GENERATION kWh'
        creditor_code = 'CREDITORCODE'
        mandate1_id = self.Investment.get_or_create_payment_mandate(
            self.personalData.partnerid, iban, purpose, creditor_code)
        mandate2_id = self.Investment.get_or_create_payment_mandate(
            self.personalData.partnerid, iban, purpose, creditor_code)
        self.assertEqual(mandate1_id, mandate2_id)

    def test__get_or_create_payment_mandate__notOpenCreatsANewOne(self):
            iban = 'ES8901825726580208779553'
            purpose = 'GENERATION kWh'
            creditor_code = 'CREDITORCODE'
            mandate1_id = self.Investment.get_or_create_payment_mandate(
                self.personalData.partnerid, iban, purpose, creditor_code)
            self.PaymentMandate.write(mandate1_id, dict(date_end='2015-01-01'))
            mandate2_id = self.Investment.get_or_create_payment_mandate(
                self.personalData.partnerid, iban, purpose, creditor_code)
            self.assertNotEqual(mandate1_id, mandate2_id)

    def test__get_or_create_payment_mandate__newlyCreatedHasProperFields(self):
            iban = 'ES8901825726580208779553'
            purpose = 'GENERATION kWh'
            creditor_code = 'CREDITORCODE'

            old_mandate_id = self.Investment.get_or_create_payment_mandate(
                self.personalData.partnerid, iban, purpose, creditor_code)
            # Ensure the next is new
            self.PaymentMandate.write(old_mandate_id, dict(date_end='2015-01-01'))

            mandate_id = self.Investment.get_or_create_payment_mandate(
                self.personalData.partnerid, iban, purpose, creditor_code)

            mandate = ns(self.PaymentMandate.read(mandate_id, []))
            self.assertTrue(mandate.name and
                all(x in 'abdcdef1234567890' for x in mandate.name),
                "mandate.name should be a lowercase hex code")
            mandate.creditor_id = mandate.creditor_id[1]
            partner = self.ResPartner.browse(self.personalData.partnerid)
            nom_complet = self.personalData.surname + ", " + self.personalData.name
            self.assertNsEqual(mandate, ns.loads("""\
                creditor_address: CL. PIC DE PEGUERA, 11 A 2 8  17003 GIRONA (ESPAÑA)
                creditor_code: CREDITORCODE
                creditor_id: SOM ENERGIA SCCL
                date: '{today}'
                date_end: false
                debtor_address: {address}
                debtor_country: '67'
                debtor_iban: {iban}
                debtor_iban_print: {format_iban}
                debtor_name: {debtor_name}
                debtor_state: {state}
                debtor_vat: {vat}
                id: {id}
                name: {name}
                notes: GENERATION kWh
                payment_type: recurring
                reference: res.partner,{partner_id}
                """.format(
                    id=mandate_id,
                    name=mandate.name, # always change
                    partner_id=self.personalData.partnerid,
                    vat="ES"+self.personalData.nif,
                    debtor_name=nom_complet,
                    address = partner.address[0].street.encode('utf-8'),
                    state = partner.address[0].state_id.name.encode('utf-8'),
                    iban=iban,
                    format_iban=' '.join(
                        iban[n:n+4] for n in xrange(0,len(iban),4)),
                    today=datetime.today().strftime("%Y-%m-%d"),
                )))

    def test__send_mail__emailCreacioSent(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.assertNsEqual(self.MailMockup.log(), ns.loads("""\
            logs:
                - PlantillaEmailEnviada: generationkwh_mail_creacio
            """))

    def test__send_mail__emailPagamentSent(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.send_mail(id,'account.invoice', 'generationkwh_mail_pagament')
        self.assertNsEqual(self.MailMockup.log(), ns.loads("""\
            logs:
                - PlantillaEmailEnviada: generationkwh_mail_creacio
                - PlantillaEmailEnviada: generationkwh_mail_pagament
           """))

    def test__send_mail__emailImpagamentSent(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.send_mail(id,'account.invoice', 'generationkwh_mail_impagament')
        self.assertNsEqual(self.MailMockup.log(), ns.loads("""\
            logs:
                - PlantillaEmailEnviada: generationkwh_mail_creacio
                - PlantillaEmailEnviada: generationkwh_mail_impagament
           """))

    def test__send_mail__emailAmortizationSent(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        date_due_dt = datetime.today() + timedelta(730)
        date_due = date_due_dt.strftime('%Y-%m-%d')
        self.Investment.mark_as_paid([id], datetime.today().strftime('%Y-%m-%d'))
        self.Investment.amortize(date_due, [id])
        self.assertNsEqual(self.MailMockup.log(), ns.loads("""\
            logs:
                - PlantillaEmailEnviada: generationkwh_mail_creacio
                - PlantillaEmailEnviada: generationkwh_mail_pagament
                - PlantillaEmailEnviada: generationkwh_mail_amortitzacio
           """))

    def test__amortized_amount__zeroByDefault(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2015-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_paid([id], '2015-01-02')
        investment = self.Investment.read(id, ['amortized_amount'])
        self.assertEqual(0.0, investment['amortized_amount'])

    def test__amortize__justBeforeAmortization(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_paid([id], '2015-01-02')
        self.Investment.amortize('2017-01-01',[id])
        investment = self.Investment.read(id,['amortized_amount'])
        self.assertEqual(0, investment['amortized_amount'])

    def test__amortize__justAtAmortizationDate(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_paid([id], '2015-01-02')

        self.Investment.amortize('2017-01-02',[id])

        investment = self.Investment.read(id,['amortized_amount'])
        self.assertEqual(40, investment['amortized_amount'])

    def test__amortize__secondAmortization(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_paid([id], '2015-11-20')
        self.Investment.amortize('2017-11-20',[id])
        self.Investment.amortize('2018-11-20',[id])

        investment = self.Investment.read(id,['amortized_amount'])
        self.assertEqual(80, investment['amortized_amount'])

    def test__amortize__afterFullAmortization(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_paid([id], '2015-11-20')

        invoice,errors = self.Investment.amortize('2040-11-20',[id])
        investment = self.Investment.read(id,['amortized_amount'])
        self.assertTrue(invoice)
        self.assertEqual(1000, investment['amortized_amount'])

        invoice,errors = self.Investment.amortize('2041-11-20',[id])
        self.assertFalse(invoice)
        investment = self.Investment.read(id,['amortized_amount'])
        self.assertEqual(1000, investment['amortized_amount'])

    # Amortizations
    def pendingAmortizations(self, id, currentDate):
        result = self.Investment.pending_amortizations(currentDate, [id])
        return [x[:-1] for x in sorted(result)] # filter id and log

    def test__pending_amortitzations__unpaid(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.assertEqual(self.pendingAmortizations(id, '2017-11-20'), [])

    def test__pending_amortitzations__manyAmortizationsSameInvestment(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_paid([id], '2000-01-02')
        self.assertEqual(
            self.pendingAmortizations(id, '2004-01-04'),[
            [id, mid, '2002-01-02',  0, 40, 1, 24],
            [id, mid, '2003-01-02', 40, 40, 2, 24],
            [id, mid, '2004-01-02', 80, 40, 3, 24],
            ])

    def test__pending_amortitzations__withDueInvestments(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_paid([id], '2000-01-02')
        self.assertEqual(
            self.pendingAmortizations(id, '2002-01-02'),[
            [id, mid, '2002-01-02',  0, 40, 1, 24],
            ])

    def test__pending_amortitzations__notDue(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_paid([id], '2000-01-02')
        self.assertEqual(
            self.pendingAmortizations(id, '2002-01-01'),[
            ])

    def test__pending_amortitzations__whenPartiallyAmortized(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_paid([id], '2000-01-02')
        self.Investment.amortize('2002-01-02',[id])
        self.assertEqual(
            self.pendingAmortizations(id, '2003-01-02'),[
            [id, mid, '2003-01-02', 40, 40, 2, 24],
            ])


unittest.TestCase.__str__ = unittest.TestCase.id

if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
