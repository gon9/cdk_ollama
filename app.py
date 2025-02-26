#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from aws_cdk import App, Environment
from cdk_ollama.cdk_ollama_stack import OllamaServerCdkStack

# .env ファイルから環境変数を読み込む
load_dotenv()

# 環境変数から値を取得
use_gpu = os.getenv('USE_GPU', 'false').lower() == 'true'

# インスタンスタイプとAMI IDを選択
if use_gpu:
    ami_id = os.getenv('GPU_AMI_ID')
    instance_type_str = os.getenv('GPU_INSTANCE_TYPE')
else:
    ami_id = os.getenv('CPU_AMI_ID')
    instance_type_str = os.getenv('CPU_INSTANCE_TYPE')

# 値が設定されていない場合のエラーハンドリング
if not instance_type_str or not ami_id:
    raise ValueError("INSTANCE_TYPE or AMI_ID is not set properly in the .env file")

key_pair_name = os.getenv("KEY_PAIR_NAME", "default-key-pair")
peer_ip = os.getenv("PEER_IP", "0.0.0.0")
s3_bucket_name = os.getenv("S3_BUCKET_NAME", "defauld_s3_bucket_name")
s3_bucket_arn = os.getenv("S3_BUCKET_ARN", "defauld_s3_bucket_arn")
s3_bucket_arn_wildcard = os.getenv("S3_BUCKET_ARN_WILDCARD", "defauld_s3_bucket_arn_wildcard")

app = App()
OllamaServerCdkStack(
    app,
    "OllamaServerStack",
    use_gpu=use_gpu,
    instance_type_str=instance_type_str,
    ami_id=ami_id,
    key_pair_name=key_pair_name,
    peer_ip=peer_ip,
    s3_bucket_name=s3_bucket_name,
    s3_bucket_arn=s3_bucket_arn,
    s3_bucket_arn_wildcard=s3_bucket_arn_wildcard,
    env=Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    )
)

app.synth()