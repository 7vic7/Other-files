import boto3

# Initialize the ELBv2 client
client = boto3.client('elbv2')

# Initialize the EC2 resource
ec2 = boto3.resource('ec2', region_name='ap-southeast-2')

# Provided details
AMI_ID = 'ami-0c7c2fcf9f0885c8c'
KEY_NAME = 'jinweil5'
SECURITY_GROUP_NAME = '21862278l5'

# Create the first EC2 instance in 'ap-southeast-2a'
instance1 = ec2.create_instances(
    ImageId=AMI_ID,
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    KeyName=KEY_NAME,
    SecurityGroups=[SECURITY_GROUP_NAME],
    Placement={'AvailabilityZone': 'ap-southeast-2a'}
)[0]

# Create the second EC2 instance in 'ap-southeast-2b'
instance2 = ec2.create_instances(
    ImageId=AMI_ID,
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    KeyName=KEY_NAME,
    SecurityGroups=[SECURITY_GROUP_NAME],
    Placement={'AvailabilityZone': 'ap-southeast-2b'}
)[0]

print(f"Instance 1 ID: {instance1.id} created in 'ap-southeast-2a'")
print(f"Instance 2 ID: {instance2.id} created in 'ap-southeast-2b'")


# Extracting details from instance1
subnet_id_1 = instance1.subnet_id
security_group_id_1 = instance1.security_groups[0]['GroupId']
vpc_id_1 = instance1.vpc_id
instance_id_1 = instance1.id

# Extracting details from instance2
subnet_id_2 = instance2.subnet_id
security_group_id_2 = instance2.security_groups[0]['GroupId']  # Assuming same security group for both instances
vpc_id_2 = instance2.vpc_id  # This should be the same as vpc_id_1 if both instances are in the same VPC
instance_id_2 = instance2.id

print(f"Subnet ID 1: {subnet_id_1}")
print(f"Subnet ID 2: {subnet_id_2}")
print(f"Security Group ID: {security_group_id_1}") 
print(f"Security Group ID: {security_group_id_2}") # Both instances use the same security group
print(f"VPC ID: {vpc_id_1}") 
print(f"VPC ID: {vpc_id_2}")  # Both instances are in the same VPC
print(f"Instance ID 1: {instance_id_1}")
print(f"Instance ID 2: {instance_id_2}")



# Create the load balancer
response = client.create_load_balancer(
    Name='MyApplicationLoadBalancer',
    Subnets=[subnet_id_1, subnet_id_2],  # Replace with your subnet IDs
    SecurityGroups=[security_group_id_1],  # Replace with your security group ID
    Scheme='internet-facing',
    Type='application'
)
load_balancer_arn = response['LoadBalancers'][0]['LoadBalancerArn']

# Create a target group
response = client.create_target_group(
    Name='JinweiTargetGroup',
    Protocol='HTTP',
    Port=80,
    VpcId=vpc_id_1,  # Replace with your VPC ID
    TargetType='instance'
)
target_group_arn = response['TargetGroups'][0]['TargetGroupArn']

# [c] Register targets in the target group
client.register_targets(
    TargetGroupArn=target_group_arn,
    Targets=[
        {'Id': instance_id_1},  
        {'Id': instance_id_2}   
    ]
)

# Create a listener
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

print("Application Load Balancer and related components created successfully!")