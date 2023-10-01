from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import os
import json
import uuid
import pika

API_TOKEN = os.getenv('BOT_TOKEN')
MQ_CONNECTION_URL = os.getenv('MQ_CONNECTION_URL')
print(f'MQ_CONNECTION_URL={MQ_CONNECTION_URL}')

bot = Bot(token=API_TOKEN) # телеграм-бот

# ========================
#
# Конфигурация очереди MQ
#
# ========================

 # Подключение к очереди

QUEUE_REQUEST = 'request'
QUEUE_RESPONSE = 'response'

mq_connection = pika.BlockingConnection(pika.ConnectionParameters(MQ_CONNECTION_URL))
mq_channel = mq_connection.channel()
mq_req_channel.queue_declare(queue=QUEUE_REQUEST)
mq_resp_channel.queue_declare(queue=QUEUE_RESPONSE)

# Отправка запроса

def mq_send_request(user_id, query):
    message = {
        'query': query,
        'key': uuid.uuid4(),
        'user_id': user_id
    }
    mq_req_channel.basic_publish(exchange='',
                      routing_key=QUEUE_REQUEST,
                      body=json.dumps(message))
    return message['key']

# Обработка ответа

def mq_response_callback(ch, method, properties, body):
    msg = json.loads(body)
    bot.send_message(msg.user_id, f'Ответ на запрос {msg["key"]}. {msg["answer"]}')
    print(f" [x] Received {body}")

mq_resp_channel.basic_consume(queue=QUEUE_RESPONSE,
                      auto_ack=True,
                      on_message_callback=mq_response_callback)


# ========================
# 
# Конфигурация телеграма
#
# ========================

dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет!\nМеня зовут Бобот! Я работать сотрудник отдела кадров. Ты задавать вопрос, я отвечать.")


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Задай мне вопрос и я отвечу")


@dp.message_handler()
async def echo_message(msg: types.Message):
    request_id = mq_send_request(msg.from_user.id, msg.text)
    await bot.send_message(msg.from_user.id, f'Запрос отправлен в языковую модель. Номер запроса: {request_id}')


# ==================
#
# Запуск приложения
#
# ==================

if __name__ == '__main__':
    executor.start_polling(dp)
    mq_connection.close()