import os
from dotenv import load_dotenv

from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    Stack,
)
from constructs import Construct

# .envファイルから環境変数をロード
load_dotenv()

class OllamaServerCpuCdkStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # デフォルト VPC を取得
        vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)

        # EC2 用 IAM ロールの作成
        ollama_role = iam.Role(
            self,
            "OllamaRole",
            role_name="ollama-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="EC2 instance role for ollama server",
        )

        # S3 フルアクセスのマネージドポリシーをアタッチ
        ollama_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )

        # EC2 インスタンスの作成 (メモリサイズ20GB以上のインスタンス例: m5.2xlargeは約32GBのメモリを持ちます)
        instance = ec2.Instance(
            self,
            "OllamaInstance",
            instance_name="ollama-server",
            instance_type=ec2.InstanceType("m5.2xlarge"),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            ),
            vpc=vpc,
            role=ollama_role,
            # キーペア名を.envから読み込み。環境変数が設定されていない場合は"default-key-pair"となる
            key_name=os.environ.get("KEY_PAIR_NAME", "default-key-pair"),
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=100,
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                    ),
                )
            ],
        )

        # ユーザーデータスクリプトの設定
        user_data_script = """#!/bin/bash
# SSH ポートを 10022 に変更
sudo sed -i 's/^#Port 22/Port 10022/' /etc/ssh/sshd_config
sudo sed -i 's/^Port 22/Port 10022/' /etc/ssh/sshd_config
sudo service sshd restart

sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
# CPU 用の ollama サーバーコンテナの起動
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama --restart always ollama/ollama:latest
# コンテナの起動を待機（必要に応じて調整）
sleep 15
# 各モデルをプル（必要に応じて実行）
docker exec ollama ollama pull deepseek-llm
docker exec ollama ollama pull llama2
docker exec ollama ollama pull deepseek-coder:6.7b
docker exec ollama ollama pull codellama:7b
# モデルの起動（例: llama2 の起動）
docker exec ollama ollama run llama2
# ollama-webui コンテナの起動例
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v ollama-webui:/app/backend/data --name ollama-webui --restart always ghcr.io/ollama-webui/ollama-webui:main
"""
        instance.add_user_data(user_data_script)

        # ポート 11434 へのインバウンド接続を許可
        instance.connections.allow_from_any_ipv4(
            ec2.Port.tcp(11434),
            "Allow inbound traffic for Ollama server port 11434"
        )

        # ポート 22 (SSH) へのインバウンド接続を許可
        instance.connections.allow_from_any_ipv4(
            ec2.Port.tcp(10022),
            "Allow SSH access"
        )
