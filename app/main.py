# app/main.py
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from werkzeug.security import check_password_hash

from app.database import engine
from app.dependencies import get_db
from app.models import (
    Base, Group, User, Equipment,
    AlertsSubscription, Workflow, AnswersList, UsersGroup
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создаёт и удаляет ресурсы при старте и завершении приложения."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class DowntimeUpdateRequest(BaseModel):
    """Модель запроса для обновления информации о простое оборудования."""
    answer_id: int


@app.get("/")
async def welcome(request: Request):
    """Отображает приветственную страницу с ссылкой на выбор группы."""
    return templates.TemplateResponse("welcome.html", {"request": request})


@app.get("/select-group")
async def select_group(request: Request, db: AsyncSession = Depends(get_db)):
    """Возвращает список доступных групп пользователей."""
    async with db.begin():
        result = await db.execute(select(Group))
        groups = result.scalars().all()
    return templates.TemplateResponse("select_group.html", {"request": request, "groups": groups})


@app.post("/set-group")
async def set_group(request: Request, db: AsyncSession = Depends(get_db)):
    """Устанавливает группу пользователя в сессии и перенаправляет на страницу выбора пользователя."""
    form = await request.form()
    group_id_value = form.get("group_id")
    if isinstance(group_id_value, UploadFile):
        raise HTTPException(status_code=400, detail="Invalid input type for group ID")
    group_id_str = str(group_id_value)
    if group_id_str is None:
        raise HTTPException(status_code=400, detail="Group ID not provided")
    try:
        group_id = int(group_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Group ID format")
    request.session['group_id'] = group_id
    return RedirectResponse(url="/select-user", status_code=303)


@app.get("/select-user")
async def select_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Возвращает страницу для выбора пользователя в зависимости от выбранной группы."""
    group_id = request.session.get('group_id')
    if not group_id:
        raise HTTPException(status_code=400, detail="Группа не выбрана")
    async with db.begin():
        result = await db.execute(select(User).join(UsersGroup).filter(UsersGroup.group_id == group_id))
        users = result.scalars().all()
    return templates.TemplateResponse("select_user.html", {"request": request, "users": users, "group_id": group_id})


@app.get("/login")
async def login_form(request: Request):
    """Представляет форму входа."""
    username = request.query_params.get('username')
    if not username:
        raise HTTPException(status_code=400, detail="Пользователь не выбран")
    group_id = request.session.get('group_id')
    return templates.TemplateResponse("login.html", {"request": request, "username": username, "group_id": group_id})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), group_id: int = Form(...), db: AsyncSession = Depends(get_db)):
    """Аутентификация пользователя и установка сессии после успешного входа."""
    async with db.begin():
        result = await db.execute(select(User).join(UsersGroup, UsersGroup.user_id == User.user_id).filter(User.user_name == username, UsersGroup.group_id == group_id))
        user = result.scalars().first()
    if not user or not check_password_hash(user.user_password, password):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    request.session['user_id'] = user.user_id
    request.session['group_id'] = group_id
    return RedirectResponse(url=f"/dashboard/{group_id}", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    """Логаут пользователя"""
    request.session.clear()  # Очистка сессии
    return RedirectResponse(url='/', status_code=303) 


@app.get("/dashboard/{group_id}")
async def dashboard(request: Request, group_id: int, db: AsyncSession = Depends(get_db)):
    """Отображает панель управления, показывая все оборудование, связанное с выбранной группой."""
    async with db.begin():
        result = await db.execute(select(Equipment).filter(Equipment.group_id == group_id))
        equipments = result.scalars().all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "equipments": equipments, "group_id": group_id})


@app.get("/equipment/{group_id}")
async def get_equipment(group_id: int, db: AsyncSession = Depends(get_db)):
    """Возвращает список оборудования вместе с их текущим статусом в выбранной группе."""
    async with db.begin():
        result = await db.execute(select(Equipment).filter(Equipment.group_id == group_id))
        equipments = result.scalars().all()
    equipment_list = []
    for equipment in equipments:
        subscription_result = await db.execute(
            select(AlertsSubscription)
            .filter(AlertsSubscription.equipment_id == equipment.equipment_id)
            .order_by(AlertsSubscription.subscribe_time.desc())
        )
        subscription = subscription_result.scalars().first()
        equipment_list.append({
            "id": equipment.equipment_id,
            "name": equipment.equipment_name,
            "active": subscription.active if subscription else False
        })
    return equipment_list


def get_current_user(request: Request):
    """Извлекает и возвращает ID текущего пользователя из сессии."""
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(status_code=400, detail="Пользователь не вошел в систему")
    return user_id


@app.post("/toggle-equipment/{equipment_id}")
async def toggle_equipment(equipment_id: int, user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Переключает статус активности оборудования для пользователя."""
    async with db.begin():
        result = await db.execute(
            select(AlertsSubscription)
            .filter(AlertsSubscription.equipment_id == equipment_id, AlertsSubscription.user_id == user_id)
            .order_by(AlertsSubscription.subscribe_time.desc())
        )
        subscription = result.scalars().first()
        if subscription and subscription.active:
            subscription.active = False
            subscription.unsubscribe_time = datetime.now()  # Обновите, если требуется серверное время
        elif subscription:
            subscription.active = True
            subscription.subscribe_time = datetime.now()  # Обновите, если требуется серверное время
        else:
            subscription = AlertsSubscription(
                equipment_id=equipment_id,
                user_id=user_id,
                active=True,
                subscribe_time=datetime.now(),  # Обновите, если требуется серверное время
                minutes_to_live=480
            )
            db.add(subscription)
        await db.commit()
    return {"status": "success", "active": subscription.active, "equipment_id": equipment_id}


@app.get("/downtimes/{equipment_id}")
async def get_downtimes(equipment_id: int, db: AsyncSession = Depends(get_db)):
    """Получает список всех простоев для указанного оборудования."""
    async with db.begin():
        result = await db.execute(select(Workflow).filter(Workflow.equipment_id == equipment_id))
        downtimes = result.scalars().all()
    return [{
        "id": {"equipment_id": downtime.equipment_id, "start_id": downtime.start_id},
        "equipment_id": downtime.equipment_id,
        "start_id": datetime.utcfromtimestamp(downtime.start_id/1000).strftime("%Y-%m-%d %H:%M:%S"),
        "stop_id": datetime.utcfromtimestamp(downtime.stop_id/1000).strftime("%Y-%m-%d %H:%M:%S") if downtime.stop_id else None,
        "answer_id": downtime.answer_id
    } for downtime in downtimes]


@app.post("/update-downtime/{equipment_id}/{start_id}")
async def update_downtime(equipment_id: int, start_id: int, request: DowntimeUpdateRequest, db: AsyncSession = Depends(get_db)):
    """Обновляет информацию о простое, связывая его с ответом оператора."""
    async with db.begin():
        result = await db.execute(
            select(Workflow).filter(Workflow.equipment_id == equipment_id, Workflow.start_id == start_id)
        )
        downtime = result.scalars().first()
    if downtime:
        downtime.answer_id = request.answer_id
        await db.commit()
        return {"status": "success", "message": "Downtime updated"}
    else:
        raise HTTPException(status_code=404, detail="Downtime not found")


@app.get("/answers")
async def get_answers(db: AsyncSession = Depends(get_db)):
    """Возвращает список всех доступных ответов для использования в системе."""
    async with db.begin():
        result = await db.execute(select(AnswersList))
        answers = result.scalars().all()
        response = [{"answer_id": answer.answer_id, "answer_text": answer.answer_text} for answer in answers]
        print("Answers:", response)  # Добавьте логирование для отладки
    return [{"answer_id": answer.answer_id, "answer_text": answer.answer_text} for answer in answers]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
