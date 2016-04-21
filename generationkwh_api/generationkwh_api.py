# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields
import netsvc
from mongodb_backend.mongodb2 import mdbpool

from generationkwh.dealer import Dealer
from generationkwh.sharescurve import MemberSharesCurve
from generationkwh.rightspershare import RightsPerShare
from generationkwh.memberrightscurve import MemberRightsCurve
from generationkwh.memberrightsusage import MemberRightsUsage
from generationkwh.fareperiodcurve import FarePeriodCurve
from generationkwh.usagetracker import UsageTracker
from generationkwh.isodates import localisodate
from .assignment import AssignmentProvider
from .remainder import RemainderProvider
from .investment import InvestmentProvider
from .holidays import HolidaysProvider
from .productionloader import ProductionAggregatorProvider # unused, force load

# Models

class GenerationkWhTestHelper(osv.osv):
    """
        Helper model that enables accessing data providers
        from tests written with erppeek.
    """

    _name = 'generationkwh.testhelper'
    _auto = False

    def holidays(self, cursor, uid,
            start, stop,
            context=None):
        holidaysProvider = HolidaysProvider(self, cursor, uid, context)
        return holidaysProvider.get(start, stop)

    def setup_rights_per_share(self, cursor, uid,
            nshares, startDate, data,
            context=None):
        rightsPerShare = RightsPerShare(mdbpool.get_db())
        rightsPerShare.updateRightsPerShare(nshares, localisodate(startDate), data)

    def clear_mongo_collections(self, cursor, uid, collections, context=None):
        for collection in collections:
            mdbpool.get_db().drop_collection(collection)



    def trace_rigths_compilation(self, cursor, uid,
            member, start, stop, fare, period,
            context=None):
        """
            Helper function to show data related to computation of available
            rights.
        """
        print "Dropping results for", member, start, stop, fare, period
    
        investment = InvestmentProvider(self, cursor, uid, context)
        memberActiveShares = MemberSharesCurve(investment)
        rightsPerShare = RightsPerShare(mdbpool.get_db())

        generatedRights = MemberRightsCurve(
            activeShares=memberActiveShares,
            rightsPerShare=rightsPerShare,
            eager=True,
            )
        rightsUsage = MemberRightsUsage(mdbpool.get_db())
        holidays = HolidaysProvider(self, cursor, uid, context)
        farePeriod = FarePeriodCurve(holidays)

        print 'investment', investment.shareContracts(
            start=localisodate(start),
            end=localisodate(stop),
            member=2)
        print 'active', memberActiveShares.hourly(
            localisodate(start),
            localisodate(stop),
            member)
        for nshares in set(memberActiveShares.hourly(
            localisodate(start),
            localisodate(stop),
            member)):
            print 'rightsPerShare', nshares, rightsPerShare.rightsPerShare(nshares,
                localisodate(start),
                localisodate(stop),
                )
        print 'rights', generatedRights.rights_kwh(member,
            localisodate(start),
            localisodate(stop),
            )

        print 'periodmask', farePeriod.periodMask(
            fare, period,
            localisodate(start),
            localisodate(stop),
            )

    def usagetracker_available_kwh(self, cursor, uid,
            member, start, stop, fare, period,
            context=None):

        GenerationkWhDealer = self.pool.get('generationkwh.dealer')
        usageTracker = GenerationkWhDealer._createTracker(cursor, uid, context)
        result = usageTracker.available_kwh(
            member,
            localisodate(start),
            localisodate(stop),
            fare,
            period
            )
        return result

GenerationkWhTestHelper()




