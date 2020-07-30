# -*- coding: utf-8 -*-
# @File   : application.py
# @license: Copyright(C) 2020 Ore Studio
# @Author : hansion, fox
# @Date   : 2019-02-15
# @Desc   : start

import os
import tornado.ioloop
from cullinan.controller import handler_list
from dotenv import load_dotenv
from pathlib import Path
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpserver
from tornado.options import define, options
import sys


def reflect(file, func):
    try:
        if func is None:
            __import__(file.replace('.py', ''))
        elif func is 'controller':
            f = __import__(file.replace('.py', ''))
            function = getattr(f, func)
        else:
            f = __import__(file.replace('.py', ''))
            function = getattr(f, func)
            function()
    except AttributeError:
        pass


def file_list_func():
    file_list = []
    for top, dirs, files in os.walk(os.getcwd()):
        for files_item in files:
            if os.path.splitext(files_item)[1] == '.py' and files_item != sys.argv[0][sys.argv[0].rfind(os.sep) + 1:]:
                if os.path.split(top)[-1] == os.path.split(os.getcwd())[-1]:
                    file_list.append(files_item)
                else:
                    item = os.path.split(top)[-1] + '.' + files_item
                    file_list.append(item)
    return file_list


def scan_controller(file_path):
    for x in file_path:
        reflect(x, 'controller')


def scan_service(file_path):
    for x in file_path:
        reflect(x, None)


def get_index_list(url_list):
    index_list = []
    for index in range(0, url_list.__len__()):
        if url_list[index] == '([a-zA-Z0-9-]+)':
            index_list.append(index)
    index_list.append('*')
    return index_list


def sort_url():
    handler_list_length = []
    for index in range(0, handler_list.__len__()):
        handler_list[index] = list(handler_list[index])
        handler_list[index][0] = handler_list[index][0].split('/')
        index_list = get_index_list(handler_list[index][0])
        handler_list_length.append(index_list.__len__())
        handler_list[index].append(index_list)
    for index in range(0, max(handler_list_length)):
        for i in range(0, handler_list.__len__()):
            for j in range(i + 1, handler_list.__len__()):
                if handler_list[i][2].__len__() >= index + 1 and handler_list[j][2].__len__() >= index + 1:
                    if handler_list[i][2][index] is not '*' and handler_list[j][2][index] is not '*':
                        if handler_list[i][2][index] < handler_list[j][2][index]:
                            handler_list[i], handler_list[j] = handler_list[j], handler_list[i]
                    elif handler_list[i][2][index] is not '*' and handler_list[j][2][index] is '*':
                        handler_list[i], handler_list[j] = handler_list[j], handler_list[i]
                    elif handler_list[i][2][index] is '*':
                        continue
    for item in handler_list:
        url = ""
        for index in range(1, len(item[0])):
            url = url + "/" + item[0][index]
        item[0] = url
        del item[2]


def run():
    print(
        "\n|||||||||||||||||||||||||||||||||||||||||||||||||\n|||                                           |||\n|||  "
        "   _____      _ _ _ "
        "               |||\n|||    / ____|    | | (_)                     |||\n|||   | |    _   _| | |_ _ __   __ "
        "_ _ __     |||\n|||   | |   | | | | | | | '_ \ / _` | '_ \    |||\n|||   | |___| |_| | | | | | | | (_| | | | "
        "|   |||\n|||    \_____\__, "
        "_|_|_|_|_| |_|\__,_|_| |_|   |||\n|||                                           "
        "|||\n|||||||||||||||||||||||||||||||||||||||||||||||||\n\t|||")
    print("\t|||\tloading env...")
    load_dotenv()
    load_dotenv(verbose=True)
    env_path = Path(os.getcwd()) / '.env'
    load_dotenv(dotenv_path=env_path)
    settings = dict(
        template_path=os.path.join(os.getcwd(), 'templates'),
        static_path=os.path.join(os.getcwd(), 'static')
    )
    print("\t|||\t\t└---scanning controller...")
    print("\t|||\t\t\t...")
    scan_service(file_list_func())
    scan_controller(file_list_func())
    sort_url()
    mapping = tornado.web.Application(
        handlers=handler_list,
        **settings
    )
    print("\t|||\t\t└---loading controller finish\n\t|||\t")
    define("port", default=os.getenv("SERVER_PORT"), help="run on the given port", type=int)
    print("\t|||\tloading env finish\n\t|||\t")
    http_server = tornado.httpserver.HTTPServer(mapping)
    if os.getenv("SERVER_THREAD") is not None:
        print("\t|||\t\033[0;36;0mserver is starting \033[0m")
        print("\t|||\t\033[0;36;0mport is " + str(os.getenv("SERVER_PORT")) + " \033[0m")
        http_server.bind(options.port)
        http_server.start(int(os.getenv("SERVER_THREAD")) | 0)
    else:
        http_server.listen(options.port)
        print("\t|||\t\033[0;36;0mserver is starting \033[0m")
        print("\t|||\t\033[0;36;0mport is " + str(os.getenv("SERVER_PORT")) + " \033[0m")
    tornado.ioloop.IOLoop.current().start()
