# app/main.py
"""
Модуль `main.py` является основной точкой входа для приложения на базе FastAPI.

Функции и маршруты, определенные в этом модуле, предоставляют интерфейс для работы с пользователями,
оборудованием и простоями на производстве. Модуль включает аутентификацию пользователей, выбор
производственного цеха, работу с сессиями и отображение информации через HTML-шаблоны.

Основные компоненты:
- FastAPI приложение и его конфигурация.
- Маршруты для обработки запросов пользователей, включая выбор группы (цеха), выбор пользователя и
  аутентификацию.
- Функции для работы с базой данных через SQLAlchemy, включая асинхронные запросы и транзакции.
- Обработка сессий пользователей и хранение информации о текущем состоянии в сессии.
- Шаблоны Jinja2 для отображения страниц пользователям.

Модуль использует следующие ключевые библиотеки:
- FastAPI: Основной веб-фреймворк для создания RESTful API.
- SQLAlchemy: ORM для взаимодействия с базой данных.
- Jinja2: Шаблонизатор для рендеринга HTML-страниц.
- Starlette: Для работы с сессиями и статическими файлами.
- Pydantic: Для валидации данных, поступающих в запросах.
- Werkzeug: Для обработки хеширования паролей.

Общие шаги, которые выполняет модуль:
1. Инициализация приложения FastAPI с подключением middleware для сессий.
2. Обработка GET и POST запросов для различных страниц, таких как выбор группы, выбор пользователя,
   панель управления, и т.д.
3. Взаимодействие с базой данных для извлечения и обновления данных
о пользователях, оборудовании и простоях.
4. Управление сессиями для хранения информации о текущем пользователе и выбранной группе.
"""
import os
from datetime import datetime, timezone, timedelta
from fastapi import (
    FastAPI, Depends, Form, HTTPException,
    Query, Request, status
)
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
from werkzeug.security import check_password_hash

# from app.database import engine
from app.dependencies import get_db
from app.logging_config import logger

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

KALININGRAD_TZ = timezone(timedelta(hours=2))
# переменная для доп. прав пользователям,  не являющимся операторами, на изменение статуса оборудования
USER_ROLE = 1
PAGE_SIZE = 4
PAGE = 1

class DowntimeUpdateRequest(BaseModel):
    """Модель для обновления информации о простое оборудования."""
    answer_id: int


def convert_timestamp(ts):
    """Конвертация времени из  int"""
    if ts:
        dt = datetime.fromtimestamp(ts, tz=KALININGRAD_TZ)
        return dt.strftime("%H:%M:%S %d-%m-%Y")
    return "Unknown"


def get_default_group_id():
    """Функция для получения group_id из переменной окружения"""
    group_id = os.getenv("GROUP_ID")
    if group_id:
        logger.info("Получен GROUP_ID из переменной окружения: %s", group_id)
    else:
        logger.warning("GROUP_ID не установлен в переменных окружения")
    return group_id


@app.get("/")
async def welcome(request: Request):
    """
    Отображает приветственную страницу или перенаправляет на выбор пользователя,
    если group_id установлен.
    """
    logger.info("Отображение приветственной страницы")
    group_id = get_default_group_id()
    if group_id:
        # Если group_id установлен, сохраняем его в сессии и перенаправляем на выбор пользователя
        logger.info("Перенаправление на выбор пользователя с group_id=%s", group_id)
        request.session['group_id'] = int(group_id)
        return RedirectResponse(url="/select-user", status_code=303)
    else:
        # Если group_id не установлен, отображаем приветственную страницу
        logger.info("Отображение приветственной страницы без group_id")
        return templates.TemplateResponse("welcome.html", {"request": request})


