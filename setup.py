# -*- coding: utf-8 -*-
# @File   : setup.py
# @license: Copyright(C) 2019 FNEP-Tech
# @Author : hansion
# @Date   : 2019-02-16
# @Desc   : 

from setuptools import setup

setup(
    name='cullinan',
    version='0.2.3',
    packages=['cullinan'],
    description='cullinan',
    author='fnep_tech',
    author_email='hansion@fnep-tech.com',
    url='https://www.fnep-tech.com/',
    license='http://www.apache.org/licenses/LICENSE-2.0',
    install_requires=['tornado', 'python-dotenv', 'sqlalchemy', 'pymysql'],
)
