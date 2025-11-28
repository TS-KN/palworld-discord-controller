#!/bin/bash

# DiscordのPINGリクエストをテストするスクリプト
# 使用方法: ./test-discord-ping.sh <API_GATEWAY_URL>

if [ -z "$1" ]; then
    echo "使用方法: $0 <API_GATEWAY_URL>"
    echo "例: $0 https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/webhook"
    exit 1
fi

ENDPOINT_URL="$1"

echo "🧪 Discord PINGリクエストをテストします..."
echo "エンドポイント: $ENDPOINT_URL"
echo ""

# DiscordのPINGリクエスト（type: 1）を送信
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"type": 1}' \
  "$ENDPOINT_URL")

# レスポンスを分離
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)

echo "HTTPステータス: $HTTP_STATUS"
echo "レスポンスボディ:"
echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
    # レスポンスボディをチェック
    TYPE=$(echo "$BODY" | jq -r '.type' 2>/dev/null)
    if [ "$TYPE" = "1" ]; then
        echo "✅ 成功！PINGリクエストに正しく応答しています。"
    else
        echo "⚠️  HTTPステータスは200ですが、レスポンスのtypeが1ではありません。"
        echo "   期待: {\"type\": 1}"
        echo "   実際: $BODY"
    fi
else
    echo "❌ エラー: HTTPステータスが200ではありません。"
    echo "   Lambda関数のログを確認してください。"
fi

