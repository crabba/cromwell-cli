#! /usr/bin/env python3

import boto3
import chevron
import click
import coloredlogs
import datetime
import jq
import json
import logging
import os
import re
import requests
import sys
import tempfile
import urllib3

MAX_FILES = 10
INPUTS_FILE_MUSTACHE = 'parliament2_inputs.mustache'

def make_url(host):
    '''Return url and headers for given host'''
    url = f"https://{host}/api/workflows/v1"
    headers = {
        'accept': 'application/json',
    }
    return(url, headers)

def print_response(response):
    if response:
        print("Success")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.status_code}")
        # print(json.dumps(response.json()))
        print(response.text)

def bai_from_bam(bam):
    '''Return string of bam key edited with .bai suffix'''
    return bam.key.replace('.bam', '.bai', 1)

def has_bai_object(bam, objects):
    '''Return True if given bam object has corresponding bai object'''
    bai_key = bai_from_bam(bam)
    bai_objects = [elem for elem in objects if elem.key == bai_key]
    ret = len(bai_objects) == 1
    logging.debug(f"Test for {bai_key} returning {ret}")
    return ret

def bam_objects_in(bucket, prefix):
    bucket_r = s3_r.Bucket(bucket)
    bucket_objects = bucket_r.objects.filter(Prefix = prefix)
    count_obj = sum(1 for _ in bucket_objects.all())
    bam_objects = [elem for elem in bucket_objects if elem.key.endswith('.bam')]
    bam_objects_with_index = [elem for elem in bam_objects if has_bai_object(elem, bucket_objects)]
    logging.info(f"{len(bam_objects_with_index)} BAM objects with BAI index in {bucket}")
    return(bam_objects_with_index)

def create_inputs_file(bam_object):
    '''Return contents of a parliament2.inputs.json file from mustache template, with bam file name'''
    logging.debug(f"bam_object: {bam_object}")
    bam_path = f"{bam_object.bucket_name}/{bam_object.key}"
    bai_path = re.sub(r'.bam$', '.bai', bam_path)
    args = {
        'bam_s3': f"s3://{bam_path}",
        'bai_s3': f"s3://{bai_path}"
    }
    with open(INPUTS_FILE_MUSTACHE, 'r') as f:
        out = chevron.render(f, args)
    return(out)

def do_run(host, source, inputs):
    '''Submit POST request to host
    host: Cromwell server
    source: Name of file for workflowSource
    inputs: Contents of file for workflowInputs
    '''
    logging.info(f"run({source}) on {host}")
    
    # Create request
    (url, headers) = make_url(host)
    files = {
        'workflowSource': open(source, 'rb'),
        'workflowInputs': inputs
    }
    response = requests.post(url, headers=headers, files=files, verify=False)
    print_response(response)

@click.group()
@click.option('-v', '--verbose', count = True , help = "Verbosity (cumulative)")
@click.option('-p', '--profile', default = 'default', help = 'AWS CLI Profile')
def main(verbose, profile):
    if verbose > 0:
        logging.getLogger().setLevel(logging.DEBUG)
        
    logging.warning(f"Using profile {profile}")
    level = logging.getLogger().getEffectiveLevel()
    level_name = logging.getLevelName(level)
    logging.warning(f"Log level {level_name}")
    boto3.setup_default_session(profile_name=profile)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # Example client
    global s3_r
    s3_r = boto3.resource('s3')

@main.command()
@click.option('--host', required = True, help = 'DNS name or IP of Cromwell host')
@click.option('--source', required = True, help = 'WDL input file')
@click.option('--bucket', required = True, help = 'Bucket of BAM files to process')
@click.option('--prefix', required = True, help = 'Prefix of objects within bucket')
def run_bucket(host, source, bucket, prefix):
    '''Call run() on each BAM file in the given bucket'''
    bam_objects = bam_objects_in(bucket, prefix)
    if len(bam_objects) > MAX_FILES:
        logging.error(f"Number of objects in {bucket}/{prefix} ({len(bam_objects)}) exceeds limit of {MAX_FILES}")
        sys.exit(1)
    for bam_object in bam_objects:
        inputs_file = create_inputs_file(bam_object)
        do_run(host, source, inputs_file)

# curl --insecure -X POST "https://ec2-52-203-201-171.compute-1.amazonaws.com/api/workflows/v1" \
#     -H  "accept: application/json" \
#     -F "workflowSource=@./parliament2.wdl" \
#     -F "workflowInputs=@parliament2.inputs.json"

@main.command()
@click.option('--host', required = True, help = 'DNS name or IP of Cromwell host')
@click.option('--source', required = True, help = 'WDL input file')
@click.option('--inputs', required = False, help = 'JSON inputs file')
def run(host, source, inputs):
    '''Run given source WDL file with inputs JSON file'''
    # Inputs is sent as contents to match behaviour of run_bucket which generates contents
    # TODO: Some workflows (eg: hello world) don't use inputs
    # Accommodate this with if inputs is not None:, send empty string, test for this in do_run()
    
    with open(inputs, 'r') as fp:
        input_contents = fp.read()
    do_run(host, source, input_contents)

@main.command()
@click.option('--host', required = True, help = 'DNS name or IP of Cromwell host')
@click.option('--days', default = 1, help = 'Range of days in past to include')
def query(host, days):
    '''Query host for all workflows'''
    logging.info(f"query() on {host} in past {days} days")
    (url, headers) = make_url(host)

    now = datetime.datetime.utcnow()
    starttime = now - datetime.timedelta(days = days)

    response = requests.get(
        f"{url}/query", 
        headers=headers, 
        verify=False,
        params={'submission': f"{starttime.isoformat()}Z"}
        )
    print_response(response)


if __name__ == '__main__':
    coloredlogs.install(fmt='%(asctime)s,%(msecs)03d %(lineno)3d:%(funcName)20s %(levelname)s %(message)s')
    main()
