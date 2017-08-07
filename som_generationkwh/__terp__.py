# -*- coding: utf-8 -*-
{
  "name": "Generation kWh",
  "description": """Support for SomEnergia's Generation kWh in GisceERP""",
  "version": "1.6",
  "author": "GISCE-TI & Som Energia",
  "category": "Master",
  "depends": [
    'base',
    "poweremail",
    "poweremail_references",
    'som_polissa_soci',
    'som_inversions',
    'som_plantmeter',
    ],
  "init_xml": [],
  "demo_xml": [],
  "update_xml": [
    "som_generationkwh_data.xml",
    "giscedata_facturacio_view.xml",
    "som_generationkwh_view.xml",
    "wizard/wizard_investment_activation.xml",
    "wizard/wizard_investment_amortization.xml",
    "wizard/wizard_investment_payment.xml",
    "investment_view.xml",
    "assignment_view.xml",
    "somenergia_soci_view.xml",
    "somenergia_soci_data.xml",
    "security/som_generationkwh_security.xml",
    "security/ir.model.access.csv",
    "amortization_report.xml"
    ],
  "active": False,
  "installable": True
}
