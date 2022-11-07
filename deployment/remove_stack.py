import boto3
from optparse import OptionParser
from botocore.exceptions import ClientError



def disable_protection(client, stackname):
    '''disable stack Terminationprotection'''
    try:
        response = client.update_termination_protection(
            EnableTerminationProtection=False,
            StackName=stackname
        )
    except ClientError as err:
        print(err.response)

def delete_stack(client, stackname):
    '''delete stack'''
    try:
        response = client.delete_stack(
            StackName=stackname,
        )
    except ClientError as err:
        print(err.response)
        
def get_stacks(client):
    '''get all the stack in current account and region'''
    response = {}
    try:
        response = client.list_stacks(
            StackStatusFilter=[
                'CREATE_COMPLETE','UPDATE_COMPLETE'
            ]
        )
    except ClientError as err:
        print(err.response)

    return response
if __name__ == '__main__':

    parser = OptionParser() 
    parser.add_option('-p','--profile',  
                      help='Only use if your default aws profile is not for mgn account: [example: aws-profile-master]')

    parser.add_option('-r','--region',  
                      help='Only use if your default aws profile is not for mgn account: [example: aws-profile-master]')
    options, args = parser.parse_args()  

    if options.profile and options.region:
        session = boto3.session.Session(profile_name=options.profile, region_name=options.region)
    elif options.profile:
        session = boto3.session.Session(profile_name=options.profile)
    elif options.region:
        session = boto3.session.Session(region_name=options.region)
    else:
        session = boto3.session.Session()
    
    client = session.client("cloudformation")
    
    stack_list_info = get_stacks(client)

    stacks_info = stack_list_info['StackSummaries']

    
    last_delete_stackname = ""
    for stack in stacks_info:
        if stack['StackName'].startswith("cn-cloudfoundation") and 'selfstack' not in stack['StackName']:
            disable_protection(client, stack['StackName'])
            delete_stack(client, stack['StackName'])
        if 'selfstack' in stack['StackName']:
            last_delete_stackname = stack['StackName']

    if last_delete_stackname:
        delete_stack(client, last_delete_stackname)
        
        