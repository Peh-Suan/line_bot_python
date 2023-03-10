# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

import os


@app.route("/callback", methods=['POST'])
def callback():
    data_path = 'data.txt'
    
    if not os.path.isfile(data_path):
        data = {}
        print('Initiating new data...')
    else:
        with open(data_path, 'r') as f:
            lines = f.readlines()
            print('data appended')

        data = {line.split('/')[0]:int(line.split('/')[1].replace('\n', '')) for line in lines}

    try:
    
        def write_data(data_path, data):
            with open(data_path, 'w') as f:
                for idx, name in enumerate(data):
                    if idx+1!=len(data):
                        f.writelines(f'{name}/{data[name]}\n')
                    else:
                        f.writelines(f'{name}/{data[name]}')

        def show_data(data, name):
            amount = data[name]
            if amount > 0:
                to_reply = f'{name} ????????? {amount} ???'
            elif amount==0:
                to_reply = f'{name} ???????????????'
            else:
                to_reply = f'????????? {name} {-amount} ???'

            return to_reply

        signature = request.headers['X-Line-Signature']

        # get request body as text
        body = request.get_data(as_text=True)
        app.logger.info("Request body: " + body)

        # parse webhook body
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            abort(400)


        # if event is MessageEvent and message is TextMessage, then echo text
        for event in events:
            
            if not isinstance(event, MessageEvent):
                continue
            if not isinstance(event.message, TextMessage):
                continue
                
            to_reply = ''
            if event.message.text.strip()=='????????????':

                if data=={}:
                    to_reply = '????????????'
                else:

                    for idx, name in enumerate(data):
                        to_reply = to_reply+f'{name}: {data[name]}'
                        if idx+1!=len(data):
                            to_reply= to_reply+'\n'

            elif event.message.text.strip() in data:

                to_reply = show_data(data, event.message.text.strip())

            elif event.message.text.strip()=='????????????':
                data = {}
                to_reply = '???????????????'

            else:
                if '+' in event.message.text or '-' in event.message.text:
                    if '+' in event.message.text:
                        name = event.message.text.split('+')[0].strip()
                        amount = int(event.message.text.split('+')[1].strip())

                    elif '-' in event.message.text:
                        name = event.message.text.split('-')[0].strip()
                        amount = -int(event.message.text.split('-')[1].strip())
                    if name in data:
                        data[name] += amount
                    else:
                        data[name] = amount

                    to_reply = show_data(data, name)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=to_reply)
            )
            write_data(data_path, data)

        return 'OK'
    except Exception as e:
        print(e)
        return 'OK'


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()
    
    app.run(debug=options.debug, port=options.port)
