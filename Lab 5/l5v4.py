import boto3

# Initialize Boto3 client for EC2 and ELBv2
ec2 = boto3.resource('ec2')
client = boto3.client('elbv2')

# [1] Create 2 EC2 instances in two different availability zones
instances = ec2.create_instances(
    ImageId='<AMI_ID>',  # Replace with your AMI ID
    MinCount=2,
    MaxCount=2,
    InstanceType='t2.micro',
    KeyName='jinweil5',  # Replace with your key name
    SecurityGroups=['21862278l5-sg'],  # Replace with your security group name
    Placement={'AvailabilityZone': '<AVAILABILITY_ZONE_1>'}  # Replace with your first availability zone
)

# Naming the instances
student_number = '<STUDENT_NUMBER>'  # Replace with your student number
for i, instance in enumerate(instances):
    instance.create_tags(Tags=[{
        'Key': 'Name',
        'Value': f'{student_number}-<AVAILABILITY_ZONE_{i+1}>'
    }])

# [2] Create the Application Load Balancer

# [a] Create the load balancer
response = client.create_load_balancer(
    Name='MyLoadBalancer',
    Subnets=['<SUBNET_ID_1>', '<SUBNET_ID_2>'],  # Replace with your subnet IDs
    SecurityGroups=['<SECURITY_GROUP_ID>'],  # Replace with your security group ID
    Scheme='internet-facing',
    Type='application'
)
load_balancer_arn = response['LoadBalancers'][0]['LoadBalancerArn']

# [b] Create a target group
response = client.create_target_group(
    Name='MyTargetGroup',
    Protocol='HTTP',
    Port=80,
    VpcId='<VPC_ID>',  # Replace with your VPC ID
    TargetType='instance'
)
target_group_arn = response['TargetGroups'][0]['TargetGroupArn']

# [c] Register targets in the target group
client.register_targets(
    TargetGroupArn=target_group_arn,
    Targets=[
        {'Id': instances[0].id},
        {'Id': instances[1].id}
    ]
)

# [d] Create a listener
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

print("Load balancer and instances created successfully!")
