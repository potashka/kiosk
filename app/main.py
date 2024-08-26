# app/main.py
from datetime import datetime, timezone, timedelta
from fastapi import (
    FastAPI, Depends, Form, HTTPException,
    Query, Request, status
)
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

KALININGRAD_TZ = timezone(timedelta(hours=2))
USER_ROLE = 1
PAGE_SIZE = 5
PAGE = 1

class DowntimeUpdateRequest(BaseModel):
    """Модель для обновления информации о простое оборудования."""
    answer_id: int


def convert_timestamp(ts):
    """Конвертация времени из  int"""
    if ts:
        dt = datetime.fromtimestamp(ts / 1000, tz=KALININGRAD_TZ)
        return dt.strftime("%H:%M:%S %d-%m-%Y")
    return "Unknown"


@app.get("/")
async def welcome(request: Request):
    """Отображает приветственную страницу с ссылкой на выбор группы."""
    return templates.TemplateResponse("welcome.html", {"request": request})


@app.get("/select-group")
async def select_group(request: Request, db: AsyncSession = Depends(get_db)):
    """Возвращает список доступных групп пользователей."""
    query = text("SELECT group_id, group_name FROM groups")
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
    query = text("""
        SELECT users.user_id, users.user_name, users.user_full_name
        FROM users
        JOIN users_groups ON users.user_id = users_groups.user_id
        WHERE users_groups.group_id = :group_id
    """)
    async with db.begin():
        result = await db.execute(query, {'group_id': group_id})
        users = result.fetchall()

    user_data = [
        {"user_name": user.user_name, "user_full_name": user.user_full_name} for user in users
    ]

    return templates.TemplateResponse(
        "select_user.html",
        {"request": request,"users": user_data, "group_id": group_id}
    )


@app.get("/login")
async def login_form(request: Request):
    """Предоставляет форму входа."""
    username = request.query_params.get('username')
    group_id = request.session.get('group_id')
    return templates.TemplateResponse(
        "login.html", {"request": request, "username": username, "group_id": group_id}
    )


@app.post("/login")
async def login(
    request: Request, username: str = Form(...),
    password: str = Form(...), group_id: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
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
        error_message = "Неверное имя пользователя или пароль"
        return templates.TemplateResponse(
            "login.html", {
                "request": request, "error_message": error_message,
                "username": username, "group_id": group_id
            }
        )
        # raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

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


def get_current_user(request: Request):
    """Извлекает и возвращает ID текущего пользователя из сессии."""
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(status_code=400, detail="Пользователь не вошел в систему")
    return user_id


@app.get("/dashboard/{group_id}")
async def dashboard(request: Request, group_id: int, db: AsyncSession = Depends(get_db)):
    """Отображает панель управления, показывая все оборудование, связанное с выбранной группой."""
    # Получаем текущего пользователя
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=400, detail="Пользователь не найден")

    # Получаем имя текущего пользователя
    user_query = text("SELECT user_name FROM users WHERE user_id = :user_id")
    # Получаем список оборудования
    equipment_query = text("SELECT * FROM equipment WHERE group_id = :group_id")
    async with db.begin():
        user_result = await db.execute(user_query, {'user_id': user_id})
        user_name = user_result.scalar()
        result = await db.execute(equipment_query, {'group_id': group_id})
        equipments = result.fetchall()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "equipments": equipments,
            "group_id": group_id,
            "user_name": user_name,  # Передаем имя пользователя в шаблон
            "PAGE": PAGE,
            "PAGE_SIZE": PAGE_SIZE
        }
    )


@app.get("/equipment/{group_id}")
async def get_equipment(group_id: int, db: AsyncSession = Depends(get_db)):
    """
    Возвращает список оборудования вместе с их текущим статусом в выбранной группе,
    включая пользователя.
    """
    equipment_query = text("""
        SELECT e.equipment_id, e.equipment_name, COALESCE(a.active, FALSE) AS active, u.user_name
        FROM equipment e
        LEFT JOIN alerts_subscription a ON e.equipment_id = a.equipment_id AND a.active = TRUE
        LEFT JOIN users u ON a.user_id = u.user_id
        WHERE e.group_id = :group_id
    """)
    async with db.begin():
        result = await db.execute(equipment_query, {'group_id': group_id})
        equipments = result.all()

    # Обработка результатов как списка словарей
    equipment_list = [
        {"id": eq[0], "name": eq[1], "active": eq[2], "user_name": eq[3]}
        for eq in equipments
    ]
    return equipment_list


