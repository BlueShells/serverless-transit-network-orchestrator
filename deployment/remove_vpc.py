

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

def get_tag_Name(tags):
    result = None
    #print(tags)
    tags_keys = [key['Key'] for key in tags]
    if "Name" in tags_keys:
        for tag in tags:
            if tag['Key'] == "Name":
                result = tag['Value']
        
    else:
        pass 
    return result

#####start vpc 
def list_vpcs(client):
    try:
        response = client.describe_vpcs(
            MaxResults=123
        )
        return response
    except ClientError as err:
        print(err)

def delete_vpc(client, vpcid , account_id, region):
    print(f"going to delete vpc: {vpcid}")
    subnets_info = get_subnet_withvpcid(client, vpcid)
    subnets_arns = [item['SubnetArn'] for item in subnets_info['Subnets']]
    for subnet_arn in subnets_arns:
        delete_subnet_withid(client, subnet_arn , account_id, region)
    
    internete_gateways = get_internet_gateways(client, vpcid)
    for internet_gateway in internete_gateways['InternetGateways']:
        
        detach_internet_gateway(client, internet_gateway['InternetGatewayId'], vpcid)
        time.sleep(10)
        delete_internet_gateways(client, internet_gateway['InternetGatewayId'])

    time.sleep(10)
    #confirm if subnet deleted
    while True:
        subnets_info = get_subnet_withvpcid(client, vpcid)
        if len(subnets_info['Subnets']) == 0 :
            print(f"all the subnet delete for this vpc {vpcid}")
            break
        else:
            print("subnets still in deleting status")
            time.sleep(10)
    try:
        response = client.delete_vpc(
            VpcId=vpcid,
        )
        return response
    except ClientError as err:
        print(err)
    




def get_subnet_withvpcid(client, vpcid):
    try:
        response = client.describe_subnets(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpcid
                    ]
                },
            ],
            MaxResults=123
        )
        return response
    except ClientError as err:
        print(err)

def delete_subnet_withid(client, subnet_id , account_id, region):
    try:
        print(f"going to delete subnet {subnet_id}")
        arn_format = "arn:aws-cn:ec2:"+region+":"+account_id+":subnet/"
        subnet_short_id = subnet_id.replace(arn_format,"")
        #print(f"subnet_short_id: {subnet_short_id}")
        response = client.delete_subnet(
            SubnetId= subnet_id.replace(arn_format,"")
        )
        return response
        
    except ClientError as err:
        print(err)

def get_internet_gateways(client, vpcid):
    try:
        response = client.describe_internet_gateways(
            Filters=[
                {
                    'Name': 'attachment.vpc-id',
                    'Values': [
                        vpcid
                    ]
                },
            ],
            MaxResults=123
        )
        return response
        #respone['InternetGateways][0]['InternetGatewayId']
    except ClientError as err:
        print(err)

def delete_internet_gateways(client, gatewayid):
    try:
        print(f"going to delete gateway : {gatewayid}")
        response = client.delete_internet_gateway(
            InternetGatewayId=gatewayid,
        )
        return response
    except ClientError as err:
        print(err)
def detach_internet_gateway(client, gatewayid, vpcid_short):
    try:
        print(f"going to detach internetgateway : {gatewayid} from :{vpcid_short}" )
        response = client.detach_internet_gateway(
            InternetGatewayId=gatewayid,
            VpcId=vpcid_short,
        )
    except ClientError as err:
        print(err)


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
    parser.add_option("-f", "--force",
                  action="store_true", dest="force", default=False,
                  help="force mode to clean all the vpc and subnet")

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
    region = session.region_name
    #print(f"region is : {region}")
    
    if options.nameprefix:
        nameprefix = options.nameprefix

    account_id = session.client("sts").get_caller_identity()["Account"]
    vpc_client = session.client("ec2")
    #print(f"vpc_client : {vpc_client}")
    #get all the list of vpc in the current account region
    vpcslist = list_vpcs(vpc_client)['Vpcs']

    for vpc in vpcslist:
        if options.force:
                delete_vpc(vpc_client, vpc['VpcId'], account_id, region)
        else:
            if "Tags" in vpc:
                #print(f"vpc: {vpc}")
                vpcid = vpc['VpcId']
                tags= vpc['Tags']
                vpc_name = get_tag_Name(tags)

                
                if vpc_name and vpc_name.startswith(nameprefix):
                    print(f"going to clean up vpc {vpc_name}")
                    delete_vpc(vpc_client, vpcid, account_id, region)
            else:
                print(f"this vpc: {vpc['VpcId']} didn't have tag , skip")





    
    

   
