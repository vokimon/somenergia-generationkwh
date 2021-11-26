# -*- coding: utf-8 -*-
from datetime import date, datetime
from osv import osv, fields
from tools.translate import _
import pickle

class WizardInvestmentTransfer(osv.osv):

    _name = 'wizard.generationkwh.investment.transfer'

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'invoices': fields.text(
            'test',
        ),
        'transmission_date': fields.date('Transmission Date', required=True),
        'partner_id_alt': fields.many2one(
            'res.partner',
            'Titular',
            domain=[('category_id.name','=','Soci')],
            required=True,
        ),
        'iban': fields.many2one(
            'res.partner.bank',
            'IBAN',
            required=True,
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: 'Aquesta acció transferirà la inversió.\n'
                           'Condicions:\n'
                           '  - Les inversions han d"estar pagades \n',
        'transmission_date': lambda *a: date.today().strftime('%Y-%m-%d')
    }

    _constraints = [
        (_check_transmission_date, 'Error! Aquest wizard no permet dates anteriors a avui.', ['transmission_date'])
    ]

    def _check_transmission_date(self, cr, uid, ids):
        wiz = self.browse(cursor, uid, ids[0])
        transmission_date = datetime.strptime(wiz.transmission_date, "%Y-%m-%d").date()
        return transmission_date >= date.today()

    def do_transfer(self, cursor, uid, ids, context=None):

        if context is None:
            context = {}

        Investment = self.pool.get('generationkwh.investment')
        wiz = self.browse(cursor, uid, ids[0], context)
        investment_ids = context.get('active_ids', [])
        new_partner_id = int(wiz.partner_id_alt.id)
        iban = wiz.iban.iban
        transmission_date = wiz.transmission_date

        new_investment_id = Investment.create_from_transfer(cursor, uid, investment_ids[0], new_partner_id, transmission_date, iban, context=None)
        old = Investment.read(cursor, uid, investment_ids[0],['name'])
        new = Investment.read(cursor, uid, new_investment_id,['name'])

        info = "RESULTAT: \n"
        info += "================\n"
        info += "Investment vell: %s" % (old['name'] if old else "Error")
        info += "\nInvestment nou: %s" % (new['name'] if new else "Error")
        wiz.write(dict(
            info= info,
            state = 'Done',
            ))

        return True


WizardInvestmentTransfer()
# vim: et ts=4 sw=4 
