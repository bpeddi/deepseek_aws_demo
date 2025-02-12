from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3,
    CfnOutput,
    Stack,
)
from constructs import Construct
import os
import json

class AIInfraPipeline(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, env=kwargs["env"])

        # Extracting parameters from kwargs
        env_name = kwargs["env_name"]
        artifacts_bucket = kwargs["artifacts_bucket"]

        # ==================================================
        # ==================== VPC =========================
        # ==================================================

        # Define subnet configurations
        public_subnet = ec2.SubnetConfiguration(
            name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=28
        )
        private_subnet = ec2.SubnetConfiguration(
            name="Private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=28
        )

        # Create a Virtual Private Cloud (VPC)
        vpc = ec2.Vpc(
            scope=self,
            id="VPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/24"),  # Define the CIDR block
            max_azs=2,  # Maximum availability zones
            nat_gateway_provider=ec2.NatProvider.gateway(),  # Define NAT Gateway
            nat_gateways=1,  # Number of NAT Gateways
            subnet_configuration=[public_subnet, private_subnet],
        )
        
        # Add an S3 endpoint to the VPC to enable private S3 access
        vpc.add_gateway_endpoint(
            "S3Endpoint", service=ec2.GatewayVpcEndpointAwsService.S3
        )

        # Access an existing S3 bucket
        existing_bucket = s3.Bucket.from_bucket_name(
            self, "ExistingBucket", artifacts_bucket
        )

        # ==================================================
        # =============== Security Group ===================
        # ==================================================

        # Create a Security Group for the EC2 instance
        security_group = ec2.SecurityGroup(
            self, "DeepSeekSecurityGroup",
            vpc=vpc,
            security_group_name="deepSeekSecurityGroup",
            description="Security group for deepSeek",
            allow_all_outbound=True  # Allows all outbound traffic
        )

        # Add inbound rules to allow SSH and application traffic
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH access"
        )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(3000), "Allow access to port 3000"
        )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(11434), "Allow access to port 11434"
        )

        # ==================================================
        # ================= IAM Role =======================
        # ==================================================

        # Create an IAM Role for the EC2 instance
        role = iam.Role(
            self,
            "deepSeekRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),  # Allows EC2 to assume the role
        )
        
        # Attach an S3 read-only policy to the IAM Role
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
        )
        
        # Create an Instance Profile and associate the IAM Role
        instance_profile = iam.CfnInstanceProfile(
            self,
            "deepSeekInstanceProfile",
            roles=[role.role_name],  # Associate the IAM Role with the Instance Profile
            instance_profile_name="deepSeekProfile",  # Optional: Name the Instance Profile
        )

        # ==================================================
        # ============= Key Pair and User Data ============
        # ==================================================

        # Use an existing Key Pair
        key_pair = ec2.KeyPair.from_key_pair_attributes(self, "KeyPair",
                                 key_pair_name="simplytrack",
        )

        # Define Amazon Linux 2 AMI
        ami = ec2.MachineImage.latest_amazon_linux2() 

        # Define user data script for instance initialization
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "sudo yum update -y",
            "sudo amazon-linux-extras enable docker",
            "sudo yum install -y docker",
            "sudo systemctl start docker",
            "sudo systemctl enable docker",
            "sudo usermod -aG docker ec2-user",
            "docker network create ollama_nw_1",
            "docker run -d --network ollama_nw_1 -v ollama:/root/.ollama -p 11435:11434 --name ollama_1 ollama/ollama",
            "docker run -d --network ollama_nw_1 -v ollama:/root/.ollama -p 11436:11434 --name ollama_2 ollama/ollama",
            "docker run -d --network ollama_nw_1 -p 3000:8080 -e OLLAMA_BASE_URL='http://ollama_1:11434;http://ollama_1:11435;http://ollama_1:11436' -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main",
            "docker exec -it ollama_1 ollama pull deepseek-r1:7b",
            "docker exec -it ollama_2 ollama pull llama3.2"
        )

        # ==================================================
        # ============== EC2 Instance ======================
        # ==================================================

        # Create an EC2 instance
        instance = ec2.Instance(
            self, "DeepSeekInstance",
            instance_type=ec2.InstanceType("r5a.2xlarge"),  # Define instance type
            machine_image=ami,
            vpc=vpc,
            security_group=security_group,
            key_pair=key_pair,
            role=role,
            user_data=user_data,  # Attach user data script
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=100,  # 100 GB EBS volume
                        volume_type=ec2.EbsDeviceVolumeType.GP3
                    )
                )
            ],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)  # Deploy in public subnet
        )
