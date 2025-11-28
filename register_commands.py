#!/usr/bin/env python3
"""
Discordスラッシュコマンドを登録するスクリプト
使用方法:
    export DISCORD_BOT_TOKEN="your_bot_token"
    export DISCORD_APPLICATION_ID="your_application_id"
    python3 register_commands.py

オプション:
    --guild-id: 特定のサーバー（ギルド）にのみコマンドを登録（開発用）
    指定しない場合はグローバルコマンドとして登録（反映まで最大1時間かかる場合があります）
"""

import os
import sys
import json
import requests
import argparse

# Discord API エンドポイント
DISCORD_API_BASE = "https://discord.com/api/v10"

def register_commands(bot_token: str, application_id: str, guild_id: str = None):
    """スラッシュコマンドをDiscordに登録"""

    # コマンド定義
    commands = [
        {
            "name": "start",
            "description": "Palworldサーバーを起動します",
            "type": 1  # CHAT_INPUT
        },
        {
            "name": "stop",
            "description": "Palworldサーバーを停止します",
            "type": 1  # CHAT_INPUT
        },
        {
            "name": "status",
            "description": "Palworldサーバーの状態を確認します",
            "type": 1  # CHAT_INPUT
        }
    ]

    # エンドポイントの決定
    if guild_id:
        # ギルドコマンド（特定のサーバーにのみ登録、即座に反映）
        url = f"{DISCORD_API_BASE}/applications/{application_id}/guilds/{guild_id}/commands"
        print(f"📝 ギルドコマンドとして登録します（Guild ID: {guild_id}）")
    else:
        # グローバルコマンド（全サーバーに登録、反映まで最大1時間）
        url = f"{DISCORD_API_BASE}/applications/{application_id}/commands"
        print(f"🌍 グローバルコマンドとして登録します")

    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }

    print(f"\n登録するコマンド:")
    for cmd in commands:
        print(f"  - /{cmd['name']}: {cmd['description']}")
    print()

    # 各コマンドを登録
    success_count = 0
    for command in commands:
        try:
            response = requests.post(url, headers=headers, json=command)

            if response.status_code == 200 or response.status_code == 201:
                print(f"✅ /{command['name']} を登録しました")
                success_count += 1
            else:
                print(f"❌ /{command['name']} の登録に失敗しました")
                print(f"   ステータスコード: {response.status_code}")
                print(f"   レスポンス: {response.text}")
        except Exception as e:
            print(f"❌ /{command['name']} の登録中にエラーが発生しました: {e}")

    print(f"\n{'='*50}")
    if success_count == len(commands):
        print(f"✅ すべてのコマンドを登録しました！")
        if not guild_id:
            print("⚠️  グローバルコマンドは反映まで最大1時間かかる場合があります")
    else:
        print(f"⚠️  {success_count}/{len(commands)} 個のコマンドを登録しました")
        sys.exit(1)

def list_commands(bot_token: str, application_id: str, guild_id: str = None):
    """登録済みのコマンド一覧を表示"""
    if guild_id:
        url = f"{DISCORD_API_BASE}/applications/{application_id}/guilds/{guild_id}/commands"
    else:
        url = f"{DISCORD_API_BASE}/applications/{application_id}/commands"

    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            commands = response.json()
            if commands:
                print(f"登録済みコマンド ({len(commands)}個):")
                for cmd in commands:
                    print(f"  - /{cmd['name']}: {cmd.get('description', '説明なし')} (ID: {cmd['id']})")
            else:
                print("登録済みコマンドはありません")
        else:
            print(f"❌ コマンド一覧の取得に失敗しました: {response.status_code}")
            print(f"   レスポンス: {response.text}")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def delete_command(bot_token: str, application_id: str, command_id: str, guild_id: str = None):
    """コマンドを削除"""
    if guild_id:
        url = f"{DISCORD_API_BASE}/applications/{application_id}/guilds/{guild_id}/commands/{command_id}"
    else:
        url = f"{DISCORD_API_BASE}/applications/{application_id}/commands/{command_id}"

    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            print(f"✅ コマンド (ID: {command_id}) を削除しました")
        else:
            print(f"❌ コマンドの削除に失敗しました: {response.status_code}")
            print(f"   レスポンス: {response.text}")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def main():
    parser = argparse.ArgumentParser(description="Discordスラッシュコマンドを管理")
    parser.add_argument("--guild-id", help="ギルドID（指定するとそのサーバーにのみ登録）")
    parser.add_argument("--list", action="store_true", help="登録済みコマンド一覧を表示")
    parser.add_argument("--delete", help="コマンドIDを指定して削除")

    args = parser.parse_args()

    # 環境変数から認証情報を取得
    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    application_id = os.environ.get("DISCORD_APPLICATION_ID")

    if not bot_token:
        print("❌ エラー: DISCORD_BOT_TOKEN 環境変数が設定されていません")
        print("   使用方法: export DISCORD_BOT_TOKEN='your_bot_token'")
        sys.exit(1)

    if not application_id:
        print("❌ エラー: DISCORD_APPLICATION_ID 環境変数が設定されていません")
        print("   使用方法: export DISCORD_APPLICATION_ID='your_application_id'")
        sys.exit(1)

    if args.list:
        list_commands(bot_token, application_id, args.guild_id)
    elif args.delete:
        delete_command(bot_token, application_id, args.delete, args.guild_id)
    else:
        register_commands(bot_token, application_id, args.guild_id)

if __name__ == "__main__":
    main()

