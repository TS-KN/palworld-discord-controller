import json
import boto3
import os

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

ec2 = boto3.client('ec2')
INSTANCE_ID = os.environ.get('INSTANCE_ID', '')
PUBLIC_KEY = os.environ.get('DISCORD_PUBLIC_KEY', '')


def lambda_handler(event, context):
    try:
        # セキュリティヘッダーの検証（リクエスト処理の前に実行）
        if not _verify_signature(event):
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Unauthorized"})
            }
    except Exception as e:
        print(f"Error in signature verification: {e}")
        # 検証エラーが発生した場合は401を返す
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

    try:
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
            print(f"Processing command: {command}")

            if command == "start":
                print("Starting /start command processing")
                try:
                    result = start_ec2()
                    print(f"/start command completed successfully, response: {json.dumps(result)}")
                    return result
                except Exception as e:
                    print(f"Error in /start command: {e}", exc_info=True)
                    return response(f"❌ エラーが発生しました: {str(e)}")
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
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
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

def _get_instance_state_and_ip():
    """EC2 インスタンスの状態と Public IP を取得する共通関数"""
    print(f"[_get_instance_state_and_ip] Getting state for instance: {INSTANCE_ID}")
    try:
        print("[_get_instance_state_and_ip] Calling describe_instances...")
        status = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
        print(f"[_get_instance_state_and_ip] describe_instances response received")

        if not status.get("Reservations") or len(status["Reservations"]) == 0:
            print("[_get_instance_state_and_ip] No reservations found")
            raise Exception("No reservations found for instance")

        if not status["Reservations"][0].get("Instances") or len(status["Reservations"][0]["Instances"]) == 0:
            print("[_get_instance_state_and_ip] No instances found in reservation")
            raise Exception("No instances found in reservation")

        instance = status["Reservations"][0]["Instances"][0]
        state = instance["State"]["Name"]
        ip_address = instance.get("PublicIpAddress")
        print(f"[_get_instance_state_and_ip] State: {state}, IP: {ip_address}")

        return state, ip_address
    except Exception as e:
        print(f"[_get_instance_state_and_ip] Exception: {e}", exc_info=True)
        raise


def start_ec2():
    print(f"[start_ec2] Function called, INSTANCE_ID: {INSTANCE_ID}")

    try:
        # まず現在の状態を確認
        print("[start_ec2] Getting instance state and IP...")
        state, ip_address = _get_instance_state_and_ip()
        print(f"[start_ec2] Current state: {state}, IP: {ip_address}")

        # すでに起動済みの場合は、その旨とIP（あれば）を返す
        if state == "running":
            print("[start_ec2] Instance is already running")
            if ip_address:
                message = f"✅ すでに起動中です！\n📡 EC2 状態: {state}\n🌐 公開IP: {ip_address}:8211"
            else:
                message = f"✅ すでに起動中です！\n📡 EC2 状態: {state}\n🌐 公開IP: 未割り当て"
            print(f"[start_ec2] Returning message: {message}")
            return response(message)

        # 起動していない場合は起動処理を実行
        print(f"[start_ec2] Starting instance {INSTANCE_ID}...")
        start_response = ec2.start_instances(InstanceIds=[INSTANCE_ID])
        print(f"[start_ec2] Start response: {json.dumps(start_response, default=str)}")
        message = "⏳ EC2 起動中… 数分後に参加できます！"
        print(f"[start_ec2] Returning message: {message}")
        return response(message)
    except Exception as e:
        print(f"[start_ec2] Exception occurred: {e}", exc_info=True)
        raise


def stop_ec2():
    # 現在の状態を確認
    state, _ = _get_instance_state_and_ip()

    # すでに停止中 or 停止処理中の場合
    if state in ("stopping", "stopped"):
        if state == "stopped":
            message = "✅ すでに停止済みです。"
        else:
            message = "⏳ すでに停止処理中です…"
        return response(message)

    # 起動中などの場合は停止処理を開始
    ec2.stop_instances(InstanceIds=[INSTANCE_ID])
    return response("🛑 サーバー停止中… 数分後に完全に停止します。")


def get_status():
    state, ip_address = _get_instance_state_and_ip()

    if ip_address:
        message = f"📡 EC2 状態: {state}\n🌐 公開IP: {ip_address}:8211"
    else:
        message = f"📡 EC2 状態: {state}\n🌐 公開IP: 未割り当て"

    return response(message)


def response(message: str):
    response_data = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "type": 4,
            "data": {"content": message}
        })
    }
    print(f"[response] Returning response: {json.dumps(response_data)}")
    return response_data
