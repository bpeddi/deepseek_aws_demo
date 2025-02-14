
# Deepseek Infrastructure Pipeline - AWS CDK

## Overview

DeepSeek R1 is a large language model developed with a strong focus on reasoning tasks. It excels at problems requiring multi-step analysis and logical thinking. Unlike typical models that rely heavily on Supervised Fine-Tuning (SFT), DeepSeek R1 uses Reinforcement Learning (RL) as its primary training strategy. This emphasis on RL empowers it to figure out solutions with greater independence. <br> <br>


This project provisions a scalable and secure AI infrastructure for deploying the DeepSeek AI model using **AWS CDK (Cloud Development Kit)** with Python. The architecture leverages **Amazon VPC, EC2 Instances, IAM Roles, Security Groups, and S3 Bucket** integration to provide a robust environment for AI model training and inference. This CDK implementation also automates the deployment of Docker containers and efficiently downloads the DeepSeek and Ollama models, alongside Open-WebUI for seamless model inference and interaction.


![Architecture](deepseek_aws.PNG)

## Prerequisites:
- Active AWS account with appropriate permissions to launch EC2 instances and manage related resources.
- Service Quota limit for approved for Running On-Demand Inf instances under Amazon Elastic Compute Cloud (Amazon EC2) with a value of 96 or above.
- A Key Pair created to connect with EC2 instance.
- **AWS CDK** installed (`npm install -g aws-cdk`)
- **AWS CLI** configured (`aws configure`)
- **Python** (>= 3.8)
- **AWS account with required permissions**


## Features

- **VPC Configuration:**
  - Public and private subnets.
  - NAT gateway for outbound internet access.
  - S3 VPC Endpoint for efficient data transfer.
- **Security Group:**
  - SSH (Port 22) access.
  - AI model serving ports (3000, 11434, etc.).
- **IAM Role & Instance Profile:**
  - EC2 assumes IAM Role with **AmazonS3ReadOnlyAccess**.
- **EC2 Instance Configuration:**
  - Uses an **r5a.2xlarge** instance type.
  - Boots with Amazon Linux 2 AMI.
  - Installs Docker and deploys AI models (Ollama, Open-WebUI).
  - Uses key pair authentication.

## Deploying to CPU based EC2 instance 

No changes required ,This code works as is

## Deploying to GPU-powered EC2 instance instance 

### Install and configure NVIDIA drivers on EC2 Instance
If you are planning to use GPU-powered EC2 instance, you will have to change InstanceType below line to g4dn.xlarge in cdkai_deploy/ai_deploy.py
```instance_type=ec2.InstanceType("r5a.2xlarge"),  # Define instance type```

Login to EC2 instance and Run the following commands in the to install the NVIDIA GRID drivers on the g4dn EC2 instance.

```sudo yum update -y
sudo yum install gcc makesudo yum install -y gcc kernel-devel-$(uname -r)
cd ~
aws s3 cp --recursive s3://ec2-linux-nvidia-drivers/latest/ .
chmod +x NVIDIA-Linux-x86_64*.run
mkdir /home/ssm-user/tmp
chmod -R 777 tmp
cd /home/ssm-user 
export TMPDIR=/home/ssm-user/tmp
CC=/usr/bin/gcc10-cc ./NVIDIA-Linux-x86_64*.run --tmpdir=$TMPDIR
nvidia-smi -q | head
sudo touch /etc/modprobe.d/nvidia.conf
echo "options nvidia NVreg_EnableGpuFirmware=0" | sudo tee --append /etc/modprobe.d/nvidia.conf
```



## Deployment Steps

## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/bpeddi/deepseek_aws_demo.git
   cd deepseek_aws_demo/cdkai_deploy
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate   # Mac/Linux
   .venv\Scripts\activate      # Windows
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Bootstrap CDK (if first-time deployment):**
   ```sh
   cdk bootstrap
   ```
5. **Deploy the stack:**
   ```sh
   cdk deploy
   ```


## Cleanup

To remove the resources provisioned:

```sh
cdk destroy
```

## Configuration

