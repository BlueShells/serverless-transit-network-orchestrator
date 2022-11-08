

from subprocess import check_output
from zoneinfo import available_timezones
from botocore.exceptions import ClientError
from optparse import OptionParser
import json
import boto3
import copy
import re
import logging
import time


def list_s3(client):
    try:
        response = client.list_buckets()
    except ClientError as err:
        print(err)
    return response
def delete_s3(session, delete_bucket):

    try:
        s3 = session.resource('s3')
        print(f"Removing bucket {delete_bucket}.")
        bucket = s3.Bucket(delete_bucket)
        print("bucket content:")
        object_summary_iterator = bucket.objects.all()
        for object in object_summary_iterator:
            print(object)
        #confirmation = input(f"Do you want to continue to remove this bucket {options.bucket}? Y/N :")

        bucket.object_versions.delete()
        # if you want to delete the now-empty bucket as well, uncomment this line:
        bucket.delete()
        print(f"Bucket {options.bucket} been removed successfully.")
    except ClientError as err:
        if err.response['Error']['Code'] == 'NoSuchBucket':
            print(f"Bucket {options.bucket} does not exist in account {account_id} !!!")
        else:
            print(err)


def run_cmd(cmd):
    output_cmd=copy.deepcopy(cmd)
    # filter the aksk values
    output_cmd = re.sub("(?<=AWS_ACCESS_KEY_ID)([\w+=/]+)","",output_cmd)
    output_cmd = re.sub("(?<=AWS_SECRET_ACCESS_KEY)([\w+=/]+)","",output_cmd)
    output_cmd = re.sub("(?<=AWS_SESSION_TOKEN)([\w+=/]+)","",output_cmd)
    output_cmd = re.sub("(?<=AWS_SECURITY_TOKEN)([\w+=/]+)","",output_cmd)
    print(f"Run {output_cmd}")
    output_return = check_output(cmd, shell=True).decode('utf-8')
    print(output_return)
    return 

if __name__ == '__main__':
    usage = "Usage: \n%prog -p <aws-profile-name>"

    parser = OptionParser(usage,version='%prog 1.0') 


    parser.add_option('-p','--profile',  
                      help='Only use if your default aws profile is not for mgn account: [example: aws-profile-master]')

    parser.add_option('-r','--region',  
                      help='Only use if your default aws profile is not for mgn account: [example: aws-profile-master]')


    parser.add_option('-b','--bucket',  
                      help='Please input the s3 bucket you would like to remove')

    parser.add_option('-n','--nameprefix',  
                      help='Please input the s3 bucket prefix')


    options, args = parser.parse_args()    
    if options.profile and options.region:
        session = boto3.session.Session(profile_name=options.profile, region_name=options.region)
    elif options.profile:
        session = boto3.session.Session(profile_name=options.profile)
    elif options.region:
        session = boto3.session.Session(region_name=options.region)
    else:
        session = boto3.session.Session()

    nameprefix = "cn-cloudfoundation"
    if options.nameprefix:
        nameprefix = options.nameprefix

    account_id = session.client("sts").get_caller_identity()["Account"]

    s3list = list_s3(session.client("s3"))
    print(f"get all the s3 from current account {options.profile}")
    print(s3list['Buckets'])
    print(f"start clean s3 with prefix: {nameprefix}")
    for d_buckt in s3list['Buckets']:
        if d_buckt['Name'].startswith(nameprefix):
            delete_s3(session, d_buckt['Name'])
    

   
