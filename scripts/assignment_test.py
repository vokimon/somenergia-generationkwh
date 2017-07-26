# -*- coding: utf-8 -*-

import unittest
import datetime
from yamlns import namespace as ns
from generationkwh.isodates import isodate
dbconfig = None
try:
    import dbconfig
    import erppeek_wst
except ImportError:
    pass

@unittest.skipIf(not dbconfig, "depends on ERP")
class Assignment_Test(unittest.TestCase):

    def setUp(self):
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Assignment = self.erp.GenerationkwhAssignment
        self.Assignment.dropAll()

        (
            self.member,
            self.member2,
            self.member3,
        ) = self.erp.SomenergiaSoci.search([],limit=3)
        (
            self.contract,
            self.contract2,
            self.contract3,
        ) = self.erp.GiscedataPolissa.search([], limit=3)
        self.today = str(datetime.date.today())

    def setupProvider(self,assignments=[]):
        for contract, member, priority in assignments:
            self.Assignment.create(dict(
                contract_id = contract,
                member_id = member,
                priority = priority,
                ))

    def assertAssignmentsEqual(self, expectation):
        result = self.Assignment.browse([])
        self.assertEqual( [
                (
                    r.contract_id.id,
                    r.member_id.id,
                    r.priority,
                    r.end_date,
                )
                for r in result
            ],expectation)

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()

    def test_no_assignments(self):
        self.setupProvider()
        self.assertAssignmentsEqual([])

    def test_default_values(self):
        self.Assignment.create(dict(
            member_id = self.member,
            contract_id = self.contract,
            priority = 0,
            ))
        self.assertAssignmentsEqual([
            (self.contract, self.member, 0, False),
            ])

    def test_create_priorityRequired(self):

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                member_id = self.member,
                contract_id = self.contract,
                ))
        self.assertRegexpMatches(
            #'null value in column "priority" violates not-null constraint',
            str(ctx.exception),
            'Integrity.*Error.*priority.*not.*null')

    def test_create_contractRequired(self):

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                member_id = self.member,
                priority = 0,
                ))
        self.assertRegexpMatches(
            #'null value in column "priority" violates not-null constraint',
            str(ctx.exception),
            'Integrity.*Error.*contract_id.*not.*null')

    def test_create_memberRequired(self):

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                contract_id = self.contract,
                priority = 0,
                ))
        self.assertRegexpMatches(
            #'null value in column "priority" violates not-null constraint',
            str(ctx.exception),
            'Integrity.*Error.*member_id.*not.*null')

    def test_one_assignment(self):
        self.setupProvider([
            (self.contract,self.member,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract,self.member,1,False),
            ])

    def test_no_duplication(self):
        self.setupProvider([
            (self.contract, self.member, 1),
            (self.contract, self.member, 2),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 1, self.today),
            (self.contract, self.member, 2, False),
            ])
    
    def test_change_priority(self):
        self.setupProvider([
            (self.contract,self.member,1),
            (self.contract,self.member,2),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 1, self.today),
            (self.contract,self.member,2, False),
            ])

    def test_three_member_three_polissas(self):
        members=self.member, self.member2, self.member3
        contracts=self.contract,self.contract2,self.contract3
        self.setupProvider([
            (self.contract, self.member, 1),
            (self.contract2,self.member2,1),
            (self.contract3,self.member3,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 1,False),
            (self.contract2,self.member2,1,False),
            (self.contract3,self.member3,1,False),
            ])

    def test_three_member_one_polissa(self):
        members=self.member, self.member2, self.member3
        self.setupProvider([
            (self.contract,self.member, 1),
            (self.contract,self.member2,1),
            (self.contract,self.member3,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract,self.member, 1,False),
            (self.contract,self.member2,1,False),
            (self.contract,self.member3,1,False),
            ])

    def test_one_member_three_polissas(self):
        contracts=self.contract,self.contract2,self.contract3
        self.setupProvider([
            (self.contract,  self.member,1),
            (self.contract2, self.member,1),
            (self.contract3, self.member,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract , self.member,1,False),
            (self.contract2, self.member,1,False),
            (self.contract3, self.member,1,False),
            ])

    def test_expire_one_member_one_polissa(self):
        self.setupProvider([
            (self.contract, self.member,1),
            ])
        self.Assignment.expire(self.contract, self.member)
        self.assertAssignmentsEqual([
            (self.contract, self.member,1,self.today),
            ])

    def test_expire_one_member_two_polissa(self):
        self.setupProvider([
            (self.contract, self.member,1),
            (self.contract2, self.member,1),
            ])
        self.Assignment.expire(self.contract, self.member)
        self.assertAssignmentsEqual([
            (self.contract, self.member,1,self.today),
            (self.contract2, self.member,1,False),
            ])

    def test_expire_previously_expired_polissa(self):
        self.setupProvider([
            (self.contract, self.member,1),
            (self.contract, self.member,1),
            ])
        self.Assignment.expire(self.contract, self.member)
        self.assertAssignmentsEqual([
            (self.contract, self.member,1,self.today),
            (self.contract, self.member,1,self.today),
            ])

