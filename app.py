from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
from starlette.responses import PlainTextResponse

from jinja2 import Template
from orm import session, Client, Coffee, Conf
import os
import sqlalchemy
import re
import json

app = FastAPI()

def get_clients():
    raw_clients = (
        session.query(
            Client,
            sqlalchemy.func.sum(Coffee.count).label("coffee_count"),
            sqlalchemy.func.count(Coffee.count).label("visits"),
            sqlalchemy.func.max(Coffee.event_at).label("last_visit"),
            sqlalchemy.func.min(Coffee.event_at).label("first_visit"),
            sqlalchemy.func.sum(Coffee.price).label("spent")
        )
        .outerjoin(Coffee, Client.id == Coffee.client_id)
        .group_by(Client.id)
        .order_by(sqlalchemy.desc(Client.last_update))
        .all()
    )

    clients = []
    for client in raw_clients:
        data = {c.name: getattr(client[0], c.name) for c in client[0].__table__.columns}
        if data['hidden']: continue
        if not client[1]:
            data.update({["coffee_count", "visits", "last_visit", "first_visit", "spent"][i]: c for i, c in enumerate([0, 0, data["last_update"], data["last_update"], 0])})
        else:
            data.update({["coffee_count", "visits", "last_visit", "first_visit", "spent"][i-2]: c for i, c in enumerate(client, 1)})
        
        clients.append(data)

    return clients

@app.get("/admin", response_class=HTMLResponse)
async def index():
    with open(os.path.join(os.getcwd(), "www", "admin.jinja"), encoding="utf-8") as f:
        content = f.read()

    clients = get_clients()
    
    config = session.query(Conf).all()
    config: dict[str, str] = {c.key: c.value for c in config}

    coffee_limit = int(c if (c := config.get("coffee_limit", 6)) != '' else 6)

    if int(config.get("sort_by_name", True)):
        clients.sort(key=lambda client: client['name'])
    if int(config.get("sort_by_date", False)):
        clients.sort(key=lambda client: client['last_visit'])
    if int(config.get("pin_bonus_coffee", True)):
        clients.sort(key=lambda client: client['coffee_count'] % coffee_limit != coffee_limit - 1)

    t = Template(content)
    return HTMLResponse(t.render(clients=clients, coffee_limit=coffee_limit))


@app.get("/{f:path}.{e}")
async def files(f: str, e: str):
    path = os.path.join(os.getcwd(), "www", f"{f}.{e}")
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(404)


@app.get("/changeName")
async def files(id: str, name: str):
    client = session.query(Client).filter(Client.public_id == id).first()
    if client:
        client.name = name
        session.commit()
    return 200

@app.get("/dropClient")
async def files(id: str):
    client = session.query(Client).filter(Client.public_id == id).first()
    if client:
        client.hidden = True
        session.commit()
    return 200

@app.get("/newOrder")
async def files(id: str, count: int):
    if count == 0: return 200
    client = session.query(Client).filter(Client.public_id == id).first()
    if client:    
        c = Coffee(
            client_id = client.id,
            count = count,
            price = 0,
            comment="Кофе"
        )

        session.add(c)
        session.commit()
    return 200

@app.get("/newClient", response_class=PlainTextResponse)
async def files(name: str, phone: str):
    phone = re.sub(r"^[\d]", '', phone)
    client = Client(
        name=name,
        phone=phone
    )
    session.add(client)
    session.commit()

    return str(client.public_id)


@app.get("/search", response_class=HTMLResponse)
async def search(input: str = ""):
    with open(os.path.join(os.getcwd(), "www", "search.jinja"), encoding="utf-8") as f:
        content = f.read()

    clients = get_clients()
    
    config = session.query(Conf).all()
    config: dict[str, str] = {c.key: c.value for c in config}

    coffee_limit = int(c if (c := config.get("coffee_limit", 6)) != '' else 6)
    if input != "":
        if int(config.get("sort_by_name", True)):
            clients.sort(key=lambda client: client['name'])
        if int(config.get("sort_by_date", False)):
            clients.sort(key=lambda client: client['last_visit'])
        if int(config.get("pin_bonus_coffee", True)):
            clients.sort(key=lambda client: client['coffee_count'] % coffee_limit != coffee_limit - 1)

        result = {
            "Имена": list(filter(lambda x: input.lower().replace(" ", "") in x['name'].lower().replace(" ", ""), clients)),
            "Номера телефонов": list(filter(lambda x: phone in x['phone'], clients)) if (phone := re.sub(r"[^0-9]", "", input)) != "" else [],
            "Коды": list(filter(lambda x: str(x['public_id']).startswith(input), clients)) if input.isdigit() else []
        }
    else:
        result = {}

    t = Template(content)
    return HTMLResponse(t.render(coffee_limit=coffee_limit, results=result, input=input))


@app.get("/config")
async def files(key: str, value: str):
    conf = session.query(Conf).filter(Conf.key == key).first()
    if not conf:
        conf = Conf(key=key, value=value)
        session.add(conf)
    else: conf.value = value
    session.commit()
    return 200

@app.get("/settings", response_class=HTMLResponse)
async def settings():
    with open(os.path.join(os.getcwd(), "www", "settings.jinja"), encoding="utf-8") as f:
        content = f.read()

    config = session.query(Conf).all()
    config: dict[str, str] = {c.key: c.value for c in config}


    fields = {
        "coffee_limit": {"name": "Лимит кофе", "value": c if (c := config.get("coffee_limit", 6)) != '' else 6, "type": "int"},
        "sort_by_name": {"name": "Сортировать по имени", "value": int(config.get("sort_by_name", 1)), "type": "radio:sort"},
        "sort_by_date": {"name": "Сначала недвание", "value": int(config.get("sort_by_date", 0)), "type": "radio:sort"},
        "pin_bonus_coffee": {"name": "Закрепить бонус кофе", "value": int(config.get("pin_bonus_coffee", 1)), "type": "checkbox"},
        "login": {"name": "Логин", "value": config.get("login", ""), "type": "text"},
        "password": {"name": "Пароль", "value": config.get("password", ""), "type": "text"}
    }

    t = Template(content)
    return HTMLResponse(t.render(fields=fields))
