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
    update.add_argument('--use-db', dest = 'use_db', action = 'store_true', 
                        help='Use databse from MD government?\n'\
                            '(default: False; use collected data in ./data/*tsv)')
    update.add_argument('--refresh', action = 'store_true', 
                        help='Fetch data and create data table?\n'\
                            '(default: False; only create if the data table is not created today)')

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



