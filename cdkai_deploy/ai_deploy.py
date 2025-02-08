from aws_cdk import (
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    aws_codedeploy as codedeploy,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as pipelineactions,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_elasticloadbalancingv2 as elb,
    aws_iam as iam,
    aws_s3 as s3,
    CfnOutput,
    Stack,
    SecretValue,
)
from constructs import Construct
import os
import json




class DockerInfraPipeline(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, env=kwargs["env"])

        # Extracting parameters from kwargs
        target_account = kwargs["target_account"]
        target_region = kwargs["target_region"]
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

        # Create VPC
        vpc = ec2.Vpc(
            scope=self,
            id="VPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/24"),
            max_azs=2,
            nat_gateway_provider=ec2.NatProvider.gateway(),
            nat_gateways=1,
            subnet_configuration=[public_subnet, private_subnet],
        )
        vpc.add_gateway_endpoint(
            "S3Endpoint", service=ec2.GatewayVpcEndpointAwsService.S3
        )

        # Access existing S3 bucket
        existing_bucket = s3.Bucket.from_bucket_name(
            self, "ExistingBucket", artifacts_bucket
        )


        # Create a Security Group
        security_group = ec2.SecurityGroup(
            self, "DeepSeekSecurityGroup",
            vpc=vpc,
            security_group_name="deepSeekSecurityGroup",
            description="Security group for deepSeek",
            allow_all_outbound=True  # Allows all outbound traffic
        )

        # Add Ingress Rules (Allow inbound traffic)
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH access"
        )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(3000), "Allow access to port 3000"
        )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(11434), "Allow access to port 11434"
        )

        # Add Egress Rule (Allow all outbound traffic)
        security_group.add_egress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.all_traffic(), "Allow all outbound traffic"
        )

        
        # ==================================================
        # ================= IAM Role =======================
        # ==================================================



        # Create an IAM Role
        role = iam.Role(
            self,
            "deepSeekRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),  # Use ServicePrincipal for the Principal
        )
        # Attach S3 read-only policy to the IAM Role
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
        )
        
        # Instance Profile containing the IAM Role
        # instance_profile = iam.InstanceProfile(
        #     "deepSeekProfile", name="deepseek-profile", role=role.name
        # )

                # Create an Instance Profile and associate the IAM Role
        instance_profile = iam.CfnInstanceProfile(
            self,
            "deepSeekInstanceProfile",
            roles=[role.role_name],  # Associate the IAM Role with the Instance Profile
            instance_profile_name="deepSeekProfile",  # Optional: Name the Instance Profile
        )


         # Lookup the latest Amazon Linux 2 AMI based on filters
        # ami = ec2.MachineImage.lookup(
        #     name="amzn2-ami-hvm-2.0.*-x86_64-gp2",  # Filter by name
        #     owners=["137112412989"],  # Amazon's owner ID
        # )       
        # Create EC2 Instance


        key_pair = ec2.KeyPair.from_key_pair_attributes(self, "KeyPair",
                                 key_pair_name="simplytrack",
        )
   
        
        ami = ec2.MachineImage.latest_amazon_linux2() 
        instance = ec2.Instance(
            self, "DeepSeekInstance",
            instance_type=ec2.InstanceType("g4dn.xlarge"),
            # instance_type=ec2.InstanceType("r5.xlarge"),
            machine_image=ami,
            vpc=vpc,
            security_group=security_group,
            # key_name="simplytrack",  # Replace with actual key pair
            key_pair = key_pair,
            role=role,
            # user_data=ec2.UserData.custom(user_data),
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=100,  # 100 GB
                        volume_type=ec2.EbsDeviceVolumeType.GP3
                    )
                )
            ],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
            # vpc_subnets=ec2.SubnetSelection(subnets=[public_subnet])  # Assign to specific subnet
        )
       