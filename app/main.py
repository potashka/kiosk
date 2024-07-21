# app/main.py
from datetime import datetime
from fastapi import FastAPI, Depends, Form, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from werkzeug.security import check_password_hash

from app.database import engine
from app.dependencies import get_db

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class DowntimeUpdateRequest(BaseModel):
    """Модель для обновления информации о простое оборудования."""
    answer_id: int


@app.get("/")
async def welcome(request: Request):
    """Отображает приветственную страницу с ссылкой на выбор группы."""
    return templates.TemplateResponse("welcome.html", {"request": request})


@app.get("/select-group")
async def select_group(request: Request, db: AsyncSession = Depends(get_db)):
    """Возвращает список доступных групп пользователей."""
    query = text("SELECT group_id, group_name FROM groups")  # Убедитесь, что поля называются именно так в вашей БД
    async with db.begin():
        result = await db.execute(query)
        groups = result.all()
    return templates.TemplateResponse("select_group.html", {"request": request, "groups": groups})


@app.post("/set-group")
async def set_group(request: Request, db: AsyncSession = Depends(get_db)):
    """Устанавливает группу пользователя в сессии и перенаправляет на страницу выбора пользователя."""
    form = await request.form()
    group_id = form.get("group_id")
    if not group_id:
        raise HTTPException(status_code=400, detail="Не указан ID группы")
    request.session['group_id'] = int(group_id)
    return RedirectResponse(url="/select-user", status_code=303)


