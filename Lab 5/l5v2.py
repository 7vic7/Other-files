import boto3
import time

aws_access_key_id = 'AKIAXD4PI5LYSU3R7S2M'
aws_secret_access_key = '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'
region_name = 'ap-southeast-2'

student_id = '21862278'

# Initialize EC2 and ELB clients
ec2_client = boto3.client('ec2', region_name=region_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
elbv2_client = boto3.client('elbv2', region_name=region_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

# Specify filters to narrow down the search
filters = [{'Name': 'name', 'Values': ['Amazon Linux 2 AMI*']}]

# Use describe_images to get information about AMIs
response = ec2_client.describe_images(Filters=filters)

# Specify the AMI ID
ami_ids = [image['ImageId'] for image in response['Images']]

# Specify the instance type
instance_type = 't2.micro'

# Specify the key pair name 
key_name = 'jinweikey'

# Specify the security group IDs (replace with your security group IDs)
security_group_response = ec2_client.create_security_group(
    GroupName='jinweil5',
    Description='jinwei lab5'
)
security_group_id = security_group_response['GroupId']

# Specify the availability zones
availability_zones = ['ap-southeast-2a', 'ap-southeast-2b']

# Use describe_vpcs to get information VPCs
response = ec2_client.describe_vpcs()
# Get the id of the first one in the list
vpc_id = response['Vpcs'][0]['VpcId']

# Use describe_subnets to get information about subnets
response = ec2_client.describe_subnets()
# Get the IDs of the first two subnets in the list
subnet_ids = [subnet['SubnetId'] for subnet in response['Subnets'][:2]]

# Launch instances in two availability zones
instance_ids = []
for i in range(2):
    response = ec2_client.run_instances(
        ImageId='ami-xxxxxxxxxxxxxxxxx',  # Replace with your AMI ID
        InstanceType=instance_type,
        MinCount=1,
        MaxCount=1,
        KeyName=key_name,
        SecurityGroupIds=[security_group_id],
        Placement={'AvailabilityZone': availability_zones[i]},
        SubnetId=subnet_ids[i],
        UserData=f'''#!/bin/bash
                    yum update -y
                    yum install -y httpd
                    echo "Hello from {student_id}-{availability_zones[i]} instance" > /var/www/html/index.html
                    service httpd start'''
    )
    instance_ids.extend([instance['InstanceId'] for instance in response['Instances']])

print(f'Launched instances: {", ".join(instance_ids)}')

# Wait for instances to be running
print('Waiting for instances to be running...')
ec2_client.get_waiter('instance_running').wait(InstanceIds=instance_ids)
print('Instances are running.')

# Create a target group
target_group_response = elbv2_client.create_target_group(
    Name=f'{student_id}-target-group',
    Protocol='HTTP',
    Port=80,
    VpcId=vpc_id
)
target_group_arn = target_group_response['TargetGroups'][0]['TargetGroupArn']

# Register targets in the target group
targets = [{'Id': instance_id} for instance_id in instance_ids]
elbv2_client.register_targets(TargetGroupArn=target_group_arn, Targets=targets)

# Create a load balancer
load_balancer_response = elbv2_client.create_load_balancer(
    Name=f'{student_id}-load-balancer',
    Subnets=subnet_ids,
    SecurityGroups=[security_group_id],
    Scheme='internet-facing',
    LoadBalancerAttributes=[
        {'Key': 'idle_timeout.timeout_seconds', 'Value': '60'}
    ]
)
load_balancer_arn = load_balancer_response['LoadBalancers'][0]['LoadBalancerArn']

# Create a listener with a default rule
elbv2_client.create_listener(
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

print('Load balancer and listener created.')

# Wait for the load balancer to be active
print('Waiting for the load balancer to be active...')
elbv2_client.get_waiter('load_balancer_exists').wait(Names=[f'{student_id}-load-balancer'])
print('Load balancer is active.')

# Print information for accessing instances
print('\nAccess your instances using the following public IP addresses:')
for i, instance_id in enumerate(instance_ids):
    instance_details = ec2_client.describe_instances(InstanceIds=[instance_id])
    public_ip = instance_details['Reservations'][0]['Instances'][0]['PublicIpAddress']
    print(f'Instance {i+1}: {public_ip}')
