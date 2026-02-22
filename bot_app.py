import os
import logging
import asyncio
from io import BytesIO
import requests
from flask import Flask, request
from telegram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8249720818:AAEihtjIUeyLYqX3JDdbl3lLFBJ3NO4k19g')
GYAZO_ACCESS_TOKEN = os.environ.get('GYAZO_ACCESS_TOKEN', 'YOUR_GYAZO_TOKEN_HERE')

app = Flask(__name__)

def upload_to_gyazo(image_bytes):
    image_bytes.seek(0)
    response = requests.post(
        'https://upload.gyazo.com/api/upload',
        headers={'Authorization': 'Bearer ' + GYAZO_ACCESS_TOKEN},
        files={'imagedata': ('photo.jpg', image_bytes, 'image/jpeg')},
        timeout=30
    )
    data = response.json()
    if 'url' in data:
        return data['url']
    else:
        raise Exception('Gyazo upload failed: ' + str(data))

async def handle_photo_logic(update):
    bot = Bot(token=BOT_TOKEN)
    if update.get('message') and update['message'].get('photo'):
        photo = update['message']['photo'][-1]
        file_id = photo['file_id']
        chat_id = update['message']['chat']['id']
        try:
            file_info = await bot.get_file(file_id)
            file_bytes = await file_info.download_as_bytearray()
            image_bytes = BytesIO(bytes(file_bytes))
            gyazo_url = upload_to_gyazo(image_bytes)
            await bot.send_message(chat_id=chat_id, text=gyazo_url)
        except Exception as e:
            await bot.send_message(chat_id=chat_id, text='Sorry, upload failed: ' + str(e))
    elif update.get('message'):
        chat_id = update['message']['chat']['id']
        await bot.send_message(chat_id=chat_id, text='Send me a photo and I will upload it for you!')

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(handle_photo_logic(update))
        except Exception as e:
            logger.error('Webhook error: ' + str(e))
        finally:
            loop.close()
    return 'OK', 200

@app.route('/')
def index():
    return 'Bot is running!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
