# Lab 3 Networking
## Part1 Configure inbound IP on my VM
### Configure my VM
   ![image](1.1.png)

#### Test the NAT'd port
1.  Install the tasksel package ```sudo apt install tasksel```, and the output is as follows:
   ![image](1.2.png)
2. Install the OpenSSH server package using the tasksel tool ```sudo tasksel install openssh-server``` , and the output is as follows:
   ![image](1.3.png)
3.  Establish an SSH connection ```ssh -p 2222 vic77@127.0.0.1```, and the output is as follows:
   ![image](1.4.png)


## Part2 Boto3  application
In this section, In this section, I use Boto3 to create two EC2 instances in different availability zones and set up an application load balancer to distribute HTTP requests between them.
### The code of the application is as below:
```import boto3

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
```
### Run the code and output is as below:
  ![image](2.1.png)
The group is created in previous version of the application, so I added this Exception Handling to the application:

``` # Check if the specified security group already exists
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
        
```


### Connect to my instances
#### The first instances:
![image](2.2.1.png)
##### Run this command ```ssh -i "21862278-key.pem" root@ec2-3-26-51-226.ap-southest-2.compute.amazonaws.com```, and the outcome is as below: 
![image](2.2.png)


##### Trouble shooting
1. There was an error, so I change the permissions.
![image](2.3.png)


2. I tried SSH command ```ssh -i "21862278-key.pem" root@ec2-3-26-51-226.ap-southest-2.compute.amazonaws.com``` again, there is a remainder let me change the user, so I run ```21862278-key.pem" ubuntu@ec2-3-26-51-226.ap-southest-2.compute.amazonaws.com``` to connect successfully.
![image](2.4.png)

#### Apache 2 Installation
##### Run the command ```sudo apt-get update``` to update the packages, and the outcome:
![image](2.5.png)

##### Run ```sudo apt install apache2``` to install apache2, and the outcome is :
![image](2.6.png) ![image](2.7.png)

##### Trouble Shooting:
1. I still cannot get access the Ip address, so I use ```sudo systemctl status apache2``` to check the status of apache2, and find the errors.
   ![image](2.8.png)
2. Run ```sudo lsof -i:80``` to identify which processes are using port 80 on a system, and use ```sudo systemctl stop nginx``` to stop the processes.
   ![image](2.9.png)
3. ```sudo systemctl restart apache2``` to restart to apache2 ,and then check its status again.
   ![image](2.10.png)
4. The connection is successful now, and I can browse the Ip Address.
   ![image](2.11.png)
   
##### Edit the file /var/www/html/index.html
1. Run ```sudo nano /var/www/html/index.html``` to open the file and add '21862278-ap-southeast-2a' to the file.
![image](2.12.png)

2. Fresh the IP address and we can see the updated website.
![image](2.13.png)

#### Close the connection.
![image](2.14.png)



#### The Second instances
![image](3.1.png)
1. For the second instance, I repeated the steps as the first one.
The original website is like this,![image](3.4.png)



2. Run ```sudo nano /var/www/html/index.html``` to open the file and add '21862278-ap-southeast-2a' to the file,there is a typo, I should add the '21862278-ap-southeast-2b'  .
![image](3.3.png)

3. Fresh the IP address and we can see the updated website.
![image](3.2.png)

4. Close the connection.
![image](3.5.png)



## Part3 Delete the listener, Load balancer, target group and terminate the EC2 instances.

### Delete the listener

![image](4.1.png) ![image](4.2.png)
### Delete the load balancer

![image](4.3.png) ![image](4.4.png)

### Delete the target group
![image](4.5.png) ![image](4.6.png)

### Terminate the instances
![image](4.7.png) ![image](4.8.png) ![image](4.9.png)