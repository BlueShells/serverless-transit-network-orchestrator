

from pydoc import cli
from subprocess import check_output
from zoneinfo import available_timezones
from botocore.exceptions import ClientError
from optparse import OptionParser
import boto3
import time
import os 


def list_tgw(client):
    response = client.describe_transit_gateways(
        Filters=[
        {
            'Name': 'state',
            'Values': [
                'available','failed'
            ]
        },
    ],
        MaxResults=123
    )

    return response

def delete_tgw(client, tgw_id):
    #1 get attach ments
    attached_vpcs = get_attached_vpc(client, tgw_id)
    #print(attached_vpcs)
    taatched_vpcs_ids = []
    for attached_vpc in attached_vpcs['TransitGatewayVpcAttachments']:
        #print("atachme",attached_vpc['TransitGatewayAttachmentId'])
        taatched_vpcs_ids.append(attached_vpc['TransitGatewayAttachmentId'])
        #2 remove vpc attachment
        remove_attach_from_tgw(client, attached_vpc['TransitGatewayAttachmentId'])
    #3 check status make sure attachment detached "Deleted"
    while True:
        vpc_attachement_deleted = get_attached_vpc_deletedstatus(client, taatched_vpcs_ids)
        if vpc_attachement_deleted:
            print("confirmed all the attachment been deleted")
            break 
        time.sleep(15)
    try:        
        response = client.delete_transit_gateway(
            TransitGatewayId=tgw_id
        )
    except ClientError as err:
        print(err)
    

def get_attached_vpc_deletedstatus(client, vpcids):
    result = True
    #print(f"vpcids :{vpcids}")
    try:
        response = client.describe_transit_gateway_vpc_attachments(
            TransitGatewayAttachmentIds=vpcids,
            MaxResults=123,
        )
        for attch in response['TransitGatewayVpcAttachments']:
            if attch['State'] != 'deleted':
                result = False 
                break
        return result
    except ClientError as err:
        print(err)

    

    

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
    try:
        print(f"trying to delete attachment: {transitGatewayAttachment_id}")
        response = client.delete_transit_gateway_vpc_attachment(
            TransitGatewayAttachmentId= transitGatewayAttachment_id
        )
    except ClientError as err:
        print(err)
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
    print(f"going to clean up all the tgw with prefix: {nameprefix}")
    if len(tgwlist['TransitGateways']) == 0:
        print("all the transit gateway been removed")
        os._exit(os.EX_OK)

    for tgw in tgwlist['TransitGateways']:
        tgw_name = ""
        tags = tgw['Tags']
        print(tags)
        for tag in tags:
            if tag['Key']  == "Name":
                tgw_name = tag['Value']
        if tgw_name.startswith("STNO-TGW"):
            print("deleting tgw ",tgw_name)
            delete_tgw(tgw_client, tgw['TransitGatewayId'])

    
    

   
