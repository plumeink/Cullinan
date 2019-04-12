# -*- coding: utf-8 -*-
# @File   : dao.py
# @license: Copyright(C) 2019 FNEP-Tech
# @Author : hansion
# @Date   : 2019-03-15
# @Desc   :
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import *


class Conn(object):
    engine = None
    Base = object

    @classmethod
    def conn(cls):
        session = sessionmaker(cls.engine)
        session = session()
        return session

    @classmethod
    def set_db_url(cls, db_url):
        cls.db_url = db_url
        cls.engine = create_engine(cls.db_url)
        cls.Base = declarative_base(cls.engine)

    @classmethod
    def save(cls):
        Conn.Base.metadata.create_all(cls.engine)

