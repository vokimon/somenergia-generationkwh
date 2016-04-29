# -*- coding: utf-8 -*-

from osv import osv, fields
from .erpwrapper import ErpWrapper
import datetime
from yamlns import namespace as ns

# TODO: sort rights sources if many members assigned the same contract
# TODO: Filter out inactive contracts

class GenerationkWhAssignment(osv.osv):

    _name = 'generationkwh.assignment'

    _columns = dict(
        contract_id=fields.many2one(
            'giscedata.polissa',
            'Contract',
            required=True,
            help="Contract which gets rights to use generated kWh",
            ),
        member_id=fields.many2one(
            'res.partner',
            'Member',
            required=True,
            help="Member who bought Generation kWh shares and assigns them",
            ),
        priority=fields.integer(
            'Priority',
            required=True,
            help="Assignment precedence. "
                "This assignment won't use rights generated on dates that "
                "have not been invoiced yet by assignments "
                "of the same member having higher priority "
                "(lower the value, higher the priority).",
            ),
        end_date=fields.date(
            'Expiration date',
            help="Date at which the rule is no longer active",
            ),
        )

    def add(self, cr, uid, assignments, context=None):
        for contract_id, member_id, priority in assignments:
            same_polissa_member = self.search(cr, uid, [
                '|', ('end_date', '<', str(datetime.date.today())),
                    ('end_date','=',False),
                ('contract_id', '=', contract_id),
                ('member_id', '=', member_id),
            ], context = context)
            if same_polissa_member:
                self.write(cr,uid,
                    same_polissa_member,
                    dict(
                        end_date=str(datetime.date.today()),
                    ),
                    context=context,
                )
            self.create(cr, uid, {
                'contract_id': contract_id,
                'member_id': member_id,
                'priority': priority,
            }, context=context)

    def sortedDefaultContractsForMember(self, cr, uid, member_ids, context=None):
        """ Gets default contract to assign for a given member ids
            Criteria are:
            - Contracts the member being the payer first,
              then the ones the member is owner but not payer.
            - Within both groups the ones with more anual use first.
        """
        from tools import config
        import os
        sqlfile = os.path.join(
            config['addons_path'], 'generationkwh_api',
                'sql', 'asignacion_total_b2b.sql')
        with open(sqlfile) as f:
            sql = f.read()
        cr.execute(sql, dict(socis=tuple(member_ids)))
        return [
            (contract,member)
            for contract,member,_,_ in cr.fetchall()
            if contract
            ]

    def createOnePrioritaryAndManySecondaries(self, cr, uid, assignments, context=None):
        """ Creates assignments from a list of pairs of contract_id, member_id.
            The first pair of a member is the priority 0 and the 
            remaining contracts of the same member are inserted as priority zero.
            @pre contracts of the same member are together
            """
        formerMember=None
        members = list(set(member for contract,member in assignments))
        ids = self.search(cr, uid, [
            ('member_id','in',members),
            ],context=context)
        self.unlink(cr, uid, ids, context=context)
        for contract, member in assignments:
            self.create(cr, uid, dict(
                contract_id = contract,
                member_id = member,
                priority = 0 if member!=formerMember else 1,
                ), context=context)
            formerMember=member
    
    def dropAll(self, cr, uid, context=None):
        """Remove all records"""
        ids = self.search(cr, uid, [
            ],context=context)
        for a in self.browse(cr, uid, ids, context=context):
            a.unlink()

    def expire(self, cr, ids, context=None):
        "TODO: GenerationkWhAssignment.expire"

    def availableAssigmentsForContract(self, cursor, uid, contract_id, context=None):
        assignmentProvider = AssignmentProvider(self, cursor, uid, context)
        #Conversion of ns to dict in order to marshall to XML-RPC
        return [dict(assign) for assign in assignmentProvider.seek(contract_id)]


GenerationkWhAssignment()


class AssignmentProvider(ErpWrapper):

    def seek(self, contract_id):
        self.cursor.execute("""
            SELECT
                ass.member_id AS member_id,
                COALESCE(
                    MIN(contracte.last_usable_date),
                    DATE(NOW()) /* no peers, so now */
                ) AS last_usable_date,
                FALSE
            FROM generationkwh_assignment AS ass
            LEFT JOIN generationkwh_assignment AS peer
                ON ass.member_id = peer.member_id
                AND peer.contract_id != ass.contract_id
                AND peer.priority < ass.priority
            LEFT JOIN (
                SELECT
                    id,
                    COALESCE(
                        data_ultima_lectura,
                        data_alta
                    ) AS last_usable_date
                FROM giscedata_polissa
                ) AS contracte
                ON contracte.id = peer.contract_id
            WHERE ass.contract_id = %(contract_id)s
            GROUP BY
                ass.id,
                ass.member_id,
                FALSE
            ORDER BY
                ass.id,
                FALSE
        """, dict(contract_id=contract_id))
        return [
            ns(
                member_id=member_id,
                last_usable_date=last_usable_date,
            )
            for member_id, last_usable_date, _
            in self.cursor.fetchall()
            ]



