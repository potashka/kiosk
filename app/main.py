# app/main.py
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .dependencies import get_db
from .database import engine
from .models import Base, UserEquipment

app = FastAPI()

# Создание таблиц
Base.metadata.create_all(engine)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    query = "SELECT * FROM users WHERE username = :username AND password = :password"  # noqa
    result = db.execute(
        query, {'username': username, 'password': password}
    ).fetchone()
    if result:
        return {"user_id": result.user_id}
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")


@app.get("/equipment/")
def list_equipment(db: Session = Depends(get_db)):
    result = db.execute("SELECT * FROM equipment")
    return [dict(row) for row in result]


@app.get("/login/", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard/", response_class=HTMLResponse)
def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.post("/start_shift/")
async def start_shift(user_id: int, db: Session = Depends(get_db)):
    current_time = datetime.now()
    db.execute(
        "INSERT INTO user_sessions (user_id, check_in_time) VALUES (:user_id, :time)",  # noqa
        {'user_id': user_id, 'time': current_time}
    )
    db.commit()
    return {"message": "Shift started", "time": current_time}


@app.post("/end_shift/")
async def end_shift(user_id: int, db: Session = Depends(get_db)):
    current_time = datetime.now()
    db.execute(
        "UPDATE user_sessions SET check_out_time = :time WHERE user_id = :user_id",  # noqa
        {'time': current_time, 'user_id': user_id}
    )
    db.commit()
    return {"message": "Shift ended", "time": current_time}


@app.post("/assign_downtime/")
async def assign_downtime(
    user_id: int, downtime_id: int, type_id: int, db: Session = Depends(get_db)
):
    db.execute(
        "UPDATE workflow SET answer_id = :type_id WHERE id = :downtime_id AND equipment_id IN (SELECT equipment_id FROM user_equipment WHERE user_id = :user_id)",  # noqa
        {'type_id': type_id, 'downtime_id': downtime_id, 'user_id': user_id}
    )
    db.commit()
    return {
        "message": "Downtime assigned",
        "downtime_id": downtime_id,
        "type_id": type_id
    }


@app.post("/assign_equipment/")
async def assign_equipment(
    user_id: int, equipment_id: int, db: Session = Depends(get_db)
):
    new_assignment = UserEquipment(
        user_id=user_id, equipment_id=equipment_id, start_time=datetime.now()
    )
    db.add(new_assignment)
    db.commit()
    return {
        "message": "Equipment assigned successfully",
        "user_id": user_id,
        "equipment_id": equipment_id
    }


@app.post("/release_equipment/")
async def release_equipment(
    user_id: int, equipment_id: int, db: Session = Depends(get_db)
):
    assignment = db.query(UserEquipment).filter(
        UserEquipment.user_id == user_id,
        UserEquipment.equipment_id == equipment_id
    ).first()
    if assignment:
        assignment.end_time = datetime.now()
        db.commit()
        return {
            "message": "Equipment released",
            "user_id": user_id,
            "equipment_id": equipment_id
        }
    else:
        raise HTTPException(status_code=404, detail="Assignment not found")
