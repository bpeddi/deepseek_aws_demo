from configs.globalconfig import default_region


## Devops Account
devops_account = {"account": "xxxxxxxx", "region": default_region}

## CI/CD managed Accounts
managed_accounts = {
    "dev": {
        "enabled": True,
        "account": "xxxxxxxx",
        "region": default_region,
        "vpc_id": "vpc-xxxxxxxx",
        "private_subnets": ["subnet-xxxxxxxx", "subnet-xxxxxxxx"],
        "artifacts_bucket": "aws-vamsi-devops-artifacts-bucket",
    },
    "prod": {
        "enabled": True,
        "account": "xxxxxxxx",
        "region": default_region,
        "vpc_id": "vpc-xxxxxxxx",
        "private_subnets": ["subnet-xxxxxxxx", "subnet-xxxxxxxx"],
        "artifacts_bucket": "aws-vamsi-prod-devops-artifacts-bucket",
    },
}
