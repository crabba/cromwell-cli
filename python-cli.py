#! /usr/bin/env python3

import boto3
import click
import coloredlogs
import jq
import json
import logging


@click.group()
@click.option('-v', '--verbose', count = True , help = "Verbosity (cumulative)")
@click.option('--profile', default='default', help='AWS CLI Profile')
def main(verbose, profile):
    if verbose > 0:
        logging.getLogger().setLevel(logging.DEBUG)
        
    logging.warning(f"Using profile {profile}")
    level = logging.getLogger().getEffectiveLevel()
    level_name = logging.getLevelName(level)
    logging.warning(f"Log level {level_name}")
    boto3.setup_default_session(profile_name=profile)
    # Example client
    global sts_c
    sts_c = boto3.client('sts')

@main.command()
def foo():
    '''Foo method'''
    # Code goes here
    
@main.command()
@click.option('--someparam', required=True, help='Function with a parameter')
def bar(someparam):
    '''Bar method'''
    logging.info(f"bar({someparam})")

@main.command()
def get_caller_identity():
    '''Display AWS account number'''
    caller_identity = sts_c.get_caller_identity()
    print(caller_identity['Account'])

if __name__ == '__main__':
    coloredlogs.install(fmt='%(asctime)s,%(msecs)03d %(lineno)3d:%(funcName)20s %(levelname)s %(message)s')
    main()
