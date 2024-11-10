# -*- coding: utf-8 -*-

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
        os.getenv("DB_CODING"),
        os.getenv("DB_POOL_RECYCLE"),
        os.getenv("DB_POOL_SIZE"),
        os.getenv("DB_MAX_OVERFLOW")
    ) if os.getenv("DB_TYPE", 'mysql') == 'mysql' else 'sqlite:///{}'.format(os.getenv("DB_NAME"))
    engine = create_engine(db_url)
    Base = declarative_base()

    @classmethod
    def conn(cls):
        session = sessionmaker(Conn.engine)
        session = session()
        return session

    @classmethod
    def save(cls):
        Conn.Base.metadata.create_all(Conn.engine)