@app.get("/auto-set-group")
async def auto_set_group(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Получаем group_id из переменной окружения
    и перенаправляем на выбор пользователя, если установлен
    """
    logger.info("Автоматическая установка group_id")
    group_id = get_default_group_id()
    if group_id:
        logger.info("group_id найден в окружении %s:", group_id)
        request.session['group_id'] = int(group_id)
        return RedirectResponse(url="/select-user", status_code=303)
    else:
        logger.warning("group_id не найден в окружении")
        return RedirectResponse(url="/select-group", status_code=303)


@app.get("/select-group")
async def select_group(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Возвращает список доступных групп пользователей или
    перенаправляет на выбор пользователя, если group_id уже установлен.
    """
    logger.info("Получение списка доступных групп")
    query = text("SELECT group_id, group_name FROM groups")
    async with db.begin():
        result = await db.execute(query)
        groups = result.all()

    return templates.TemplateResponse("select_group.html", {"request": request, "groups": groups})


@app.post("/set-group")
async def set_group(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Устанавливает группу пользователя в сессии и
    перенаправляет на страницу выбора пользователя.
    """
    form = await request.form()
    group_id = form.get("group_id")
    if not group_id:
        logger.error("Не указан ID группы")
        raise HTTPException(status_code=400, detail="Не указан ID группы")
    logger.info("Установка group_id в сессии: %s", group_id)
    request.session['group_id'] = int(group_id)
    return RedirectResponse(url="/select-user", status_code=303)


@app.get("/select-user")
async def select_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Возвращает страницу для выбора пользователя на основе выбранной группы."""
    group_id = request.session.get('group_id')
    logger.info("Выбор пользователя для group_id: %s", group_id)
    # auto_set = group_id == int(os.getenv("GROUP_ID", 0))
    # Проверяем, был ли установлен group_id из переменной окружения
    # Получаем значение group_id из переменной окружения как строку и преобразуем в int
    env_group_id = os.getenv("GROUP_ID")
    if env_group_id is not None:
        env_group_id = int(env_group_id)
    # Проверяем, был ли установлен group_id из переменной окружения
    auto_set = group_id == env_group_id
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
        {"request": request, "users": user_data, "group_id": group_id, "auto_set": auto_set}
    )


@app.get("/login")
async def login_form(request: Request):
    """Предоставляет форму входа."""
    username = request.query_params.get('username')
    group_id = request.session.get('group_id')
    logger.info("Отображение формы входа для пользователя %s в группе %s", username, group_id)
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
    logger.info("Попытка входа пользователя %s в группу %s", username, group_id)
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
        logger.warning(
            "Ошибка аутентификации для пользователя %s: %s", username, error_message
        )
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
    logger.info("Пользователь %s успешно аутентифицирован", username)
    return RedirectResponse(url=f"/dashboard/{group_id}", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    """Выход пользователя и очистка сессии."""
    logger.info("Пользователь выходит из системы")
    request.session.clear()
    return RedirectResponse(url='/', status_code=303)


def get_current_user(request: Request):
    """Извлекает и возвращает ID текущего пользователя из сессии."""
    user_id = request.session.get('user_id')
    if not user_id:
        logger.error("Пользователь не вошел в систему")
        raise HTTPException(status_code=400, detail="Пользователь не вошел в систему")
    return user_id


@app.get("/dashboard/{group_id}")
async def dashboard(request: Request, group_id: int, db: AsyncSession = Depends(get_db)):
    """Отображает панель управления, показывая все оборудование, связанное с выбранной группой."""
    logger.info("Отображение панели управления для group_id: %s", group_id)
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
async def get_equipment(
    group_id: int,
    page: int = Query(PAGE, alias="page", ge=PAGE),
    page_size: int = Query(PAGE_SIZE, alias="page_size", ge=PAGE),
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает список оборудования с постраничным выводом для выбранной группы.
    """
    logger.info(
        "Получение списка оборудования для group_id: %s, страница: %s, размер страницы: %s",
        group_id,
        page,
        page_size
    )
    offset = (page - 1) * page_size

    # Запрос для получения общего количества записей
    count_query = text("""
        SELECT COUNT(*)
        FROM equipment
        WHERE group_id = :group_id
    """)
    async with db.begin():
        count_result = await db.execute(count_query, {'group_id': group_id})
        total_records = count_result.scalar()  # Получаем общее количество записей

    total_pages = (total_records + page_size - 1) // page_size  # Рассчитываем количество страниц

    equipment_query = text("""
        SELECT e.equipment_id, e.equipment_name, COALESCE(a.active, FALSE) AS active, u.user_name
        FROM equipment e
        LEFT JOIN alerts_subscription a ON e.equipment_id = a.equipment_id AND a.active = TRUE
        LEFT JOIN users u ON a.user_id = u.user_id
        WHERE e.group_id = :group_id
        ORDER BY e.equipment_id DESC
        LIMIT :limit OFFSET :offset
    """)
    async with db.begin():
        result = await db.execute(
            equipment_query,
            {'group_id': group_id, 'limit': page_size, 'offset': offset}
        )
        equipments = result.all()

    logger.info(
        "Список оборудования получен для group_id: %s, количество записей: %s",
        group_id,
        len(equipments)
    )
    equipment_list = [
        {"id": eq[0], "name": eq[1], "active": eq[2], "user_name": eq[3]}
        for eq in equipments
    ]
    return {
        "equipments": equipment_list,
        "current_page": page,
        "total_pages": total_pages
    }


async def can_toggle_equipment(user_id: str, equipment_id: int, db: AsyncSession):
    """
    Функция для проверки, может ли пользователь переключить статус оборудования.
    """
    logger.info(
        "Проверка прав пользователя user_id: %s на переключение оборудования equipment_id: %s",
        user_id,
        equipment_id
    )
    async with db.begin():  # Начинаем транзакцию для проверки прав
        # Получаем роль текущего пользователя
        user_role_query = text("""
            SELECT user_role FROM users
            WHERE user_id = :user_id
        """)
        user_role_result = await db.execute(user_role_query, {'user_id': user_id})
        user_role = user_role_result.scalar()

        if user_role is None:
            logger.error("Пользователь user_id: %s не найден", user_id)
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
        occupation_check_result = await db.execute(
            occupation_check_query, {'equipment_id': equipment_id}
        )
        occupation = occupation_check_result.fetchone()

        # Если оборудование уже занято другим пользователем, проверяем роль текущего пользователя
        if occupation:
            occupied_by_user_id = occupation.user_id
            occupied_by_user_name = occupation.user_name
            logger.info(
                "Оборудование занято пользователем %s (user_id: %s)",
                occupied_by_user_name,
                occupied_by_user_id
            )

            # Проверяем, имеет ли текущий пользователь права на изменение статуса
            if occupied_by_user_id != user_id and user_role != USER_ROLE:
                logger.warning(
                    "Пользователь user_id: %s не имеет прав на переключение оборудования",
                    user_id
                )
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
    logger.info(
        "Переключение статуса оборудования equipment_id: %s пользователем user_id: %s",
        equipment_id,
        user_id
    )

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
        occupation_check_result = await db.execute(
            occupation_check_query, {'equipment_id': equipment_id}
        )
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
                logger.info(
                    "Оборудование equipment_id: %s освобождено пользователем user_id: %s",
                    equipment_id,
                    user_id
                )
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
                logger.info(
                    "Оборудование equipment_id: %s занято пользователем user_id: %s",
                    equipment_id,
                    user_id
                )
        else:
            # Если оборудование не занято, занимаем его текущим пользователем
            activate_query = text("""
                INSERT INTO alerts_subscription (equipment_id, user_id, active, subscribe_time, minutes_to_live)
                VALUES (:equipment_id, :user_id, TRUE, timezone('utc', now()), 480)
            """)
            await db.execute(activate_query, {'equipment_id': equipment_id, 'user_id': user_id})
            active_status = True
            logger.info(
                "Оборудование equipment_id: %s занято пользователем user_id: %s",
                equipment_id,
                user_id
            )

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
    logger.info(
        "Получение списка простоев для оборудования equipment_id: %s, страница: %s, размер страницы: %s",
        equipment_id,
        page,
        page_size
    )

    offset = (page - 1) * page_size

    # Запрос для получения общего количества простоев
    count_query = text("""
        SELECT COUNT(*)
        FROM workflow
        WHERE equipment_id = :equipment_id
    """)
    async with db.begin():
        count_result = await db.execute(count_query, {'equipment_id': equipment_id})
        total_records = count_result.scalar()  # Получаем общее количество простоев

    total_pages = (total_records + page_size - 1) // page_size  # Рассчитываем количество страниц

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
        
    logger.info(
        "Список простоев получен для equipment_id: %s, количество записей: %s",
        equipment_id,
        len(downtimes)
    )

    return {
        "downtimes": [
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
        ],
        "current_page": page,
        "total_pages": total_pages
    }


@app.post("/update-downtime/{equipment_id}/{start_id}")
async def update_downtime(
    equipment_id: int, start_id: int,
    request: DowntimeUpdateRequest, db: AsyncSession = Depends(get_db)
):
    """Обновляет информацию о простое, связывая его с ответом оператора."""
    logger.info(
        "Обновление простоя для оборудования equipment_id: %s, start_id: %s",
        equipment_id,
        start_id
    )
    query = text("""
        UPDATE workflow 
        SET answer_id = :answer_id 
        WHERE equipment_id = :equipment_id AND start_id = :start_id 
        RETURNING equipment_id, start_id, stop_id, answer_id
    """)
    async with db.begin():
        result = await db.execute(
            query,
            {'answer_id': request.answer_id, 'equipment_id': equipment_id, 'start_id': start_id}
        )
        downtime = result.mappings().first()  # Используем mappings(), чтобы получить результат в виде словаря

    if downtime:
        # Возвращаем информацию об обновлённом простое
        logger.info(
            "Простой обновлен для equipment_id: %s, start_id: %s", equipment_id, start_id
        )
        return {
            "status": "success",
            "message": "Простой обновлен",
            "data": downtime  # Отправляем данные как словарь
        }
    else:
        # Если строка не была найдена или обновлена, возвращаем ошибку
        logger.error(
            "Простой не найден для equipment_id: %s, start_id: %s", equipment_id, start_id
        )
        raise HTTPException(status_code=404, detail="Простой не найден")


@app.get("/answers")
async def get_answers(db: AsyncSession = Depends(get_db)):
    """Возвращает список всех доступных ответов для использования в системе."""
    logger.info("Получение списка всех доступных ответов")
    query = text("SELECT answer_id, answer_text FROM answers_list")
    async with db.begin():
        result = await db.execute(query)
        answers = result.all()  # Получаем все строки, каждая строка будет в виде кортежа
    logger.info("Получено %d ответов", len(answers))
    # Преобразуем каждую строку (кортеж) в словарь
    return [{'answer_id': ans[0], 'answer_text': ans[1]} for ans in answers]
