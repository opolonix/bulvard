from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Session


import random, datetime
import sqlalchemy, os

def sclite_engine(path: str, autocommit: bool = True) -> sqlalchemy.engine.base.Engine:
    path = path.strip('\\').strip('/')
    is_new = False
    if not os.path.exists(path): 
        open(path, 'w+').close()
        is_new = True

    eng = sqlalchemy.create_engine(
        f"sqlite:///{path}",
        isolation_level = "AUTOCOMMIT" if autocommit else None
    )
    return eng, is_new

def generate_id() -> str:
    while True:
        secret = random.randint(999, 99999)
        if not session.query(Client).filter(Client.public_id == secret).first():
            return secret

engine, is_new = sclite_engine("db.db")
session = Session(bind=engine)

class Base(DeclarativeBase):
    pass

class Moderator(Base):
    __tablename__ = 'moderators'

    id = Column(Integer, primary_key=True, autoincrement=True)

    login = Column(String, nullable=False)
    password = Column(String, nullable=False)


class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    public_id = Column(Integer, unique=True, default=generate_id)
    name = Column(String, nullable=False)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    last_update = Column(DateTime, default=datetime.datetime.now)
    hidden = Column(Boolean, default=False)

class Coffee(Base):
    __tablename__ = 'coffee'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'))

    count = Column(Integer, default=1)
    event_at = Column(DateTime, default=datetime.datetime.now)
    price = Column(Integer)
    comment = Column(String, default="Кофе")


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)

    token = Column(String, unique=True, index=True)
    moderator = Column(Integer, ForeignKey('moderators.id'))

    init = Column(DateTime, default=datetime.datetime.now)

class Conf(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True, autoincrement=True)

    key = Column(String, unique=True)
    value = Column(String)

    date = Column(DateTime, default=datetime.datetime.now)

Base.metadata.create_all(bind=engine)
if is_new:
    session.add(Conf(key="login", value="admin"))
    session.add(Conf(key="password", value="admin"))
    session.commit()