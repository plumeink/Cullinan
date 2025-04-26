# -*- coding: utf-8 -*-
import importlib
import inspect
import os
import pkgutil

import tornado.ioloop
from cullinan.controller import handler_list, header_list
from dotenv import load_dotenv
from pathlib import Path
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpserver
from tornado.options import define, options
import sys
import platform
from cullinan.exceptions import CallerPackageException


def is_nuitka_compiled():
    return "__compiled__" in globals()

def get_project_root_with_pyinstaller():
    return os.path.dirname(os.path.abspath(__file__)) + '/../'

def get_caller_package():
    project_root = get_project_root_with_pyinstaller()
    stack = inspect.stack()
    for frame in stack:
        module = inspect.getmodule(frame[0])
        if module and module.__name__.startswith('cullinan'):
            continue
        caller_filename = os.path.relpath(frame.filename, project_root)
        caller_package = os.path.dirname(caller_filename).replace(os.sep, '.')
        return caller_package
    raise CallerPackageException()

def list_submodules(package_name):
    package = importlib.import_module(package_name)
    submodules = []
    if hasattr(package, '__path__'):
        for _, name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
            if not is_pkg:
                submodules.append(name)
    return submodules

def reflect(file: str, func: str):
    try:
        if func == 'nobody':
            __import__(file.replace('.py', ''))
        elif func == 'controller':
            __import__(file.replace('.py', ''))
        else:
            f = __import__(file.replace('.py', ''))
            function = getattr(f, func)
            function()
    except AttributeError:
        pass


def file_list_func():
    if is_nuitka_compiled():
        module_list = []
        for module in pkgutil.walk_packages(path=[__compiled__.containing_dir]):
            if module.ispkg:
                module_list = module_list + list_submodules(module.name)
        return module_list
    if getattr(sys, 'frozen', False):
        caller_package = get_caller_package()
        return list_submodules(caller_package)
    file_list = []
    for top, dirs, files in os.walk(os.getcwd()):
        for files_item in files:
            if os.path.splitext(files_item)[1] == '.py' and files_item != sys.argv[0][sys.argv[0].rfind(os.sep) + 1:]:
                if os.path.split(top)[-1] == os.path.split(os.getcwd())[-1]:
                    file_list.append(files_item)
                else:
                    system = platform.system()
                    if system == "Windows":
                        item = top.replace(os.path.split(os.path.realpath(sys.argv[0]))[0] + '\\', '')\
                                   .replace('\\', '.') + '.' + files_item
                        file_list.append(item)
                    else:
                        item = top.replace(os.path.split(os.path.realpath(sys.argv[0]))[0] + '/', '')\
                                   .replace('/', '.') + '.' + files_item
                        file_list.append(item)
    return file_list


def scan_controller(file_path: list):
    for x in file_path:
        reflect(x, 'controller')


def scan_service(file_path: list):
    for x in file_path:
        reflect(x, 'nobody')


def get_index_list(url_list: list) -> list:
    index_list = []
    for index in range(0, url_list.__len__()):
        if url_list[index] == '([a-zA-Z0-9-]+)':
            index_list.append(index)
    index_list.append('*')
    return index_list


def sort_url():
    if handler_list.__len__() == 0:
        return
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
                    if handler_list[i][2][index] != '*' and handler_list[j][2][index] != '*':
                        if handler_list[i][2][index] < handler_list[j][2][index]:
                            handler_list[i], handler_list[j] = handler_list[j], handler_list[i]
                    elif handler_list[i][2][index] != '*' and handler_list[j][2][index] == '*':
                        handler_list[i], handler_list[j] = handler_list[j], handler_list[i]
                    elif handler_list[i][2][index] == '*':
                        continue
    for item in handler_list:
        url = ""
        for index in range(1, len(item[0])):
            url = url + "/" + item[0][index]
        item[0] = url
        del item[2]


def run(handlers=None):
    if handlers is None:
        handlers = []
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
        handlers=handler_list + handlers,
        **settings
    )
    print("\t|||\t\t└---loading controller finish\n\t|||\t")
    define("port", default=os.getenv("SERVER_PORT", 4080), help="run on the given port", type=int)
    print("\t|||\tloading env finish\n\t|||\t")
    http_server = tornado.httpserver.HTTPServer(mapping)
    if os.getenv("SERVER_THREAD") is not None:
        print("\t|||\t\033[0;36;0mserver is starting \033[0m")
        print("\t|||\t\033[0;36;0mport is " + str(os.getenv("SERVER_PORT", 4080)) + " \033[0m")
        http_server.bind(options.port)
        http_server.start(int(os.getenv("SERVER_THREAD")) | 0)
    else:
        http_server.listen(options.port)
        print("\t|||\t\033[0;36;0mserver is starting \033[0m")
        print("\t|||\t\033[0;36;0mport is " + str(os.getenv("SERVER_PORT", 4080)) + " \033[0m")
    tornado.ioloop.IOLoop.current().start()


def add_global_header(name: str, value: str):
    header_list.append([name, value])
