# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.MD", "r", encoding="UTF-8") as fh:
    long_description = fh.read()

setup(
    name='cullinan',
    version='0.93.post1',
    packages=find_packages(exclude=['tests*', 'examples*', 'docs*', 'docs_archive*', 'scripts*']),
    description='Cullinan — A pluggable IoC/DI web framework',
    author='cullinan-py',
    project_urls={
        'Source': 'https://github.com/cullinan-py/cullinan',
        'Wiki': 'https://github.com/cullinan-py/cullinan/wiki',
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email='cullinan@plumeink.com',
    url='https://github.com/cullinan-py/cullinan',
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license='MIT',
    install_requires=['python-dotenv', 'contextvars'],
    extras_require={
        'tornado': ['tornado'],
        'asgi': ['uvicorn'],
        'openapi': ['pyyaml'],
        'full': ['tornado', 'uvicorn', 'pyyaml'],
    },
    python_requires='>=3.9'
)
