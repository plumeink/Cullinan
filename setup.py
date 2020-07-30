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
    version='0.31',
    packages=['cullinan'],
    description='a simple web framework',
    author='ore_studio',
    project_urls={
            'Source': 'https://github.com/orestu/Cullinan',
            'Wiki': 'https://github.com/orestu/Cullinan/wiki',
      },
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email='python@orestu.com',
    url='https://github.com/orestu/Cullinan',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    license='http://www.apache.org/licenses/LICENSE-2.0',
    install_requires=['tornado', 'python-dotenv', 'sqlalchemy', 'pymysql'],
    python_requires='>=3'
)
