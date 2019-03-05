# -*- coding: utf-8 -*-
# @File   : application.py
# @license: Copyright(C) 2019 FNEP-Tech
# @Author : hansion, fox
# @Date   : 2019-02-15
# @Desc   : start

import os
import tornado.ioloop
from cullinan.controller import url_list
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
        f = __import__(file.replace('.py', ''))
        function = getattr(f, func)
        function()
        print("\t|||\t\t\t...")
    except AttributeError:
        print("\t|||\t\t\t...")


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


def scan(file_path, func):
    for x in file_path:
        reflect(x, func)


def run():
    print("\n|||||||||||||||||||||||||||||||||||||||||||||||||\n|||                                           |||\n|||     _____      _ _ _       "
          "               |||\n|||    / ____|    | | (_)                     |||\n|||   | |    _   _| | |_ _ __   __ "
          "_ _ __     |||\n|||   | |   | | | | | | | '_ \ / _` | '_ \    |||\n|||   | |___| |_| | | | | | | | (_| | | | |   |||\n|||    \_____\__,"
          "_|_|_|_|_| |_|\__,_|_| |_|   |||\n|||                                           |||\n|||||||||||||||||||||||||||||||||||||||||||||||||\n\t|||")
    print("\t|||\tloading env...")
    load_dotenv()
    load_dotenv(verbose=True)
    env_path = Path(os.getcwd()) / '.env'
    load_dotenv(dotenv_path=env_path)
    settings = dict(
        template_path=os.path.join(os.getcwd(), 'templates'),
        static_path=os.path.join(os.getcwd(), 'statics')
    )
    print("\t|||\t\t└---scanning controller...")
    scan(file_list_func(), "get_api")
    scan(file_list_func(), "post_api")
    scan(file_list_func(), "put_api")
    scan(file_list_func(), "delete_api")
    scan(file_list_func(), "patch_api")
    mapping = tornado.web.Application(
        handlers=url_list,
        **settings
    )
    print("\t|||\t\t└---loading controller finish\n\t|||\t")
    define("port", default=os.getenv("SERVER_PORT"), help="run on the given port", type=int)
    print("\t|||\tloading env finish\n\t|||\t")
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(mapping)
    http_server.listen(options.port)
    print("\t|||\t\033[0;36;0mserver is starting \033[0m")
    print("\t|||\t\033[0;36;0mport is " + str(os.getenv("SERVER_PORT")) + " \033[0m")
    tornado.ioloop.IOLoop.instance().start()
