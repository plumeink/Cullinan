# -*- coding: utf-8 -*-
# @File   : setup.py
# @license: Copyright(C) 2020 Ore Studio
# @Author : hansion
# @Date   : 2019-02-16
# @Desc   : 

from setuptools import setup

with open("README.MD", "r", encoding="UTF-8") as fh:
    long_description = fh.read()

setup(
    name='cullinan',
    version='0.30b',
    packages=['cullinan'],
    description='cullinan',
    author='ore_studio',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email='python@orestu.com',
    url='https://cullinan.orestu.com/',
    license='http://www.apache.org/licenses/LICENSE-2.0',
    install_requires=['tornado', 'python-dotenv', 'sqlalchemy', 'pymysql'],
)
