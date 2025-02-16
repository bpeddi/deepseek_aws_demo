# Install and configure NVIDIA drivers on EC2 Instance

sudo yum update -y
sudo yum install gcc make sudo yum install -y gcc kernel-devel-$(uname -r)
cd ~
aws s3 cp --recursive s3://ec2-linux-nvidia-drivers/latest/ .
chmod +x NVIDIA-Linux-x86_64*.run
mkdir /home/ec2-user/tmp
chmod -R 777 tmp
cd /home/ec2-user 
export TMPDIR=/home/ec2-user/tmp
CC=/usr/bin/gcc10-cc ./NVIDIA-Linux-x86_64*.run --tmpdir=$TMPDIR

# verify the drivers are correctly installed and disable GSP
nvidia-smi -q | head
sudo touch /etc/modprobe.d/nvidia.conf
echo "options nvidia NVreg_EnableGpuFirmware=0" | sudo tee --append /etc/modprobe.d/nvidia.conf

# Install and configure Docker on EC2 Instance

sudo yum update -y
sudo yum install docker -y
sudo  usermod -a -G docker ec2-user
sudo systemctl enable docker.service
sudo systemctl start docker.service

# Once the docker service is started, run the following commands to configure Docker with NVIDIA drivers
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
sudo yum install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Start your LLM models 

docker network create ollama_nw_1

docker run -d --gpus=all --network ollama_nw_1 -v ollama:/root/.ollama -p 11438:11434 --name ollama_1 ollama/ollama 
docker run -d --gpus=all --network ollama_nw_1 -v ollama:/root/.ollama -p 11435:11434 --name ollama_2 ollama/ollama 
docker run -d --gpus=all --network ollama_nw_1 -v ollama:/root/.ollama -p 11436:11434 --name ollama_3 ollama/ollama 
docker run -d --gpus=all --network ollama_nw_1 -v ollama:/root/.ollama -p 11437:11434 --name ollama_4 ollama/ollama 

docker run -d --gpus=all --network ollama_nw_1 -p 3000:8080 -e OLLAMA_BASE_URL="http://ollama_1:11434;http://ollama_1:11435;http://ollama_1:11436;http://ollama_1:11437;http://ollama_1:11438;" -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main
sudo yum install nginx -y

docker exec -it ollama_1 ollama pull llama3.2
docker exec -it ollama_3 ollama pull deepseek-r1:8b
docker exec -it ollama_2 ollama pull deepseek-r1:7b
docker exec -it ollama_4 ollama pull llama3.1:8b




