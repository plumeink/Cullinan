# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.MD", "r", encoding="UTF-8") as fh:
    long_description = fh.read()

setup(
    name='cullinan',
    version='0.61a1',
    packages=['cullinan'],
    description='Cullinan is written based on tornado and Sqlalchemy to help the project quickly build web application',
    author='plumeink',
    project_urls={
        'Source': 'https://github.com/plumeink/Cullinan',
        'Wiki': 'https://github.com/plumeink/Cullinan/wiki',
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email='official@plumeink.com',
    url='https://github.com/plumeink/Cullinan',
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    license='http://www.apache.org/licenses/LICENSE-2.0',
    install_requires=['tornado', 'python-dotenv', 'sqlalchemy', 'pymysql', 'contextvars'],
    python_requires='>=3.7'
)
