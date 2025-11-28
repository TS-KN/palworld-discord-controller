# Palworld Discord Controller

PalworldサーバーをDiscordから制御するためのLambda関数とDiscordボットです。

## 機能

- `/start` - Palworldサーバー（EC2）を起動
- `/stop` - Palworldサーバー（EC2）を停止
- `/status` - Palworldサーバーの状態を確認

## セットアップ

### 1. Discordボットの作成とサーバーへの追加

1. [Discord Developer Portal](https://discord.com/developers/applications)でアプリケーションを作成
2. Botセクションでボットを作成し、トークンを取得
3. OAuth2 > URL Generatorで、`bot`と`applications.commands`スコープを選択
4. 生成されたURLでボットをサーバーに追加

### 2. スラッシュコマンドの登録

スラッシュコマンドをDiscordに登録します。

#### 必要な情報
- `DISCORD_BOT_TOKEN`: ボットのトークン
- `DISCORD_APPLICATION_ID`: アプリケーションID（General Informationから取得）

#### グローバルコマンドとして登録（推奨）

全サーバーで使用可能になりますが、反映まで最大1時間かかる場合があります。

```bash
export DISCORD_BOT_TOKEN="your_bot_token"
export DISCORD_APPLICATION_ID="your_application_id"
python3 register_commands.py
```

#### ギルドコマンドとして登録（開発用）

特定のサーバーにのみ登録され、即座に反映されます。開発やテストに便利です。

```bash
export DISCORD_BOT_TOKEN="your_bot_token"
export DISCORD_APPLICATION_ID="your_application_id"
python3 register_commands.py --guild-id "your_guild_id"
```

#### その他のコマンド

```bash
# 登録済みコマンド一覧を表示
python3 register_commands.py --list

# ギルドコマンド一覧を表示
python3 register_commands.py --list --guild-id "your_guild_id"

# コマンドを削除
python3 register_commands.py --delete "command_id"
```

### 3. 必要なライブラリ

スラッシュコマンド登録スクリプトを実行するには、`requests`ライブラリが必要です。

```bash
pip install requests
```

### 4. Lambda関数のデプロイ

Lambda関数はGitHub Actionsで自動デプロイされます。`main`ブランチへのマージ時に自動的にデプロイされます。

## 環境変数

Lambda関数には以下の環境変数が必要です：

- `INSTANCE_ID`: 制御するEC2インスタンスのID
- `DISCORD_PUBLIC_KEY`: Discordアプリケーションの公開鍵（Public Key）

## 使用方法

Discordサーバーで以下のコマンドを使用できます：

- `/start` - サーバーを起動
- `/stop` - サーバーを停止
- `/status` - サーバーの状態とIPアドレスを確認
