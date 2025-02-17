#!/usr/bin/env python3
import os

import aws_cdk as cdk
import configs.accounts as a
import configs.globalconfig as g
from cdkai_deploy.ai_deploy import AIInfraPipeline



app = cdk.App()

###
##  web account(s) pipelines
###


for env_name in ["dev",  "prod"]:
    if (a.managed_accounts[env_name]["enabled"]):
        AIInfraPipeline(app, env_name+"-ai-pipeline",
            env=cdk.Environment(account=a.devops_account["account"],region=a.devops_account["region"]),
            env_name=env_name,
            deployment_type = a.managed_accounts[env_name]["deployment_type"],
            )

app.synth()
