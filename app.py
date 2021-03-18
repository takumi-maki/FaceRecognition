import os
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage
)

from io import BytesIO

from azure.cognitiveservices.vision.face import FaceClient

from msrest.authentication import CognitiveServicesCredentials

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.getenv('YOUR_CHANNEL_ACCESS_TOKEN')
YOUR_CHANNEL_SECRET = os.getenv('YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

YOUR_FACE_API_KEY = os.environ["YOUR_FACE_API_KEY"]
YOUR_FACE_API_ENDPOINT = os.environ["YOUR_FACE_API_ENDPOINT"]

face_client = FaceClient(
    YOUR_FACE_API_ENDPOINT,
    CognitiveServicesCredentials(YOUR_FACE_API_KEY)
)


@app.route("/hello")
def hello():
    return "hello world"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    if text in ['愛してる', '好き']:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text + "と言ってくれてありがとう！"))
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text)
        )


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    try:
        message_id = event.message.id
        message_content = line_bot_api.get_message_content(message_id)
        image = BytesIO(message_content.content)
        detected_faces = face_client.face.detect_with_stream(image)
        print(detected_faces)

        if detected_faces != []:
            text = detected_faces[0].face_id
        else:
            text = 'no faces detected'
    except:
        text = 'error'

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text)
    )


if __name__ == "__main__":
    app.run()