async def can_toggle_equipment(user_id: str, equipment_id: int, db: AsyncSession):
    """
    Функция для проверки, может ли пользователь переключить статус оборудования.
    """
    async with db.begin():  # Начинаем транзакцию для проверки прав
        # Получаем роль текущего пользователя
        user_role_query = text("""
            SELECT user_role FROM users
            WHERE user_id = :user_id
        """)
        user_role_result = await db.execute(user_role_query, {'user_id': user_id})
        user_role = user_role_result.scalar()

        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден."
            )

        # Проверяем, занят ли станок другим пользователем
        occupation_check_query = text("""
            SELECT a.id, a.user_id, u.user_name FROM alerts_subscription a
            JOIN users u ON a.user_id = u.user_id
            WHERE a.equipment_id = :equipment_id AND a.active = TRUE
            LIMIT 1
        """)
        occupation_check_result = await db.execute(occupation_check_query, {'equipment_id': equipment_id})
        occupation = occupation_check_result.fetchone()

        # Если оборудование уже занято другим пользователем, проверяем роль текущего пользователя
        if occupation:
            occupied_by_user_id = occupation.user_id
            occupied_by_user_name = occupation.user_name

            # Проверяем, имеет ли текущий пользователь права на изменение статуса
            if occupied_by_user_id != user_id and user_role != USER_ROLE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Оборудование занято пользователем {occupied_by_user_name}. У вас нет прав на его переключение."
                )

    return True


@app.post("/toggle-equipment/{equipment_id}")
async def toggle_equipment(
    equipment_id: int,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Переключает статус активности оборудования для пользователя."""

    # Проверяем, может ли текущий пользователь переключить оборудование
    await can_toggle_equipment(user_id, equipment_id, db)

    # Теперь переключаем оборудование
    async with db.begin():  # Начинаем транзакцию только для изменения статуса оборудования
        # Проверяем, занят ли станок кем-либо
        occupation_check_query = text("""
            SELECT a.id, a.user_id, u.user_name FROM alerts_subscription a
            JOIN users u ON a.user_id = u.user_id
            WHERE a.equipment_id = :equipment_id AND a.active = TRUE
            LIMIT 1
        """)
        occupation_check_result = await db.execute(occupation_check_query, {'equipment_id': equipment_id})
        occupation = occupation_check_result.fetchone()

        if occupation:
            occupied_by_user_id = occupation.user_id

            if occupied_by_user_id == user_id:
                # Если текущий пользователь занял оборудование, освобождаем его
                deactivate_query = text("""
                    UPDATE alerts_subscription
                    SET active = FALSE, unsubscribe_time = timezone('utc', now())
                    WHERE id = :subscription_id
                """)
                await db.execute(deactivate_query, {'subscription_id': occupation.id})
                active_status = False
            else:
                # Если текущий пользователь - мастер, освобождаем предыдущее занятие и занимаем оборудование
                deactivate_query = text("""
                    UPDATE alerts_subscription
                    SET active = FALSE, unsubscribe_time = timezone('utc', now())
                    WHERE id = :subscription_id
                """)
                await db.execute(deactivate_query, {'subscription_id': occupation.id})

                activate_query = text("""
                    INSERT INTO alerts_subscription (equipment_id, user_id, active, subscribe_time, minutes_to_live)
                    VALUES (:equipment_id, :user_id, TRUE, timezone('utc', now()), 480)
                """)
                await db.execute(activate_query, {'equipment_id': equipment_id, 'user_id': user_id})
                active_status = True
        else:
            # Если оборудование не занято, занимаем его текущим пользователем
            activate_query = text("""
                INSERT INTO alerts_subscription (equipment_id, user_id, active, subscribe_time, minutes_to_live)
                VALUES (:equipment_id, :user_id, TRUE, timezone('utc', now()), 480)
            """)
            await db.execute(activate_query, {'equipment_id': equipment_id, 'user_id': user_id})
            active_status = True

        await db.commit()  # Завершаем транзакцию

    return {"status": "success", "active": active_status, "equipment_id": equipment_id}


@app.get("/downtimes/{equipment_id}")
async def get_downtimes(
    equipment_id: int,
    page: int = Query(PAGE, alias="page", ge=PAGE),
    page_size: int = Query(PAGE_SIZE, alias="page_size", ge=PAGE),
    db: AsyncSession = Depends(get_db)
):
    """Получает список всех простоев для указанного оборудования с постраничным выводом."""
    
    offset = (page - 1) * page_size

    query = text("""
        SELECT w.equipment_id, w.start_id, w.stop_id, w.answer_id, al.answer_text
        FROM workflow w
        LEFT JOIN answers_list al ON w.answer_id = al.answer_id
        WHERE w.equipment_id = :equipment_id
        ORDER BY w.start_id DESC
        LIMIT :limit OFFSET :offset
    """)
    async with db.begin():
        result = await db.execute(query, {
            'equipment_id': equipment_id,
            'limit': page_size,
            'offset': offset
        })
        downtimes = result.all()

    return [
        {
            'equipment_id': dt.equipment_id,
            'start_id': dt.start_id,  # Сохраняем как int
            'start_time': convert_timestamp(dt.start_id),  # Для отображения
            'stop_id': dt.stop_id,
            'stop_time': convert_timestamp(dt.stop_id),  # Для отображения
            'answer_id': dt.answer_id,
            'answer_text': dt.answer_text if dt.answer_id else None
        }
        for dt in downtimes
    ]



@app.post("/update-downtime/{equipment_id}/{start_id}")
async def update_downtime(
    equipment_id: int, start_id: int,
    request: DowntimeUpdateRequest, db: AsyncSession = Depends(get_db)
):
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