Modify the `conigs/accounts.py` or update `AIInfraPipeline` class parameters to customize the deployment.

## Troubleshooting

- Ensure AWS credentials are correctly configured.
- Check **CloudFormation** stack logs for deployment errors.
- Verify security group rules if access issues arise.

## Author

[Bala Peddi]\
[bala.peddi@gmail.com]



Below is a `README.md` file for the provided AWS CDK code. This file explains the purpose, setup, and deployment of the infrastructure defined in the `ai_deploy.py` script.

---

# AWS CDK Infrastructure for AI Deployment

This project uses the AWS Cloud Development Kit (CDK) to define and deploy infrastructure for an AI-based solution. The infrastructure includes a VPC, EC2 instance, security groups, IAM roles, and other AWS resources necessary for deploying and running an AI workload.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Deployment](#deployment)
- [Infrastructure Details](#infrastructure-details)
- [Usage](#usage)
- [Cleanup](#cleanup)
- [Contributing](#contributing)
- [License](#license)

## Overview
The `ai_deploy.py` script defines an AWS CDK stack that provisions the following resources:
- A **VPC** with public and private subnets.
- An **EC2 instance** for running AI workloads.
- **Security groups** to control inbound and outbound traffic.
- **IAM roles** and policies for granting necessary permissions.
- An **S3 bucket** for storing artifacts.

This infrastructure is designed to support AI workloads, such as machine learning inference or model training, by providing a secure and scalable environment.

## Prerequisites
Before deploying the infrastructure, ensure you have the following:
1. An AWS account with appropriate permissions.
2. AWS CLI installed and configured:
   ```bash
   aws configure
   ```
3. Node.js and Python installed.
4. AWS CDK installed:
   ```bash
   npm install -g aws-cdk
   ```

## Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/bpeddi/deepseek_aws_demo.git
   cd deepseek_aws_demo/cdkai_deploy
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Bootstrap the AWS CDK (if not already bootstrapped):
   ```bash
   cdk bootstrap
   ```

## Deployment
To deploy the infrastructure, run the following command:
```bash
cdk deploy
```
This will create the resources defined in the `ai_deploy.py` script.

## Infrastructure Details
### VPC
- A VPC with a CIDR block of `10.0.0.0/24` is created.
- The VPC includes:
  - Public subnets for resources that need internet access.
  - Private subnets for internal resources.
  - A NAT gateway for outbound internet access from private subnets.
  - An S3 gateway endpoint for secure access to S3.

### EC2 Instance
- An EC2 instance of type `g4dn.2xlarge` is provisioned for AI workloads.
- The instance is configured with:
  - A 100 GB GP3 EBS volume.
  - A security group allowing SSH (port 22) and custom ports (3000 and 11434).
  - An IAM role with `AmazonS3ReadOnlyAccess` policy for accessing S3.

### Security Group
- A security group is created to control traffic to the EC2 instance.
- Inbound rules allow:
  - SSH access (port 22) from any IP.
  - Access to ports 3000 and 11434 from any IP.
- Outbound rules allow all traffic.

### IAM Role
- An IAM role is created for the EC2 instance.
- The role has the `AmazonS3ReadOnlyAccess` policy attached, allowing the instance to read from S3.

### S3 Bucket
- An existing S3 bucket is referenced for storing artifacts.

## Usage
Once the infrastructure is deployed, you can:
1. SSH into the EC2 instance:
   ```bash
   ssh -i <your-key-pair>.pem ec2-user@<instance-public-ip>
   ```
2. Deploy your AI workload on the instance.
3. Access the workload via the configured ports (3000 and 11434).

## Cleanup
To avoid incurring charges, destroy the deployed resources when you're done:
```bash
cdk destroy
```

## Contributing
Contributions are welcome! If you'd like to contribute, please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a detailed description of your changes.

## License
This project is licensed under the [License Name] - see the [LICENSE](LICENSE) file for details.

---

### Notes
- Replace placeholders like `[License Name]` and `<your-key-pair>` with actual values.
- If there are additional details or specific instructions for using the AI workload, include them in the **Usage** section.

Let me know if you need further assistance!

