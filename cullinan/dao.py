# -*- coding: utf-8 -*-
# @File   : dao.py
# @license: Copyright(C) 2020 Ore Studio
# @Author : hansion
# @Date   : 2019-03-15
# @Desc   :
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import *
from sqlalchemy.dialects.mysql import *
import os


class Conn(object):
    db_url = 'mysql+pymysql://{}:{}@{}:{}/{}?charset={}'.format(
        os.getenv("DB_USERNAME"),
        os.getenv("DB_PASSWORD"),
        os.getenv("DB_HOST"),
        os.getenv("DB_PORT"),
        os.getenv("DB_NAME"),
        os.getenv("DB_CODING")
    )
    engine = create_engine(db_url)
    Base = declarative_base(engine)

    @classmethod
    def conn(cls):
        session = sessionmaker(Conn.engine)
        session = session()
        return session

    @classmethod
    def save(cls):
        Conn.Base.metadata.create_all(Conn.engine)

