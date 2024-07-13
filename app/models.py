# app/models.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base  # , relationship

Base = declarative_base()


class UserSession(Base):
    __tablename__ = 'user_sessions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)


class UserDowntime(Base):
    __tablename__ = 'user_downtimes'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('user_sessions.id'))
    workflow_id = Column(Integer, ForeignKey('workflow.id'))
    type_id = Column(Integer, ForeignKey('answers_list.id'))


class UserEquipment(Base):
    __tablename__ = 'user_equipment'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    equipment_id = Column(Integer, ForeignKey('equipment.id'))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
