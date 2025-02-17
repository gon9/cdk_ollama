#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from aws_cdk import App, Environment
from cdk_ollama.cdk_ollama_stack import OllamaServerCdkStack

# 変更があっても上書きするために override=True を指定する
load_dotenv(override=True)

# インスタンスタイプの読み込み（デフォルトはCPU版）
instance_type = os.getenv("INSTANCE_TYPE", "m5.2xlarge")

# GPUインスタンスの場合はGPU用AMIの環境変数から取得]
is_gpu = os.getenv("IS_GPU", "false")
if is_gpu:
    # インスタンスタイプの読み込み
    # memory 16GB
    instance_type = "g4dn.xlarge"
    gpu_ami = os.getenv("GPU_NVIDIA_AMI_ID")
    if not gpu_ami:
        raise Exception("GPUインスタンスが指定されていますが、GPU_NVIDIA_AMI_IDが環境変数に設定されていません。")
    ami_id = gpu_ami
else:
    # CPUインスタンスの場合は、スタック内で通常のUbuntu 22.04が選択されるようにします
    instance_type = "m5.2xlarge"
    ami_id = os.getenv("CPU_AMI_ID") # ubuntu 22.04

app = App()
OllamaServerCdkStack(
    app, 
    "OllamaServerStack",
    instance_type_str=instance_type,
    ami_id=ami_id,
    env=Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    )
)

app.synth()
