#!/usr/bin/env python

from src.update import update, check_update
from src.download import get
import argparse

def get_opt():
    parser = argparse.ArgumentParser(description='Tools for updating dashboard')
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

    #chekc update
    check = subparsers.add_parser(name = 'check',
                                description='check if MD gov database is updated?')

    #get data fomr date
    check = subparsers.add_parser(name = 'get',
                                description='get data from a given date')
    check.add_argument('--date', help = 'Getting data for this date (e.g. 2020-09-10)', required=True)
    # update dashboard 
    update = subparsers.add_parser(name = 'update', description='Update COVID19 dashboard',
                                    formatter_class=argparse.RawTextHelpFormatter)
    update.add_argument('--datadir', dest = 'datadir', default = './data', 
                        help='Data directory for tsv files, if not supplied, MD goverment data will be used')
    update.add_argument('--refresh', action = 'store_true', 
                        help='Fetch data and create data table?\n'\
                            '(default: False; only create if the data table is not created today)')
    update.add_argument('-o','--out_html', default = './dashboard.html', 
                        help='Output html file path')

    args = parser.parse_args() 
    return args


if __name__ == '__main__':
    args = get_opt()
    if args.subcommand == 'update':
        update(args)
    elif args.subcommand == 'check':
        check_update()
    elif args.subcommand == 'get':
        get(args.date)



