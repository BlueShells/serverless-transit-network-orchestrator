

from pydoc import cli
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


def list_tgw(client):
    response = client.describe_transit_gateways(
        MaxResults=123
    )

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
def delete_tgw(client, tgw_id):
    #1 get attach ments
    attached_vpcs = get_attached_vpc(client, tgw_id)
    #print(attached_vpcs)
    
    for attached_vpc in attached_vpcs['TransitGatewayVpcAttachments']:
        print("atachme",attached_vpc['TransitGatewayAttachmentId'])
        #2 remove vpc attachment
        remove_attach_from_tgw(client, attached_vpc['TransitGatewayAttachmentId'])
    response = client.delete_transit_gateway(
        TransitGatewayId=tgw_id
    )

def get_attached_vpc(client, tgw_id):
    response = client.describe_transit_gateway_vpc_attachments(
        Filters=[
            {
                'Name': 'transit-gateway-id',
                'Values': [
                    tgw_id
                ]
            }
        ],
        MaxResults=123
    )
    return response

def remove_attach_from_tgw(client, transitGatewayAttachment_id):
    response = client.delete_transit_gateway_vpc_attachment(
        TransitGatewayAttachmentId= transitGatewayAttachment_id
    )
    return response

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
    tgw_client = session.client("ec2")
    tgwlist = list_tgw(tgw_client)

    #print(tgwlist['TransitGateways'])

    for tgw in tgwlist['TransitGateways']:
        print(f"going to delete: {tgw['TransitGatewayArn']}")
        tgw_name = ""
        tags = tgw['Tags']
        print(tags)
        for tag in tags:
            if tag['Key']  == "Name":
                tgw_name = tag['Value']
        if tgw_name.startswith("STNO-TGW"):
            print("deleting tgw ",tgw_name)
            delete_tgw(tgw_client, tgw['TransitGatewayId'])

    
    

   
