# cdk_ollama (Python)

このドキュメントは、AWS CDK (Python) を使用して CPU 環境の ollama サーバー用 EC2 インスタンスを構築する手順例です。  
Terraform の GPU 用マニフェストを参考に、CDK による構成を整理しています。
参考: [conikeec/ollama_aws](https://github.com/conikeec/ollama_aws/tree/main)

## 前提条件

- AWS CLI がインストール済み、認証情報が設定済み
- Python 3.8 以上がインストール済み
- 仮想環境（venv, pyenv など）での開発を推奨
- AWS CDK がインストール済み
- キーペアが作成済み

## セットアップ手順

1. **プロジェクトの初期化**

git clone https://github.com/gon9/cdk_ollama.git
cd cdk_ollama

2. **仮想環境の作成**

pyenv local 3.12.4
poetry install

3. cdkスタックのデプロイ
poetry run cdk synth
poetry run cdk deploy

4. デプロイ後の確認
```
# サーバーの起動確認
curl http://<your-instance-public-ip>:11434
# モデル一覧
curl http://<your-instance-public-ip>:11434/api/tags

※ モデルの起動
curl http://<your-instance-public-ip>:11434/api/generate -d '{"model": "llama2", "prompt": "Hello, world!"}'
```


memo
- メモリサイズあげてインスタンス立ち直す
- イマイチuser_data_scriptがうまくいっていない
- 取りあえず動くとこまでもっていきたい
- GPU 用のインスタンスを作成する
