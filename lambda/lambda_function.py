import json
import boto3
import os

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

ec2 = boto3.client('ec2')
INSTANCE_ID = os.environ['INSTANCE_ID']
PUBLIC_KEY = os.environ['DISCORD_PUBLIC_KEY']


def lambda_handler(event, context):
    # セキュリティヘッダーの検証（リクエスト処理の前に実行）
    if not _verify_signature(event):
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Unauthorized"})
        }

    try:
        # event['body']が文字列の場合とdictの場合の両方に対応
        body_str = event.get('body', '{}')
        if isinstance(body_str, str):
            if not body_str or body_str.strip() == '':
                body = {}
            else:
                body = json.loads(body_str)
        else:
            body = body_str if body_str else {}
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error parsing body: {e}, event: {event}")
        # Discordの検証リクエストの場合、空のbodyでもPINGとして扱う
        body = {}

    # DiscordのPINGリクエスト（検証用）に対応
    request_type = body.get("type")
    print(f"Request type: {request_type}, body: {json.dumps(body)}")

    if request_type == 1:  # PING
        print("Responding to PING request")
        response_body = json.dumps({"type": 1})
        print(f"Response: {response_body}")
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": response_body
        }

    # スラッシュコマンドの処理
    if request_type == 2:  # APPLICATION_COMMAND
        command = body.get("data", {}).get("name")

        if command == "start":
            return start_ec2()
        elif command == "stop":
            return stop_ec2()
        elif command == "status":
            return get_status()

        return response("Unknown command")

    # その他のタイプはエラー
    return {
        "statusCode": 400,
        "body": json.dumps({"error": "Unsupported interaction type"})
    }

def _verify_signature(event):
    """Discordのリクエスト署名を検証"""
    if not PUBLIC_KEY:
        # 公開鍵が設定されていない場合は検証をスキップ（開発環境など）
        print("Warning: DISCORD_PUBLIC_KEY not set, skipping signature verification")
        return True

    headers = event.get('headers', {})
    # ヘッダー名は小文字に変換される場合がある
    signature = headers.get('x-signature-ed25519') or headers.get('X-Signature-Ed25519')
    timestamp = headers.get('x-signature-timestamp') or headers.get('X-Signature-Timestamp')
    body = event.get('body', '')

    if not signature or not timestamp:
        print("Missing signature headers")
        return False

    try:
        verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError) as e:
        print(f"Signature verification failed: {e}")
        return False

def start_ec2():
    ec2.start_instances(InstanceIds=[INSTANCE_ID])
    return response("⏳ EC2 起動中… 数分後に参加できます！")


def stop_ec2():
    ec2.stop_instances(InstanceIds=[INSTANCE_ID])
    return response("🛑 サーバー停止中…")


def get_status():
    status = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    instance = status["Reservations"][0]["Instances"][0]
    state = instance["State"]["Name"]
    ip_address = instance.get("PublicIpAddress")

    if ip_address:
        message = f"📡 EC2 状態: {state}\n🌐 公開IP: {ip_address}"
    else:
        message = f"📡 EC2 状態: {state}\n🌐 公開IP: 未割り当て"

    return response(message)


def response(message: str):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "type": 4,
            "data": {"content": message}
        })
    }
