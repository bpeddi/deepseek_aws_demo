from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3,
    CfnOutput,
    Stack,
)
from constructs import Construct
from cdk_ec2_spot_simple import SpotInstance
import os
import json


class AIInfraPipeline(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, env=kwargs["env"])

        # Extracting parameters from kwargs
        deployment_type = kwargs["deployment_type"]
        env_name = kwargs["env_name"]

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

        # ==================================================
        # =============== Security Group ===================
        # ==================================================

        # Create a Security Group for the EC2 instance
        security_group = ec2.SecurityGroup(
            self,
            "DeepSeekSecurityGroup",
            vpc=vpc,
            security_group_name="deepSeekSecurityGroup",
            description="Security group for deepSeek",
            allow_all_outbound=True,  # Allows all outbound traffic
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
            assumed_by=iam.ServicePrincipal(
                "ec2.amazonaws.com"
            ),  # Allows EC2 to assume the role
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
        key_pair = ec2.KeyPair.from_key_pair_attributes(
            self,
            "KeyPair",
            key_pair_name="simplytrack",
        )

        # Define Amazon Linux 2 AMI
        ami = ec2.MachineImage.latest_amazon_linux2()

        # Define user data script for instance initialization
        user_data = ec2.UserData.for_linux()

        print(deployment_type)
        if deployment_type == "gpu":

            user_data.add_commands(
                "sudo yum install -y gcc kernel-devel-$(uname -r)",
                "aws s3 cp --recursive s3://ec2-linux-nvidia-drivers/latest/ .",
                "sudo chmod +x ./NVIDIA-Linux-x86_64*.run",
                "sudo /bin/sh ./NVIDIA-Linux-x86_64*.run --tmpdir . --silent",
                "sudo touch /etc/modprobe.d/nvidia.conf",
                f'echo "options nvidia NVreg_EnableGpuFirmware=0" | sudo tee --append /etc/modprobe.d/nvidia.conf',
                "sudo yum install -y docker",
                "sudo usermod -a -G docker ec2-user",
                "sudo systemctl enable docker.service",
                "sudo systemctl start docker.service",
                "curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo",
                "sudo yum install -y nvidia-container-toolkit",
                "sudo nvidia-ctk runtime configure --runtime=docker",
                "sudo systemctl restart docker",
                # Create an Ollama containers,Pull the models in their respective containers,Create the Open WebUI container to serve as the front-end:
                "docker network create ai-network",
                "docker run -d --gpus=all --network ai-network --name ollama-llama3 -v ollama-llama3:/root/.ollama -p 11434:11434 ollama/ollama",
                "docker run -d --gpus=all  --network ai-network --name ollama-deepseek -v ollama-deepseek:/root/.ollama -p 11435:11434 ollama/ollama",
                "sleep 20",
                "docker exec  ollama-llama3 ollama pull llama3.2",
                "docker exec  ollama-deepseek ollama pull deepseek-r1:7b",
                "docker run -d --gpus=all --network ai-network  -p 3000:8080 -e OLLAMA_BASE_URLS='http://ollama-llama3:11434;http://ollama-deepseek:11434' -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main",
                # docker exec -it ollama_2 ollama pull llama3.2
            )

        else:
            user_data.add_commands(
                "sudo yum update -y",
                "sudo amazon-linux-extras enable docker",
                "sudo yum install -y docker",
                "sudo systemctl start docker",
                "sudo systemctl enable docker",
                "sudo usermod -aG docker ec2-user",
                # Create an Ollama containers,Pull the models in their respective containers,Create the Open WebUI container to serve as the front-end:
                "docker network create ai-network",
                "docker run -d --network ai-network --name ollama-llama3 -v ollama-llama3:/root/.ollama -p 11434:11434 ollama/ollama",
                "docker run -d  --network ai-network --name ollama-deepseek -v ollama-deepseek:/root/.ollama -p 11435:11434 ollama/ollama",
                "docker exec  ollama-llama3 ollama pull llama3.2",
                "docker exec  ollama-deepseek ollama pull deepseek-r1:7b",
                "docker run -d --network ai-network  -p 3000:8080 -e OLLAMA_BASE_URLS='http://ollama-llama3:11434;http://ollama-deepseek:11434' -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main",
                "docker exec  ollama-llama3 ollama pull llama3.2",
                "docker exec  ollama-deepseek ollama pull deepseek-r1:7b",
                # docker exec -it ollama_2 ollama pull llama3.2
            )

        # ==================================================
        # ============== EC2 Instance ======================
        # ==================================================

        # # Create an EC2 instance
        # private_instance = ec2.Instance(
        #     self,
        #     "DeepSeekInstance",
        #     # instance_type=ec2.InstanceType("g4dn.2xlarge"),  # Define instance type
        #     instance_type=ec2.InstanceType("g4dn.2xlarge"),  # Define instance type
        #     machine_image=ami,
        #     vpc=vpc,
        #     security_group=security_group,
        #     key_pair=key_pair,
        #     role=role,
        #     user_data=user_data,  # Attach user data script
        #     block_devices=[
        #         ec2.BlockDevice(
        #             device_name="/dev/xvda",
        #             volume=ec2.BlockDeviceVolume.ebs(
        #                 volume_size=100,  # 100 GB EBS volume
        #                 volume_type=ec2.EbsDeviceVolumeType.GP3,
        #             ),
        #         )
        #     ],
        #     vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        # )  # Deploy in public subnet

        # Advanced usage
        spot_instance = SpotInstance(
            self,
            "SpotDeepSeekInstance",
            # Required properties of "ec2.Instance"
            vpc=vpc,
            instance_type=ec2.InstanceType("g4dn.xlarge"),  # Define instance type
            #instance_type=ec2.InstanceType("r5a.2xlarge"),  # Define instance type
            machine_image=ami,
            security_group=security_group,
            key_name="simplytrack",
            role=role,
            user_data=user_data,  # Attach user data script
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=100,  # 100 GB EBS volume
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                    ),
                )
            ],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            # SpotInstance specific property
            spot_options=ec2.LaunchTemplateSpotOptions(
                interruption_behavior=ec2.SpotInstanceInterruption.STOP,
                request_type=ec2.SpotRequestType.PERSISTENT,
                max_price=0.20,
            ),
        )

        # f"echo 'server {{ listen 80; location / {{ proxy_pass http://{private_instance.instance_private_ip}:3000; }} }}' | sudo tee /etc/nginx/conf.d/reverse-proxy.conf",
        user_data = ec2.UserData.for_linux()
        # f"echo 'server {{ listen 80; location / {{ proxy_pass http://{private_instance.instance_private_ip}:3000; }} }}' | sudo tee /etc/nginx/conf.d/reverse-proxy.conf",
        # user_data.add_commands(
        #     "sudo yum update -y",
        #     "sudo amazon-linux-extras install nginx1 -y",
        #     "sudo systemctl start nginx",
        #     "sudo systemctl enable nginx",
        #     f"echo 'server {{ listen 80; location / {{ proxy_pass http://{spot_instance.instance_private_ip}:3000;proxy_http_version 1.1;proxy_set_header Upgrade $http_upgrade;proxy_set_header Connection "Upgrade";proxy_set_header Host $host;proxy_set_header X-Real-IP $remote_addr;proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;proxy_set_header X-Forwarded-Proto $scheme; }} }}' | sudo tee /etc/nginx/conf.d/reverse-proxy.conf",
        #     "sudo nginx -s reload",
        # )

        user_data.add_commands(
            "sudo yum update -y",
            "sudo amazon-linux-extras install nginx1 -y",
            "sudo systemctl start nginx",
            "sudo systemctl enable nginx",
            f"""
            echo '
            server {{
                listen 80;
                location / {{
                    proxy_pass http://{spot_instance.instance_private_ip}:3000;
                    proxy_http_version 1.1;
                    proxy_set_header Upgrade $http_upgrade;
                    proxy_set_header Connection "Upgrade";
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                    proxy_set_header X-Forwarded-Proto $scheme;
                }}
            }} ' | sudo tee /etc/nginx/conf.d/reverse-proxy.conf 
            """,
            "sudo nginx -s reload",
        )


        # EC2 instance in public subnet with Nginx
        public_instance = ec2.Instance(
            self,
            "PublicInstance",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            vpc=vpc,
            key_pair=key_pair,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            user_data=user_data,
        )

        public_instance.connections.allow_from_any_ipv4(ec2.Port.tcp(80))
        public_instance.connections.allow_from_any_ipv4(ec2.Port.tcp(22))

        CfnOutput(self, "NginxPublicIP", value=public_instance.instance_public_ip)
