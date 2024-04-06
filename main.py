import os
import json
import time
import uuid
import random
import requests
import threading
from flask import Flask, Response, request
from flask_cors import CORS
from gevent import pywsgi

app = Flask(__name__)
CORS(app)
headers = {
    'origin': 'https://chat.openai.com',
    'referer': 'https://chat.openai.com',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}


def set_token():
    url = 'https://chat.openai.com/backend-anon/sentinel/chat-requirements'
    headers['oai-device-id'] = str(uuid.uuid4())
    while True:
        try:
            resp = requests.post(url=url, headers=headers, json={})
            resp_json = json.loads(resp.text)
            print(resp_json)
            headers['openai-sentinel-chat-requirements-token'] = resp_json.get('token')
        except Exception as e:
            print(e)
        time.sleep(60)


def get_message(messages):
    url = 'https://chat.openai.com/backend-anon/conversation'
    payload = {
        'action': 'next',
        'messages': messages,
        'parent_message_id': str(uuid.uuid4()),
        'model': 'text-davinci-002-render-sha',
        'timezone_offset_min': -480,
        'suggestions': [],
        'history_and_training_disabled': False,
        'conversation_mode': {
            'kind': 'primary_assistant'
        },
        'force_paragen': False,
        'force_paragen_model_slug': '',
        'force_nulligen': False,
        'force_rate_limit': False,
        'websocket_request_id': str(uuid.uuid4())
    }
    try:
        data = {}
        with requests.post(url=url, headers=headers, json=payload, stream=True) as resp:
            for line in resp.iter_lines():
                if line:
                    string = line.decode()
                    if 'data: [DONE]' != string:
                        data = json.loads(string[len('data: '):])
                        message = data.get('message', {})
                        if 'assistant' == message.get('author', {}).get('role'):
                            parts = message.get('content', {}).get('parts', [''])
                            if 'in_progress' == message.get('status'):
                                yield parts[0]
        print(data)
    except Exception as e:
        print(e)


def get_completion_id():
    return 'chatcmpl-{}'.format(
        ''.join(random.choices(population='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=29)))


def get_result(messages):
    completion_id = get_completion_id()
    created = int(time.time())
    string = ''
    for message in get_message(messages):
        data = message[len(string):]
        string = message
        yield 'data: {}\n\n'.format(json.dumps({
            'id': completion_id,
            'object': 'chat.completion.chunk',
            'created': created,
            'model': 'gpt-3.5-turbo',
            'choices': [
                {
                    'index': 0,
                    'delta': {
                        'content': data,
                    },
                    'logprobs': None,
                    'finish_reason': None,
                },
            ],
        }))
    yield 'data: {}\n\n'.format(json.dumps({
        'id': completion_id,
        'object': 'chat.completion.chunk',
        'created': created,
        'model': 'gpt-3.5-turbo',
        'choices': [
            {
                'index': 0,
                'delta': {},
                'logprobs': None,
                'finish_reason': 'stop',
            },
        ],
    }))


@app.route('/v1/chat/completions', methods=['POST'])
def completions():
    try:
        data = request.get_data()
        data_json = json.loads(data)
        print(data_json)
        messages = []
        for message in data_json.get('messages'):
            messages.append({
                'id': str(uuid.uuid4()),
                'author': {
                    'role': message.get('role')
                },
                'content': {
                    'content_type': 'text',
                    'parts': [
                        message.get('content')
                    ]
                },
                'metadata': {}
            })
        return Response(get_result(messages), content_type='text/event-stream')
    except Exception as e:
        return {'message': e}


@app.route('/', methods=['GET'])
def index():
    return {'message': '/v1/chat/completions'}


if __name__ == '__main__':
    # os.environ.update(HTTP_PROXY='127.0.0.1:7890', HTTPS_PROXY='127.0.0.1:7890')
    threading.Thread(target=set_token).start()
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app)
    server.serve_forever()
