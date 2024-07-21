# coding: utf-8
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import BigInteger, Boolean, CHAR, Column, DateTime, Float, ForeignKey, Index, Integer, SmallInteger, String, Table, Text, Time, text
from sqlalchemy.dialects.postgresql import OID, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()
metadata = Base.metadata


class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(BigInteger, primary_key=True)
    equipment_id = Column(Integer, nullable=False)
    start_id = Column(BigInteger, nullable=False)
    user_id = Column(CHAR(32), nullable=False)
    open_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    close_time = Column(DateTime)
    answer_id = Column(Integer)
    alarm_type = Column(Integer, nullable=False, default=0)
    minutes_to_live = Column(Integer, default=30)


class AlertsSubscription(Base):
    __tablename__ = 'alerts_subscription'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id = Column(Integer, nullable=False)
    user_id = Column(CHAR(32), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    subscribe_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    unsubscribe_time = Column(DateTime)
    minutes_to_live = Column(Integer, nullable=False, default=480)
    subscribe_action = Column(Integer)


class AnswersCategory(Base):
    __tablename__ = 'answers_categories'

    answer_category = Column(Integer, primary_key=True)
    name = Column(Text)


class Equipment(Base):
    __tablename__ = 'equipment'

    equipment_id = Column(Integer, primary_key=True)
    group_id = Column(Integer)
    equipment_name = Column(String(200))
    equipment_status = Column(Integer, nullable=False, default=0)
    plan_val = Column(Float)
    mac_address = Column(String(50))
    use_align_filter = Column(Boolean, default=False)
    align_filter_secs = Column(BigInteger, default=15)
    std_window_secs = Column(BigInteger, default=5)
    sort_order = Column(Integer, default=0)


class Workflow(Base):
    __tablename__ = 'workflow'

    equipment_id = Column(BigInteger, primary_key=True, nullable=False)
    start_id = Column(BigInteger, primary_key=True, nullable=False)
    stop_id = Column(BigInteger)
    answer_id = Column(Integer, default=0)
    is_alerted = Column(Boolean, default=False)


class AnswersList(Base):
    __tablename__ = 'answers_list'

    answer_id = Column(Integer, primary_key=True)
    answer_text = Column(String(400), nullable=False)
    answer_action = Column(SmallInteger)
    is_system = Column(Boolean, default=False)
    answer_category = Column(ForeignKey('answers_categories.answer_category'), nullable=False, index=True, default=1)
    answer_color = Column(Text, nullable=False, default='#BDF4A8')

    answers_category = relationship('AnswersCategory')


class Group(Base):
    __tablename__ = 'groups'

    group_id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)
    group_name = Column(String(200))
    group_status = Column(Integer, nullable=False, default=1)


class User(Base):
    __tablename__ = 'users'

    user_id = Column(CHAR(32), primary_key=True)
    user_name = Column(String(50))
    user_full_name = Column(String(250))
    user_mail = Column(String(250))
    user_role = Column(Integer, nullable=False, default=0)
    user_auth_type = Column(Integer, nullable=False, default=0)
    user_status = Column(Integer, nullable=False, default=1)
    user_password = Column(String(400))
    salt = Column(String(400))
    last_device_id = Column(String(400))
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)
    bad_tries = Column(SmallInteger, nullable=False, default=0)


class UsersGroup(Base):
    __tablename__ = 'users_groups'

    user_id = Column(ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
    group_id = Column(ForeignKey('groups.group_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
    user_role = Column(Integer, nullable=False, default=0)

    group = relationship('Group')
    user = relationship('User')