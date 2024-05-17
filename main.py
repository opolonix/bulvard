from typing import Annotated, List
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
    token = request.cookies.get('auth-token')
    if not token: return RedirectResponse("/singin")

    moder = session.query(Session).filter(Session.token == token).first()
    # if not moder: response.delete_cookie('auth-token')
    
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
    
    if not moder: 
        response.delete_cookie('auth-token')
        return RedirectResponse("/singin")

    clients = (
        session.query(
            Client,
            sqlalchemy.func.sum(Coffee.count).label("coffee_count") # заменить на func.count и будет колличество посещений
        )
        .outerjoin(Coffee, Client.id == Coffee.client_id)
        .group_by(Client.id)
        .order_by(sqlalchemy.desc(Client.last_update))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [ClientSchema(id=c.id, public_id=c.public_id, name=c.name, phone=c.phone, created_at=c.created_at, last_update=c.last_update, coffee_count=coffee_count if coffee_count else 0) for c, coffee_count in clients]


@app.get('/new-client')
async def clietnts_list(name: str, phone: str, request: Request, response: Response) -> dict:

    token = request.cookies.get('auth-token')
    moder = session.query(Session).filter(Session.token == token).first()

    if not moder: 
        response.delete_cookie('auth-token')
        return RedirectResponse("/singin")

    phone = re.sub(r'[^0-9]', '', phone)

    if phone == '':
        return {"ok": False, "message": "Пустой номер телефона!"}

    if session.query(Client).filter(Client.phone == phone).first():
        return {"ok": False, "message": "Номер телефона уже существует в записях!"}
    
    c = Client(
        name = re.sub(r'\s\s', '', name.title()),
        phone = re.sub(r'[^0-9]', '', phone)
    )
    session.add(c)
    session.commit()

    return {"ok": True, "message": "Запись добавлена!"}


@app.get('/new-coffee')
async def clietnts_list(client: int, count, comment: str, request: Request, response: Response) -> dict:

    token = request.cookies.get('auth-token')
    moder = session.query(Session).filter(Session.token == token).first()
    
    if not moder: 
        response.delete_cookie('auth-token')
        return RedirectResponse("/singin")

    db_clietn = session.query(Client).filter(Client.id == client).first()

    if not db_clietn:
        return {"ok": False, "message": "Чтото не то с клиентом!"}
    
    db_clietn.last_update = datetime.datetime.now()

    c = Coffee(
        client_id = client,
        count = count,
        price = 0,
        comment = comment
    )

    session.add(c)
    session.commit()

    return {"ok": True, "message": "Запись добавлена!"}
@app.get('/search')
async def clietnts_list(input: str, request: Request, response: Response) -> List[ClientSchema]:
    # input = input.lower() # поиск без учета регистра не работает в slqite
    token = request.cookies.get('auth-token')
    moder = session.query(Session).filter(Session.token == token).first()

    if not moder: 
        response.delete_cookie('auth-token')
        return RedirectResponse("/singin")

    input = re.sub(r'\s\s', '', input.title())
    phone = re.sub(r'[^0-9]', '', input)
    if phone != "":
        clients = (
            session.query(
                Client,
                sqlalchemy.func.sum(Coffee.count).label("coffee_count") # заменить на func.count и будет колличество посещений
            )    
            .filter(Client.name.ilike(f"%{input}%") | Client.phone.ilike(f"%{re.sub(r'[^0-9]', '', phone)}%"))
            .outerjoin(Coffee, Client.id == Coffee.client_id)
            .group_by(Client.id)
            .order_by(sqlalchemy.desc(Client.created_at))
            .limit(20)
            .all()
        )
    else:
        clients = (
            session.query(
                Client,
                sqlalchemy.func.sum(Coffee.count).label("coffee_count") # заменить на func.count и будет колличество посещений
            )    
            .filter(Client.name.ilike(f"%{input}%"))
            .outerjoin(Coffee, Client.id == Coffee.client_id)
            .group_by(Client.id)
            .order_by(sqlalchemy.desc(Client.created_at))
            .limit(20)
            .all()
        )

    
    return [ClientSchema(id=c.id, public_id=c.public_id, name=c.name, phone=c.phone, created_at=c.created_at, last_update=c.last_update, coffee_count=coffee_count) for c, coffee_count in clients]

app.mount("/sources", StaticFiles(directory="sources"), name="sources")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7741, reload=True)