@app.get("/select-user")
async def select_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Возвращает страницу для выбора пользователя на основе выбранной группы."""
    group_id = request.session.get('group_id')
    query = text("SELECT users.* FROM users JOIN users_groups ON users.user_id = users_groups.user_id WHERE users_groups.group_id = :group_id")
    async with db.begin():
        result = await db.execute(query, {'group_id': group_id})
        users = result.all()
    return templates.TemplateResponse("select_user.html", {"request": request, "users": users, "group_id": group_id})


@app.get("/login")
async def login_form(request: Request):
    """Предоставляет форму входа."""
    username = request.query_params.get('username')
    group_id = request.session.get('group_id')
    return templates.TemplateResponse("login.html", {"request": request, "username": username, "group_id": group_id})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), group_id: int = Form(...), db: AsyncSession = Depends(get_db)):
    """Аутентификация пользователя и установка сессии после успешного входа."""
    # SQL запрос для получения информации о пользователе и его пароле
    query = text("""
        SELECT users.user_id, users.user_password
        FROM users
        JOIN users_groups ON users.user_id = users_groups.user_id
        WHERE users.user_name = :username AND users_groups.group_id = :group_id
    """)
    async with db.begin():
        result = await db.execute(query, {"username": username, "group_id": group_id})
        user = result.first()

    # Проверяем, существует ли пользователь и верный ли пароль
    if not user or not check_password_hash(user.user_password, password):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    # Установка user_id и group_id в сессию
    request.session['user_id'] = user.user_id
    request.session['group_id'] = group_id

    # Перенаправление пользователя на страницу панели управления
    return RedirectResponse(url=f"/dashboard/{group_id}", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    """Выход пользователя и очистка сессии."""
    request.session.clear()
    return RedirectResponse(url='/', status_code=303)


@app.get("/dashboard/{group_id}")
async def dashboard(request: Request, group_id: int, db: AsyncSession = Depends(get_db)):
    """Отображает панель управления, показывая все оборудование, связанное с выбранной группой."""
    query = text("SELECT * FROM equipment WHERE group_id = :group_id")
    async with db.begin():
        result = await db.execute(query, {'group_id': group_id})
        equipments = result.fetchall()
    return templates.TemplateResponse("dashboard.html", {"request": request, "equipments": equipments, "group_id": group_id})


@app.get("/equipment/{group_id}")
async def get_equipment(group_id: int, db: AsyncSession = Depends(get_db)):
    """Возвращает список оборудования вместе с их текущим статусом в выбранной группе."""
    equipment_query = text("""
        SELECT e.equipment_id, e.equipment_name, COALESCE(a.active, FALSE) AS active
        FROM equipment e
        LEFT JOIN alerts_subscription a ON e.equipment_id = a.equipment_id AND a.active = TRUE
        WHERE e.group_id = :group_id
    """)
    async with db.begin():
        result = await db.execute(equipment_query, {'group_id': group_id})
        equipments = result.all()  # Используем метод all() для получения всех результатов

    # Обработка результатов как списка кортежей
    equipment_list = [
        {"id": eq[0], "name": eq[1], "active": eq[2]}
        for eq in equipments
    ]
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
        # Проверяем текущий статус подписки
        subscription_query = text("""
            SELECT id, active FROM alerts_subscription
            WHERE equipment_id = :equipment_id AND user_id = :user_id
            ORDER BY subscribe_time DESC
            LIMIT 1
        """)
        subscription_result = await db.execute(subscription_query, {'equipment_id': equipment_id, 'user_id': user_id})
        subscription = subscription_result.fetchone()

        if subscription:
            # Получаем значения через RowProxy._mapping для безопасного доступа к данным как к словарю
            subscription_id = subscription._mapping['id']
            current_active = subscription._mapping['active']

            if current_active:
                # Если активная, деактивируем
                update_query = text("""
                    UPDATE alerts_subscription SET active = FALSE, unsubscribe_time = timezone('utc', now())
                    WHERE id = :id
                """)
                await db.execute(update_query, {'id': subscription_id})
                active_status = False
            else:
                # Если неактивная, активируем
                update_query = text("""
                    UPDATE alerts_subscription SET active = TRUE, subscribe_time = timezone('utc', now())
                    WHERE id = :id
                """)
                await db.execute(update_query, {'id': subscription_id})
                active_status = True
        else:
            # Создаем новую подписку
            insert_query = text("""
                INSERT INTO alerts_subscription (equipment_id, user_id, active, subscribe_time, minutes_to_live)
                VALUES (:equipment_id, :user_id, TRUE, timezone('utc', now()), 480)
            """)
            await db.execute(insert_query, {'equipment_id': equipment_id, 'user_id': user_id})
            active_status = True

        await db.commit()

    return {"status": "success", "active": active_status, "equipment_id": equipment_id}


@app.get("/downtimes/{equipment_id}")
async def get_downtimes(equipment_id: int, db: AsyncSession = Depends(get_db)):
    """Получает список всех простоев для указанного оборудования."""
    query = text("""
        SELECT equipment_id, start_id, stop_id, answer_id 
        FROM workflow 
        WHERE equipment_id = :equipment_id
    """)
    async with db.begin():
        result = await db.execute(query, {'equipment_id': equipment_id})
        downtimes = result.all()

    # Используем названия колонок в ответе, как они определены в таблице
    return [
        {'equipment_id': dt.equipment_id, 'start_id': dt.start_id, 'stop_id': dt.stop_id, 'answer_id': dt.answer_id}
        for dt in downtimes
    ]


@app.post("/update-downtime/{equipment_id}/{start_id}")
async def update_downtime(equipment_id: int, start_id: int, request: DowntimeUpdateRequest, db: AsyncSession = Depends(get_db)):
    """Обновляет информацию о простое, связывая его с ответом оператора."""
    query = text("""
        UPDATE workflow 
        SET answer_id = :answer_id 
        WHERE equipment_id = :equipment_id AND start_id = :start_id 
        RETURNING equipment_id, start_id, stop_id, answer_id
    """)
    async with db.begin():
        result = await db.execute(query, {'answer_id': request.answer_id, 'equipment_id': equipment_id, 'start_id': start_id})
        downtime = result.mappings().first()  # Используем mappings(), чтобы получить результат в виде словаря

    if downtime:
        # Возвращаем информацию об обновлённом простое
        return {
            "status": "success",
            "message": "Простой обновлен",
            "data": downtime  # Отправляем данные как словарь
        }
    else:
        # Если строка не была найдена или обновлена, возвращаем ошибку
        raise HTTPException(status_code=404, detail="Простой не найден")


@app.get("/answers")
async def get_answers(db: AsyncSession = Depends(get_db)):
    """Возвращает список всех доступных ответов для использования в системе."""
    query = text("SELECT answer_id, answer_text FROM answers_list")
    async with db.begin():
        result = await db.execute(query)
        answers = result.all()  # Получаем все строки, каждая строка будет в виде кортежа
    # Преобразуем каждую строку (кортеж) в словарь
    return [{'answer_id': ans[0], 'answer_text': ans[1]} for ans in answers]

