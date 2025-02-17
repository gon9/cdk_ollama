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

class OllamaServerCdkStack(Stack):
    def __init__(self, scope: Construct, id: str, *, instance_type_str: str = "m5.2xlarge", ami_id: str = None, **kwargs) -> None:
        """
        :param instance_type_str: CPU版の場合は "m5.2xlarge"、GPU版の場合は例えば "g4dn.xlarge" など、用途に合わせて指定可能
        """
        super().__init__(scope, id, **kwargs)

        # デフォルト VPC を取得
        vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)

        # EC2 用 IAM ロールの作成（必要最小限の権限に調整することを推奨）
        ollama_role = iam.Role(
            self,
            "OllamaRole",
            role_name="ollama-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="EC2 instance role for Ollama server",
        )

        # 例: 特定のS3バケット「your-bucket-name」に対してのアクセス権限のみを付与するポリシードキュメント
        s3_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "s3:GetObject",
                        "s3:ListBucket",
                    ],
                    resources=[
                        os.environ.get("S3_BUCKET_ARN"),
                        os.environ.get("S3_BUCKET_ARN_WILDCARD"),
                    ],
                )
            ]
        )

        s3_policy = iam.Policy(self, "S3AccessPolicy", document=s3_policy_document)
        ollama_role.attach_inline_policy(s3_policy)

        # セキュリティグループの作成
        ollama_sg = ec2.SecurityGroup(
            self,
            "OllamaSecurityGroup",
            vpc=vpc,
            security_group_name="ollama-sg",
            description="Security group for Ollama server",
            allow_all_outbound=True,
        )

        # インバウンドルールの追加
        inbound_ports = [
            (11434, "Ollama server port"),
            (10022, "SSH port"),
            (8080, "Web UI port")
        ]
        peer_ip = os.getenv("PEER_IP", "106.72.144.33/32")
        for port, description in inbound_ports:
            ollama_sg.add_ingress_rule(
                peer=ec2.Peer.ipv4(peer_ip),
                connection=ec2.Port.tcp(port),
                description=description,
            )

        # EC2 インスタンスの作成
        instance = ec2.Instance(
            self,
            "OllamaInstance",
            instance_name="ollama-server",
            instance_type=ec2.InstanceType(instance_type_str),
            machine_image=ec2.MachineImage.generic_linux({
                "us-east-1": ami_id
            }) if ami_id else ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            ),
            vpc=vpc,
            role=ollama_role,
            security_group=ollama_sg,  # 作成したセキュリティグループを指定
            # キーペア名を.envから読み込み。環境変数が設定されていない場合は"default-key-pair"となる
            key_name=os.environ.get("KEY_PAIR_NAME", "default-key-pair"),
            # ブロックデバイスの設定
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

        # Docker実行コマンドの設定
        if os.getenv("IS_GPU") == "true":
            docker_command = (
                "docker run -d --gpus all "
                "-v ollama:/root/.ollama "
                "-p 11434:11434 "
                "--name ollama "
                "--restart always "
                "ollama/ollama:latest"
            )
        else:
            docker_command = (
                "docker run -d "
                "-v ollama:/root/.ollama "
                "-p 11434:11434 "
                "--name ollama "
                "--restart always "
                "ollama/ollama:latest"
            )

        # ユーザーデータスクリプトの作成
        user_data = ec2.UserData.for_linux(shebang="#!/bin/bash")
        user_data.add_commands(
            "# パッケージの更新",
            "sudo apt update -y",
            "sudo apt upgrade -y",
            "",
            "# Docker のインストールと起動",
            "sudo apt install -y docker.io",
            "sudo systemctl start docker",
            "sudo systemctl enable docker",
            "sudo usermod -aG docker ubuntu",
            "",
            "# SSH ポートを 10022 に変更",
            "sudo sed -i 's/^#Port 22/Port 10022/' /etc/ssh/sshd_config",
            "sudo sed -i 's/^Port 22/Port 10022/' /etc/ssh/sshd_config",
            "sudo systemctl restart ssh",
            "",
            "# Docker コンテナの起動",
            docker_command,
            "",
            "# コンテナ起動待機（必要に応じて調整）",
            "sleep 15",
            "",
            "# 各モデルを起動(pullは不要)",
            "docker exec ollama ollama run deepseek-r1:8b",
            "docker exec ollama ollama run qwen2.5-coder:1.5b",
            "",
            "# ollama-webui コンテナの起動",
            "docker run -d -p 3000:8080 --env WEBUI_AUTH=False --add-host=host.docker.internal:host-gateway -v ollama-webui:/app/backend/data --name ollama-webui --restart always ghcr.io/ollama-webui/ollama-webui:main"
        )

        instance.add_user_data(user_data.render())
        # インバウンドルールの設定
        inbound_ports = [
            (11434, "Ollama server port"),
            (10022, "SSH port"),
            (8080, "Web UI port")
        ]
        peer_ip = os.getenv("PEER_IP", "106.72.144.33/32")
        for port, description in inbound_ports:
            instance.connections.allow_from(
                ec2.Peer.ipv4(peer_ip),
                ec2.Port.tcp(port),
                description
            )

