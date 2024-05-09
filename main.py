from typing import List
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.staticfiles import StaticFiles

import uvicorn, string, random, re, datetime, sqlalchemy
from fastapi.responses import HTMLResponse, RedirectResponse

from orm import session, Session, Client, Moderator, Coffee
from pydantic import BaseModel

app = FastAPI()

class ClientSchema(BaseModel):
    id: int
    public_id: int
    name: str
    phone: str | None
    created_at: datetime.datetime | None
    coffee_count: int

@app.get('/', response_class=HTMLResponse) # обработка индекса
async def index(request: Request, response: Response):
    print(request.cookies)
    token = request.cookies.get('auth-token')
    if not token: return RedirectResponse("/singin")
    print(token)

    moder = session.query(Session).filter(Session.token == token).first()
    if not moder: response.delete_cookie('auth-token')
    
    print(moder)

    return open('html/index.html', encoding='utf-8').read()


@app.get('/singin', response_class=HTMLResponse) # страница авторизации
async def index(request: Request, response: Response):

    token = request.cookies.get('auth-token')
    if token: 
        moder = session.query(Session).filter(Session.token == token).first()
        if not moder: response.delete_cookie('auth-token')
        else: return RedirectResponse("/")

    return open('html/signin.html', encoding='utf-8').read()


@app.get('/session') # сюда приходит запрос на создание сессии
async def new_session(password: str, login: str, request: Request, response: Response):

    moder = session.query(Moderator).filter(Moderator.login == login and Moderator.password == password).first()
    if not moder: return {"ok": False}

    s = Session(moderator = moder.id)
    session.add(s)
    session.commit()
    
    response.set_cookie('auth-token', s.token)

    return {"ok": True}

@app.get('/clients')
async def clietnts_list(limit: int, offset: int, request: Request, response: Response) -> List[ClientSchema]:

    token = request.cookies.get('auth-token')
    moder = session.query(Session).filter(Session.token == token).first()
    if not moder: response.delete_cookie('auth-token')

    clients = (
        session.query(
            Client,
            sqlalchemy.func.sum(Coffee.count).label("coffee_count") # заменить на func.count и будет колличество посещений
        )
        .outerjoin(Coffee, Client.id == Coffee.client_id)
        .group_by(Client.id)
        .order_by(sqlalchemy.desc(Client.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [ClientSchema(id=c.id, public_id=c.public_id, name=c.name, phone=c.phone, created_at=c.created_at, coffee_count=coffee_count) for c, coffee_count in clients]

@app.get('/search')
async def clietnts_list(input: str, request: Request, response: Response) -> List[ClientSchema]:
    # input = input.lower() # поиск без учета регистра не работает в slqite
    token = request.cookies.get('auth-token')
    moder = session.query(Session).filter(Session.token == token).first()
    if not moder: response.delete_cookie('auth-token')
    clients = (
        session.query(
            Client,
            sqlalchemy.func.sum(Coffee.count).label("coffee_count") # заменить на func.count и будет колличество посещений
        )    
        .filter(Client.name.ilike(f"%{input}%") | Client.phone.ilike(f"%{input}%"))
        .outerjoin(Coffee, Client.id == Coffee.client_id)
        .group_by(Client.id)
        .order_by(sqlalchemy.desc(Client.created_at))
        .limit(20)
        .all()
    )

    
    return [ClientSchema(id=c.id, public_id=c.public_id, name=c.name, phone=c.phone, created_at=c.created_at, coffee_count=coffee_count) for c, coffee_count in clients]

app.mount("/sources", StaticFiles(directory="sources"), name="sources")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7741, reload=True)