#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from aws_cdk import App, Environment
from cdk_ollama.cdk_ollama_stack import OllamaServerCpuCdkStack

load_dotenv()

app = App()
OllamaServerCpuCdkStack(app, "OllamaServerCpuCdkStack",
    env=Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    )
)

app.synth()
