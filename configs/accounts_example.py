
from configs.globalconfig import default_region

## Devops Account
devops_account = {"account": "xxxxxxxx", "region": default_region}

## CI/CD managed Accounts
managed_accounts = {
    "dev": {
        "enabled": True,
        "deployment_type" : "gpu",
        "account": "xxxxxxxx",
        "region": default_region,
        "vpc_id": "vpc-c50f3bbf",
        "private_subnets": ["subnet-xxxxxxxx", "subnet-xxxxxxxx"],
        "artifacts_bucket": "aws-xxxxxxxx-devops-artifacts-bucket",
    },
    "prod": {
        "enabled": True,
        "deployment_type" : "gpu",
        "account": "xxxxxxxx",
        "region": default_region,
        "vpc_id": "vpc-xxxxxxxx",
        "private_subnets": ["subnet-xxxxxxxx", "subnet-xxxxxxxx"],
        "artifacts_bucket": "aws-xxxxxxxx-prod-devops-artifacts-bucket",
    },
}

