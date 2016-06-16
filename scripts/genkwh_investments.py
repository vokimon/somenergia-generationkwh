#!/usr/bin/env python
description = """
Generates investments from the accounting logs.
"""

import erppeek
import datetime
from dateutil.relativedelta import relativedelta
from yamlns import namespace as ns
from generationkwh.isodates import isodate

def erp():
    global c
    import dbconfig
    return c or erppeek.Client(**dbconfig.erppeek)

def parseArgumments():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-C', '--config',
        dest='config',
        metavar='DBCONFIG.py',
        help="use that DBCONFIG.py as configuration file "
            "instead of default dbconfig.py at script location.",
        )

    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest='subcommand',
        )
    listactive = subparsers.add_parser('listactive',
        help="list active investments objects",
        )
    create = subparsers.add_parser('create',
        help="create investments objects from accounting information",
        )
    effective = subparsers.add_parser('effective',
        help="turn investment effective",
        )
    clear = subparsers.add_parser('clear',
        help="clear investments objects",
        )
    extend = subparsers.add_parser('extend',
        help="extend the expiration date of a set of investments",
        )
    for sub in effective,create: 
        sub.add_argument(
            '--force',
            action='store_true',
            help="do it even if they where already computed",
            )
    for sub in listactive,: 
        sub.add_argument(
            '--member',
            type=int,
            metavar='MEMBERID',
            help="filter by member",
            )
    for sub in effective,create,clear,listactive: 
        sub.add_argument(
            '--start','--from','-f',
            type=isodate,
            metavar='ISODATE',
            help="first purchase date to be considered",
            )
        sub.add_argument(
            '--stop','--to','-t',
            type=isodate,
            metavar='ISODATE',
            help="last purchase date to be considered",
            )
    for sub in effective,create: 
        sub.add_argument(
            '--wait',
            '-w',
            dest='waitingDays',
            type=int,
            metavar='DAYS',
            help="number of days from the purchase date until "
                "they provide usufruct",
            )
        sub.add_argument(
            '--expires',
            '-x',
            dest='expirationYears',
            type=int,
            metavar='YEARS',
            help="number of years the shares will provide usufruct"
            )
    return parser.parse_args(namespace=ns())

def clear(**args):
    ids = erp().GenerationkwhInvestment.dropAll()

def listactive(member=None, start=None, stop=None, csv=False):
    """
        List active investments between start and stop, both included,
        for the member of for any member if member is None.
        If start is not specified, it lists activated before stop.
        If stop is not specified, it list activated and not deactivated
        before start.
        If neither start or stop are specified all investments are listed
        active or not.
    """
    def buildcsv(data):
        return u''.join((
            u"\t".join((
                unicode(c) for c in line
                ))+'\n'
            for line in data))

    csvdata = buildcsv(erp().GenerationkwhInvestment.effective_investments_tuple(
            member, start and str(start), stop and str(stop)))
    if csv: return csvdata
    print csvdata

def create(start=None, stop=None,
        waitingDays=None,
        expirationYears=None,
        force=False,
        **_):
    if force: clear()
    erp().GenerationkwhInvestment.create_from_accounting(
        None, # member
        start and str(start),
        stop and str(stop),
        waitingDays,
        expirationYears,
        )

def effective(
        waitingDays,
        start=None, stop=None,
        expirationYears=None,
        force=False,
        **_):

    return erp().GenerationkwhInvestment.set_effective(
        start and str(start),
        stop and str(stop),
        waitingDays,
        expirationYears,
        force,
        )

c = None

def main():
    args = parseArgumments()
    print args.dump()

    if args.config:
        import imp
        dbconfig = imp.load_source('config',args.config)
    else:
        import dbconfig

    global c
    c = c or erppeek.Client(**dbconfig.erppeek)
    del args.config

    # Calls the function homonymous to the subcommand
    # with the options as paramteres
    subcommand = args.subcommand
    del args.subcommand
    globals()[subcommand](**args)

if __name__ == '__main__':
    main()



