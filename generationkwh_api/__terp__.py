# -*- coding: utf-8 -*-
{
  "name": "Generation kWh",
  "description": """Support for SomEnergia's Generation kWh in GisceERP""",
  "version": "0.0.1",
  "author": "GISCE-TI & Som Energia",
  "category": "Master",
  "depends": [
    'base',
    'som_polissa_soci',
    'som_inversions',
    'plantmeter_api',
    ],
  "init_xml": [],
  "demo_xml": [],
  "update_xml": [
    "security/generationkwh_api_security.xml",
    "generationkwh_api_data.xml",
    "giscedata_facturacio_view.xml",
    "generationkwh_api_view.xml",
    "investment_view.xml",
    "security/ir.model.access.csv",
    ],
  "active": False,
  "installable": True
}