@unittest.skipIf(not dbconfig, "depends on ERP")
class AssignmentProvider_Test(unittest.TestCase):

    def orderContractsByConany(self,contract_ids):
        unorderedContracts = self.erp.GiscedataPolissa.browse(contract_ids)
        unorderedCups_ids = [pol.cups.id for pol in unorderedContracts if pol.cups.active]
        orderedCups_ids = self.erp.GiscedataCupsPs.search([('id','in', unorderedCups_ids)],order='conany_kwh DESC')
        orderedCups = self.erp.GiscedataCupsPs.browse(orderedCups_ids)
        return tuple([cups.polissa_polissa.id for cups in orderedCups])

    def setUp(self):
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Assignment = self.erp.GenerationkwhAssignment
        self.AssignmentTestHelper = self.erp.GenerationkwhAssignmentTesthelper
        self.Assignment.dropAll()

        self.member, self.member2 = [
            m.id for m in self.erp.SomenergiaSoci.browse([], limit=2)]

        contract, contract2 = [ c for c in self.erp.GiscedataPolissa.browse(
                [('data_ultima_lectura','!=',False)],
                order='data_ultima_lectura',
                limit=2,
                )
            ]
        self.contract = contract.id
        self.contract2 = contract2.id
        self.contractLastInvoicedDate = contract.data_ultima_lectura
        self.contract2LastInvoicedDate = contract2.data_ultima_lectura
        self.today = str(datetime.date.today())

        newContract, = self.erp.GiscedataPolissa.browse(
                [('data_ultima_lectura','=',False),
                 ('state','=','activa')], limit=1)
        self.newContract = newContract.id
        self.newContractActivationDate = newContract.data_alta

        # pickup cases (commented out the original partner.id)
        self.member_noContracts = 537 # 629
        self.member_oneAsPayer = 4 # 5 
        self.member_asOwnerButNotPayer = 8887 # 13846
        self.contract_asOwnerButNotPayer = 15212
        self.member_aPayerAndAnOwnerContract = 107 # 120
        self.member_manyAsPayer = 54 # 61
        self.member_manyAsPayerAndManyAsOwner = 351 # 400

        # Sorted contracts for member_manyAsPayerAndManyAsOwner
        # TODO: Sort them by annual use programatically, if not is fragile,
        # since annual use depends on the database snapshot
        manyAsPayerAndManyAsOwner_partner_id = self.erp.SomenergiaSoci.get(self.member_manyAsPayerAndManyAsOwner).partner_id.id
        manyAsPayerAndManyAsOwner_payerContract_unorderedContract_ids = self.erp.GiscedataPolissa.search(
            [
             ('pagador','=',manyAsPayerAndManyAsOwner_partner_id),
             ('state','=','activa'),
             ('active','=',True),
            ])
        manyAsPayerAndManyAsOwner_ownerContract_unorderedContract_ids = self.erp.GiscedataPolissa.search(
            ['&',
                 ('titular','=', manyAsPayerAndManyAsOwner_partner_id),
                 ('pagador', '!=', manyAsPayerAndManyAsOwner_partner_id),
             ('state','=','activa'),
             ('active','=',True),
            ])

        self.payerContracts = self.orderContractsByConany(manyAsPayerAndManyAsOwner_payerContract_unorderedContract_ids)
        self.ownerContracts = self.orderContractsByConany(manyAsPayerAndManyAsOwner_ownerContract_unorderedContract_ids)

    def setupAssignments(self, assignments):
        for contract, member, priority in assignments:
            self.Assignment.create(dict(
                contract_id=contract,
                member_id=member,
                priority=priority,
                ))

    def assertAssignmentsSeekEqual(self, contract_id, expectation):
        result = self.Assignment.contractSources(contract_id)
        self.assertEqual([
            (member_id, last_usable_date)
            for member_id, last_usable_date in expectation
            ], [
            (member_id, last_usable_date)
            for member_id, last_usable_date in result
            ])

        result = self.AssignmentTestHelper.contractSources(contract_id)
        self.assertEqual([
            dict(
                member_id=member_id,
                last_usable_date=last_usable_date,
            )
            for member_id, last_usable_date in expectation
            ], result)

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()

    def test_contractSources_noAssignment(self):
        self.setupAssignments([])
        self.assertAssignmentsSeekEqual(self.contract, [])

    def test_contractSources_oneAssignment_noCompetitors(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.today),
            ])

    def test_contractSources_expiredAssignment_notRetrieved(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        self.Assignment.expire(self.contract, self.member)
        self.assertAssignmentsSeekEqual(self.contract, [
            ])

    def test_contractSources_assigmentsForOtherContracts_ignored(self):
        self.setupAssignments([
            (self.contract2, self.member, 1),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
        ])

    def test_contractSources_manyAssignments_noCompetitors(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract, self.member2, 0),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.today),
            (self.member2, self.today),
            ])

    def test_contractSources_competitorWithoutInvoices_takesActivationDate(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.newContract, self.member, 0),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.newContractActivationDate),
            ])

    def test_contractSources_competitorWithInvoices_takesLastInvoicedDate(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member, 0),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.contract2LastInvoicedDate),
            ])

    def test_contractSources_competitor_expired_ignored(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member, 0),
            ])
        self.Assignment.expire(self.contract2, self.member)
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.today),
            ])

    def test_contractSources_competitorWithEqualOrLowerPriority_ignored(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member, 1), # equal
            (self.newContract, self.member, 2), # lower (higher number)
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.today),
            ])

    def test_contractSources_manyCompetitors_earlierLastInvoicedPrevails(self):
        self.setupAssignments([
            (self.newContract,self.member,1),
            (self.contract,self.member,0),
            (self.contract2,self.member,0),
            ])
        self.assertAssignmentsSeekEqual(self.newContract, [
            (self.member, min(
                self.contractLastInvoicedDate,
                self.contract2LastInvoicedDate,
                )),
            ])

    def assertAssignmentsEqual(self,expectation):
        self.assertEqual([
            (record.contract_id.id, record.member_id.id, record.priority) 
            for record in self.Assignment.browse([], order='id')
            ], expectation)

    def test_createOnePrioritaryAndManySecondaries_oneAssignment(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract, self.member),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 0),
            ])

    def test_createOnePrioritaryAndManySecondaries_noAssignment(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            ])
        self.assertAssignmentsEqual([
            ])

    def test_createOnePrioritaryAndManySecondaries_clearPrevious(self):
        self.setupAssignments([
            (self.contract2, self.member, 1),
            ])
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract, self.member),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 0),
            ])

    def test_createOnePrioritaryAndManySecondaries_preserveOtherMembers(self):
        self.setupAssignments([
            (self.contract2, self.member2, 1),
            ])
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract,self.member),
            ])
        self.assertAssignmentsEqual([
            (self.contract2, self.member2, 1),
            (self.contract, self.member, 0),
            ])

    def test_createOnePrioritaryAndManySecondaries_manyMembers_singleContract(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract,self.member),
            (self.contract2,self.member2),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 0),
            (self.contract2, self.member2, 0),
            ])

    def test_createOnePrioritaryAndManySecondaries_sameMember_manyContracts(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract, self.member),
            (self.contract2, self.member),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 0),
            (self.contract2, self.member, 1),
            ])


    def assertContractForMember(self, member_id,expectation):
        if not isinstance(member_id,list):
            member_ids=[member_id]
        else:
            member_ids=member_id
        result=self.Assignment.sortedDefaultContractsForMember(
            member_ids
        )
        self.assertEqual([tuple(r) for r in result], expectation) 


    def test_sortedDefaultContractsForMember_noMembersSpecified(self):
        self.assertContractForMember([], [
            ])

    def test_sortedDefaultContractsForMember_withoutContracts(self):
        self.assertContractForMember(self.member_noContracts, [
            ])

    def test_sortedDefaultContractsForMember_oneAsPayer(self):
        self.assertContractForMember(self.member_oneAsPayer, [
            (106369, self.member_oneAsPayer),
            ])

    def test_sortedDefaultContractsForMember_oneAsOwnerButNotPayer(self):
        self.assertContractForMember(self.member_asOwnerButNotPayer, [
            (
                self.contract_asOwnerButNotPayer,
                self.member_asOwnerButNotPayer,
            ),
            ])

    @unittest.skip("fragile case changed along time, FIX IT!!")
    def test_sortedDefaultContractsForMember_onePayerAndOneOwner_payerFirst(self):
        self.assertContractForMember([
            self.member_aPayerAndAnOwnerContract,
            ], [
            (50851, self.member_aPayerAndAnOwnerContract), # payer
            (43,    self.member_aPayerAndAnOwnerContract), # owner
            ])

    def test_sortedDefaultContractsForMember_manyAsPayer_biggerFirst(self):
        member_manyAsPayer_partnerId = self.erp.SomenergiaSoci.get(self.member_manyAsPayer).partner_id.id
        member_manyAsPayer_unorderedContractIds = self.erp.GiscedataPolissa.search([
            ('pagador', '=', member_manyAsPayer_partnerId),
            ('state','=','activa'),
            ('active','=',True)]
        )
        member_manyAsPayer_expectedContracts = self.orderContractsByConany(
            member_manyAsPayer_unorderedContractIds
        )
        self.assertContractForMember([
            self.member_manyAsPayer,
            ], [ (contract_id, self.member_manyAsPayer)
                for contract_id in
                    member_manyAsPayer_expectedContracts
            ])

    def test_sortedDefaultContractsForMember_manyAsPayerAndManyAsOwner(self):
        # TODO: Check the order is right
        self.assertContractForMember([
            self.member_manyAsPayerAndManyAsOwner,
            ], [
            (self.payerContracts[0], self.member_manyAsPayerAndManyAsOwner),
            (self.payerContracts[1], self.member_manyAsPayerAndManyAsOwner),
            (self.payerContracts[2], self.member_manyAsPayerAndManyAsOwner),
            (self.ownerContracts[0], self.member_manyAsPayerAndManyAsOwner),
            (self.ownerContracts[1], self.member_manyAsPayerAndManyAsOwner),
            ])

    def test_sortedDefaultContractsForMember_severalMembers_doNotBlend(self):
        # TODO: Check the order is right
        member_manyAsPayer_partnerId = self.erp.SomenergiaSoci.get(self.member_manyAsPayer).partner_id.id
        member_manyAsPayer_unorderedContractIds = self.erp.GiscedataPolissa.search([
            ('pagador', '=', member_manyAsPayer_partnerId),
            ('state','=','activa'),
            ('active','=',True)]
        )
        member_manyAsPayer_expectedContracts = self.orderContractsByConany(
            member_manyAsPayer_unorderedContractIds
        )
        self.assertContractForMember([
            self.member_manyAsPayer,
            self.member_manyAsPayerAndManyAsOwner,
            ], [
            (member_manyAsPayer_expectedContracts[0], self.member_manyAsPayer),
            (member_manyAsPayer_expectedContracts[1], self.member_manyAsPayer),
            (self.payerContracts[0], self.member_manyAsPayerAndManyAsOwner),
            (self.payerContracts[1], self.member_manyAsPayerAndManyAsOwner),
            (self.payerContracts[2], self.member_manyAsPayerAndManyAsOwner),
            (self.ownerContracts[0], self.member_manyAsPayerAndManyAsOwner),
            (self.ownerContracts[1], self.member_manyAsPayerAndManyAsOwner),
            ])

    def test_anyForContract_noActiveContracts(self):
        result = self.Assignment.anyForContract(99999999)
        self.assertEqual(result,False)
    
    def test_anyForContract_ActiveOtherContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        result = self.Assignment.anyForContract(99999999)
        self.assertEqual(result,False)

    def test_anyForContract_ActiveOneContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        result = self.Assignment.anyForContract(self.contract)
        self.assertEqual(result,True)

    def test_anyForContract_ExpiredContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        self.Assignment.expire(self.contract,self.member)
        result = self.Assignment.anyForContract(self.contract)
        self.assertEqual(result,False)
        
    def test_anyForContract_ExpiredAndActiveContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        self.Assignment.create({
            'contract_id':self.contract,
            'member_id':self.member,
            'priority': 1
            })
        result = self.Assignment.anyForContract(self.contract)
        self.assertEqual(result,True)

    def test_anyForContract_OtherExpiredActiveContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member2, 1),
            ])
        self.Assignment.expire(self.contract,self.member)
        result = self.Assignment.anyForContract(self.contract2)
        self.assertEqual(result,True)
        
    def test_anyForContract_OtherActiveExpiredContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member2, 1),
            ])
        self.Assignment.expire(self.contract,self.member)
        result = self.Assignment.anyForContract(self.contract)
        self.assertEqual(result,False)





if __name__ == '__main__':
    unittest.TestCase.__str__ = unittest.TestCase.id
    unittest.main()

# vim: et ts=4 sw=4
