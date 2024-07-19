from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, create_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.sql import func
from fastapi import FastAPI, Depends
from fastapi_admin.factory import app as admin_app
from fastapi_admin.providers.login import UsernamePasswordProvider
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String, unique=True)
    user_full_name = Column(String)
    user_mail = Column(String)
    user_role = Column(String)
    user_auth_type = Column(String)
    user_status = Column(String)
    user_password = Column(String)
    salt = Column(String)
    last_device_id = Column(String)
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    bad_tries = Column(Integer)

class Equipment(Base):
    __tablename__ = 'equipment'
    equipment_id = Column(Integer, primary_key=True)
    group_id = Column(Integer)
    equipment_name = Column(String)
    equipment_status = Column(String)
    plan_val = Column(Integer)
    mac_address = Column(String)
    use_align_filter = Column(Boolean)
    align_filter_secs = Column(Integer)
    std_window_secs = Column(Integer)
    sort_order = Column(Integer)
    created_time = Column(DateTime, default=func.now())
    updated_time = Column(DateTime, default=func.now(), onupdate=func.now())

class AlertsSubscription(Base):
    __tablename__ = 'alerts_subscription'
    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey('equipment.equipment_id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    active = Column(Boolean)
    subscribe_time = Column(DateTime)
    unsubscribe_time = Column(DateTime)
    minutes_to_live = Column(Integer)
    subscribe_action = Column(String)
    user = relationship("User", back_populates="alerts")
    equipment = relationship("Equipment", back_populates="alerts")

class Workflow(Base):
    __tablename__ = 'workflow'
    equipment_id = Column(Integer, ForeignKey('equipment.equipment_id'), primary_key=True)
    start_id = Column(Integer)
    stop_id = Column(Integer)
    answer_id = Column(Integer, ForeignKey('answers_list.answer_id'))
    is_alerted = Column(Boolean)

class AnswersCategory(Base):
    __tablename__ = 'answers_categories'
    answer_category = Column(Integer, primary_key=True)
    name = Column(String)

class AnswersList(Base):
    __tablename__ = 'answers_list'
    answer_id = Column(Integer, primary_key=True)
    answer_text = Column(String(400))
    answer_action = Column(Integer)
    is_system = Column(Boolean)
    answer_category = Column(Integer, ForeignKey('answers_categories.answer_category'))
    answer_color = Column(Text)

# Установление связей
User.alerts = relationship("AlertsSubscription", back_populates="user")
Equipment.alerts = relationship("AlertsSubscription", back_populates="equipment")
Equipment.workflows = relationship("Workflow", foreign_keys="[Workflow.equipment_id]")
AnswersCategory.answers = relationship("AnswersList", back_populates="answer_category")
AnswersList.workflows = relationship("Workflow", back_populates="answer")

# Настройка FastAPI и FastAPI Admin
app = FastAPI(title="Production Management System")

@app.on_event("startup")
async def startup():
    engine = create_engine("postgresql://user:password@localhost/dbname")
    Base.metadata.create_all(engine)  # Создает таблицы, если они еще не созданы
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    await admin_app.configure(
        admin_secret="YOUR_SECRET_KEY",
        login_provider=UsernamePasswordProvider(
            username_field='user_name',
            password_field='user_password',
            pwd_context=None,  # Мы будем использовать нашу собственную функцию для проверки паролей
            verify_password=verify_password
        ),
        session=session
    )

app.mount("/admin", admin_app)

# Проверка паролей
def verify_password(plain_password, hashed_password):
    return check_password_hash(hashed_password, plain_password)

def get_password_hash(password):
    return generate_password_hash(password)


"""import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)"""
