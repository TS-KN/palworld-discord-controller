import json
import boto3
import os

ec2 = boto3.client('ec2')
INSTANCE_ID = os.environ['INSTANCE_ID']


def handler(event, context):
    body = json.loads(event['body'])

    command = body.get("data", {}).get("name")

    if command == "start":
        return start_ec2()
    elif command == "stop":
        return stop_ec2()
    elif command == "status":
        return get_status()

    return response("Unknown command")


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