class GenerationkWhDealer(osv.osv):

    _name = 'generationkwh.dealer'
    _auto = False

    def is_active(self, cursor, uid,
                  contract_id, start_date, end_date,
                  context=None):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        dealer = self._createDealer(cursor, uid, context)

        return dealer.is_active(
            contract_id, start_date, end_date)

    def get_available_kwh(self, cursor, uid,
                          contract_id, start_date, end_date, fare, period,
                          context=None):
        """ Returns generationkwh [kWh] available for contract_id during the
            date interval, fare and period"""
        dealer = self._createDealer(cursor, uid, context)

        return dealer.get_available_kwh(
            contract_id, start_date, end_date, fare, period)

    def use_kwh(self, cursor, uid,
                contract_id, start_date, end_date, fare, period, kwh,
                context=None):
        """Marks the indicated kwh as used, if available, for the contract,
           date interval, fare and period and returns the ones efectively used.
        """
        logger = netsvc.Logger()
        dealer = self._createDealer(cursor, uid, context)

        res = dealer.use_kwh(
            contract_id, start_date, end_date, fare, period, kwh)

        txt_vals = dict(
            contract=contract_id,
            period=period,
            start=start_date,
            end=end_date,
        )
        txt =''
        for line in res:
            txt_vals.update(dict(
                kwh=line['kwh'],
                member=line['member_id'],
            ))
            txt = (u'{kwh} Generation kwh of member {member} to {contract} '
                   u'for period {period} between {start} and {end}').format(
                **txt_vals
            )
            logger.notifyChannel('gkwh_dealer USE', netsvc.LOG_INFO, txt)

        return res

    def refund_kwh(self, cursor, uid,
                   contract_id, start_date, end_date, fare, period, kwh,
                   partner_id, context=None):
        """Refunds the indicated kwh, marking them as available again, for the
           contract, date interval, fare and period and returns the ones
           efectively used.
        """
        logger = netsvc.Logger()
        dealer = self._createDealer(cursor, uid, context)

        txt_vals = dict(
            contract=contract_id,
            period=period,
            start=start_date,
            end=end_date,
            member=partner_id,
            kwh=kwh
        )
        txt = (u'{kwh} Generation kwh of member {member} to {contract} '
               u'for period {period} between {start} and {end}').format(
            **txt_vals
        )
        logger.notifyChannel('gkwh_dealer REFUND', netsvc.LOG_INFO, txt)
        res = dealer.refund_kwh(
            contract_id, start_date, end_date, fare, period, kwh, partner_id)
        return res

    def _createTracker(self, cursor, uid, context):

        investments = InvestmentProvider(self, cursor, uid, context)
        memberActiveShares = MemberSharesCurve(investments)
        rightsPerShare = RightsPerShare(mdbpool.get_db())

        generatedRights = MemberRightsCurve(
            activeShares=memberActiveShares,
            rightsPerShare=rightsPerShare,
            eager=True,
            )

        rightsUsage = MemberRightsUsage(mdbpool.get_db())

        holidays = HolidaysProvider(self, cursor, uid, context)
        farePeriod = FarePeriodCurve(holidays)

        return UsageTracker(generatedRights, rightsUsage, farePeriod)

    def _createDealer(self, cursor, uid, context):

        usageTracker = self._createTracker(cursor, uid, context)
        # TODO: Feed the dealer with data sources
        return Dealer(usageTracker)

GenerationkWhDealer()


class GenerationkWhInvoiceLineOwner(osv.osv):
    """ Class with the relation between generation invoice line and rights owner
    """

    _name = 'generationkwh.invoice.line.owner'

    def name_get(self, cursor, uid, ids, context=None):
        """GkWH name"""
        res = []
        glo_vals = self.read(cursor, uid, ids, ['factura_line_id'])
        for glo in glo_vals:
            res.append((glo['id'], glo['factura_line_id'][1]))

        return res

    def _ff_invoice_number(self, cursor, uid, ids, field_name, arg,
                           context=None ):
        """Invoice Number"""
        if not ids:
            return []
        res = dict([(i, False) for i in ids])
        f_obj = self.pool.get('giscedata.facturacio.factura')

        glo_vals = self.read(cursor, uid, ids, ['factura_id'])
        inv_ids = [g['factura_id'][0] for g in glo_vals]
        inv_vals = f_obj.read(cursor, uid, inv_ids, ['number'])
        inv_dict = dict([(i['id'], i['number']) for i in inv_vals])
        for glo_val in glo_vals:
            glo_id = glo_val['id']
            glo_number = inv_dict[glo_val['factura_id'][0]]
            res.update({glo_id: glo_number})

        return res

    _columns = {
        'factura_id': fields.many2one(
            'giscedata.facturacio.factura', 'Factura', required=True,
            readonly=True
        ),
        'factura_number': fields.function(
            _ff_invoice_number, string='Num. Factura', method=True, type='char',
            size='64',
        ),
        'factura_line_id': fields.many2one(
            'giscedata.facturacio.factura.linia', 'Línia de factura',
            required=True, readonly=True
        ),
        'owner_id': fields.many2one(
            'res.partner', 'Soci Generation', required=True, readonly=True
        ),
    }

GenerationkWhInvoiceLineOwner()

# vim: ts=4 sw=4 et
