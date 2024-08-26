# app/models
# Файл носит справочный характер для настройки SQL запросов
from sqlalchemy import (
    BigInteger, Boolean, CHAR, Column, DateTime,
    Float, ForeignKey, Index, Integer, SmallInteger,
    String, Table, Text, Time, text  # noqa
)
from sqlalchemy.dialects.postgresql import OID, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Alert(Base):
    __tablename__ = 'alerts'
    __table_args__ = (
        Index('unique_equipment_user_start', 'equipment_id', 'start_id', 'user_id', unique=True),
    )

    id = Column(
        BigInteger, primary_key=True,
        server_default=text("nextval('alerts_id_seq'::regclass)")
    )
    equipment_id = Column(Integer, nullable=False)
    start_id = Column(BigInteger, nullable=False)
    user_id = Column(CHAR(32), nullable=False)
    open_time = Column(
        DateTime, nullable=False,
        server_default=text("timezone('utc'::text, now())")
    )
    close_time = Column(DateTime)
    answer_id = Column(Integer)
    alarm_type = Column(Integer, nullable=False, server_default=text("0"))
    minutes_to_live = Column(Integer, server_default=text("30"))


class AlertsSubscription(Base):
    __tablename__ = 'alerts_subscription'

    id = Column(
        BigInteger, primary_key=True,
        server_default=text("nextval('alerts_subscription_id_seq'::regclass)")
    )
    equipment_id = Column(Integer, nullable=False)
    user_id = Column(CHAR(32), nullable=False)
    active = Column(Boolean, nullable=False, server_default=text("true"))
    subscribe_time = Column(
        DateTime, nullable=False, server_default=text("timezone('utc'::text, now())")
    )
    unsubscribe_time = Column(DateTime)
    minutes_to_live = Column(Integer, nullable=False, server_default=text("480"))
    subscribe_action = Column(Integer, server_default=text("0"))


t_all_db_volume = Table(
    'all_db_volume', metadata,
    Column('total', Text)
)


class AnswersCategory(Base):
    __tablename__ = 'answers_categories'

    answer_category = Column(Integer, primary_key=True)
    name = Column(Text)


t_bad_workflows = Table(
    'bad_workflows', metadata,
    Column('dt', DateTime(True)),
    Column('equipment_id', BigInteger),
    Column('bad_start_id', BigInteger),
    Column('bad_stop_id', BigInteger),
    Column('duration1', BigInteger),
    Column('start_id', BigInteger),
    Column('stop_id', BigInteger),
    Column('duration2', BigInteger)
)


class Equipment(Base):
    __tablename__ = 'equipment'

    equipment_id = Column(Integer, primary_key=True)
    group_id = Column(Integer)
    equipment_name = Column(String(200))
    equipment_status = Column(Integer, nullable=False, server_default=text("0"))
    plan_val = Column(Float(53))
    mac_address = Column(String(50))
    use_align_filter = Column(Boolean, server_default=text("false"))
    align_filter_secs = Column(BigInteger, server_default=text("15"))
    std_window_secs = Column(BigInteger, server_default=text("5"))
    sort_order = Column(Integer, server_default=text("0"))


t_equipment_and_groups = Table(
    'equipment_and_groups', metadata,
    Column('equipment_id', Integer),
    Column('equipment_name', String(200)),
    Column('group_id', Integer),
    Column('group_name', String(200)),
    Column('channel_id', Integer),
    Column('channel_alias', String),
    Column('is_active', Boolean),
    Column('sens_level', Float(53)),
    Column('use_std', Boolean),
    Column('std_level', Float),
    Column('mac_address', String(50))
)


class Group(Base):
    __tablename__ = 'groups'

    group_id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)
    group_name = Column(String(200))
    group_status = Column(Integer, nullable=False, server_default=text("1"))


class User(Base):
    __tablename__ = 'users'

    user_id = Column(CHAR(32), primary_key=True)
    user_name = Column(String(50))
    user_full_name = Column(String(250))
    user_mail = Column(String(250))
    user_role = Column(Integer, nullable=False, server_default=text("0"))
    user_auth_type = Column(Integer, nullable=False, server_default=text("0"))
    user_status = Column(Integer, nullable=False, server_default=text("1"))
    user_password = Column(String(400))
    salt = Column(String(400))
    last_device_id = Column(String(400))
    create_time = Column(DateTime, server_default=text("timezone('utc'::text, now())"))
    update_time = Column(DateTime, server_default=text("timezone('utc'::text, now())"))
    bad_tries = Column(SmallInteger, nullable=False, server_default=text("0"))


class Workflow(Base):
    __tablename__ = 'workflow'

    equipment_id = Column(BigInteger, primary_key=True, nullable=False)
    start_id = Column(BigInteger, primary_key=True, nullable=False)
    stop_id = Column(BigInteger)
    answer_id = Column(Integer, server_default=text("0"))
    is_alerted = Column(Boolean, server_default=text("false"))


class AnswersList(Base):
    __tablename__ = 'answers_list'

    answer_id = Column(Integer, primary_key=True)
    answer_text = Column(String(400), nullable=False)
    answer_action = Column(SmallInteger)
    is_system = Column(Boolean, server_default=text("false"))
    answer_category = Column(
        ForeignKey('answers_categories.answer_category'), nullable=False,
        index=True, server_default=text("1")
    )
    answer_color = Column(Text, nullable=False, server_default=text("'#BDF4A8'::text"))

    answers_category = relationship('AnswersCategory')


class UsersGroup(Base):
    __tablename__ = 'users_groups'

    user_id = Column(
        ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True, nullable=False
    )
    group_id = Column(
        ForeignKey('groups.group_id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True, nullable=False
    )
    user_role = Column(Integer, nullable=False, server_default=text("0"))

    group = relationship('Group')
    user = relationship('User')
