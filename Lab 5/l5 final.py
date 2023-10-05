import boto3

# Initialize the ELBv2 client
client = boto3.client('elbv2')

# Initialize the EC2 resource and client for the specified region
ec2 = boto3.resource('ec2', region_name='ap-southeast-2')
ec2_client = boto3.client('ec2', region_name='ap-southeast-2')

# Define details
AMI_ID = 'ami-0c7c2fcf9f0885c8c'
KEY_NAME = '21862278-key'
SECURITY_GROUP_NAME = '21862278l5'




# Check if the specified security group already exists
# If not, create a new security group with the given name and description
try:
    response = ec2_client.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])
    security_group_id = response['SecurityGroups'][0]['GroupId']
    print(f"Security group {SECURITY_GROUP_NAME} already exists with ID {security_group_id}.")
except ec2_client.exceptions.ClientError as e:
    if "InvalidGroup.NotFound" in str(e):
        response = ec2_client.create_security_group(GroupName=SECURITY_GROUP_NAME, Description='jinwei l5')
        security_group_id = response['GroupId']
        print(f"Created security group {SECURITY_GROUP_NAME} with ID {security_group_id}.")
    else:
        raise





# Create the first EC2 instance in 'ap-southeast-2a'
instance1 = ec2.create_instances(
    ImageId=AMI_ID,
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    KeyName=KEY_NAME,
    SecurityGroupIds=[security_group_id],
    Placement={'AvailabilityZone': 'ap-southeast-2a'},
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': '21862278-ap-southeast-2a'
                }
            ]
        }
    ]
)[0]

# Create the second EC2 instance in 'ap-southeast-2b'
instance2 = ec2.create_instances(
    ImageId=AMI_ID,
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    KeyName=KEY_NAME,
    SecurityGroupIds=[security_group_id],
    Placement={'AvailabilityZone': 'ap-southeast-2b'},
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': '21862278-ap-southeast-2b'
                }
            ]
        }
    ]
)[0]

# Wait for the instances to be in a running state
instance1.wait_until_running()
instance2.wait_until_running()


# Print the IDs of the created instances
print(f"Instance 1 ID: {instance1.id} created in 'ap-southeast-2a'")
print(f"Instance 2 ID: {instance2.id} created in 'ap-southeast-2b'")




# Extracting details from instance1
subnet_id_1 = instance1.subnet_id
vpc_id_1 = instance1.vpc_id
instance_id_1 = instance1.id

# Extracting details from instance2
subnet_id_2 = instance2.subnet_id
vpc_id_2 = instance2.vpc_id  # This should be the same as vpc_id_1 if both instances are in the same VPC
instance_id_2 = instance2.id

# Print the extracted details
print(f"Subnet ID 1: {subnet_id_1}")
print(f"Subnet ID 2: {subnet_id_2}")
print(f"VPC ID: {vpc_id_1}") 
print(f"VPC ID: {vpc_id_2}")  # Both instances are in the same VPC
print(f"Instance ID 1: {instance_id_1}")
print(f"Instance ID 2: {instance_id_2}")



# Create the load balancer
response = client.create_load_balancer(
    Name='jinweiLoadLalancer',
    Subnets=[subnet_id_1, subnet_id_2],  
    SecurityGroups=[security_group_id],  
    Scheme='internet-facing',
    Type='application'
)
load_balancer_arn = response['LoadBalancers'][0]['LoadBalancerArn']

# Create a target group for the load balancer
response = client.create_target_group(
    Name='JinweiTargetGroup',
    Protocol='HTTP',
    Port=80,
    VpcId=vpc_id_1,  
    TargetType='instance'
)
target_group_arn = response['TargetGroups'][0]['TargetGroupArn']

print("Application Load Balancer created successfully!")


# Register the created EC2 instances as targets for the target group
client.register_targets(
    TargetGroupArn=target_group_arn,
    Targets=[
        {'Id': instance_id_1},  
        {'Id': instance_id_2}   
    ]
)

print("Register targets in the target group successfully!")


# Create a listener for the load balancer to forward HTTP requests to the target group
client.create_listener(
    LoadBalancerArn=load_balancer_arn,
    Protocol='HTTP',
    Port=80,
    DefaultActions=[
        {
            'Type': 'forward',
            'TargetGroupArn': target_group_arn
        }
    ]
)

print("Listener created successfully!")
