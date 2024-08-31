# app/models
"""
Модуль `models` содержит определения моделей SQLAlchemy для работы с базой данных.

Этот файл используется для настройки и работы с SQL-запросами, а также для описания
структуры таблиц и связей между ними в базе данных.
"""
from sqlalchemy import (
    BigInteger, Boolean, CHAR, Column, DateTime,
    Float, ForeignKey, Index, Integer, SmallInteger,
    String, Table, Text, Time, text  # noqa
)
# from sqlalchemy.dialects.postgresql import OID, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Alert(Base):
    """
    Модель для таблицы `alerts`, представляющей собой оповещения по оборудованию.

    Атрибуты:
        id (BigInteger): Уникальный идентификатор оповещения.
        equipment_id (Integer): Идентификатор оборудования.
        start_id (BigInteger): Идентификатор начала оповещения.
        user_id (CHAR(32)): Идентификатор пользователя, связанного с оповещением.
        open_time (DateTime): Время открытия оповещения.
        close_time (DateTime): Время закрытия оповещения.
        answer_id (Integer): Идентификатор ответа.
        alarm_type (Integer): Тип тревоги.
        minutes_to_live (Integer): Время жизни оповещения в минутах.
    """
    __tablename__ = 'alerts'
    __table_args__ = (
        Index('unique_equipment_user_start', 'equipment_id', 'start_id', 'user_id', unique=True),
    )

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('alerts_id_seq'::regclass)"))
    equipment_id = Column(Integer, nullable=False)
    start_id = Column(BigInteger, nullable=False)
    user_id = Column(CHAR(32), nullable=False)
    open_time = Column(DateTime, nullable=False, server_default=text("timezone('utc'::text, now())"))
    close_time = Column(DateTime)
    answer_id = Column(Integer)
    alarm_type = Column(Integer, nullable=False, server_default=text("0"))
    minutes_to_live = Column(Integer, server_default=text("30"))


class AlertsSubscription(Base):
    """
    Модель для таблицы `alerts_subscription`, представляющей собой подписки на оповещения.

    Атрибуты:
        id (BigInteger): Уникальный идентификатор подписки.
        equipment_id (Integer): Идентификатор оборудования.
        user_id (CHAR(32)): Идентификатор пользователя, связанного с подпиской.
        active (Boolean): Статус подписки (активная/неактивная).
        subscribe_time (DateTime): Время подписки.
        unsubscribe_time (DateTime): Время отписки.
        minutes_to_live (Integer): Время жизни подписки в минутах.
        subscribe_action (Integer): Действие при подписке.
    """
    __tablename__ = 'alerts_subscription'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('alerts_subscription_id_seq'::regclass)"))
    equipment_id = Column(Integer, nullable=False)
    user_id = Column(CHAR(32), nullable=False)
    active = Column(Boolean, nullable=False, server_default=text("true"))
    subscribe_time = Column(DateTime, nullable=False, server_default=text("timezone('utc'::text, now())"))
    unsubscribe_time = Column(DateTime)
    minutes_to_live = Column(Integer, nullable=False, server_default=text("480"))
    subscribe_action = Column(Integer, server_default=text("0"))


t_all_db_volume = Table(
    'all_db_volume', metadata,
    Column('total', Text)
)


class AnswersCategory(Base):
    """
    Модель для таблицы `answers_categories`, представляющей категории простоев.

    Атрибуты:
        answer_category (Integer): Идентификатор категории.
        name (Text): Название категории.
    """
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
    """
    Модель для таблицы `equipment`, представляющей оборудование.

    Атрибуты:
        equipment_id (Integer): Уникальный идентификатор оборудования.
        group_id (Integer): Идентификатор группы (цеха).
        equipment_name (String): Название оборудования.
        equipment_status (Integer): Статус оборудования.
        plan_val (Float): Плановое значение.
        mac_address (String): MAC-адрес оборудования.
        use_align_filter (Boolean): Использование фильтра выравнивания.
        align_filter_secs (BigInteger): Время выравнивания в секундах.
        std_window_secs (BigInteger): Время стандартного окна в секундах.
        sort_order (Integer): Порядок сортировки.
    """
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
    """
    Модель для таблицы `groups`, представляющей группы (цеха).

    Атрибуты:
        group_id (Integer): Уникальный идентификатор группы.
        parent_id (Integer): Идентификатор родительской группы.
        group_name (String): Название группы.
        group_status (Integer): Статус группы.
    """
    __tablename__ = 'groups'

    group_id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)
    group_name = Column(String(200))
    group_status = Column(Integer, nullable=False, server_default=text("1"))


class User(Base):
    """
    Модель для таблицы `users`, представляющей пользователей.

    Атрибуты:
        user_id (CHAR(32)): Уникальный идентификатор пользователя.
        user_name (String): Имя пользователя.
        user_full_name (String): Полное имя пользователя.
        user_mail (String): Электронная почта пользователя.
        user_role (Integer): Роль пользователя.
        user_auth_type (Integer): Тип аутентификации пользователя.
        user_status (Integer): Статус пользователя.
        user_password (String): Хэш пароля пользователя.
        salt (String): Соль для хэша пароля.
        last_device_id (String): Идентификатор последнего устройства.
        create_time (DateTime): Время создания пользователя.
        update_time (DateTime): Время последнего обновления данных пользователя.
        bad_tries (SmallInteger): Количество неудачных попыток входа.
    """
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
    """
    Модель для таблицы `workflow`, представляющей рабочие процессы.

    Атрибуты:
        equipment_id (BigInteger): Уникальный идентификатор оборудования.
        start_id (BigInteger): Идентификатор начала процесса.
        stop_id (BigInteger): Идентификатор завершения процесса.
        answer_id (Integer): Идентификатор ответа.
        is_alerted (Boolean): Признак того, было ли оповещение.
    """
    __tablename__ = 'workflow'

    equipment_id = Column(BigInteger, primary_key=True, nullable=False)
    start_id = Column(BigInteger, primary_key=True, nullable=False)
    stop_id = Column(BigInteger)
    answer_id = Column(Integer, server_default=text("0"))
    is_alerted = Column(Boolean, server_default=text("false"))


class AnswersList(Base):
    """
    Модель для таблицы `answers_list`, представляющей список ответов.

    Атрибуты:
        answer_id (Integer): Уникальный идентификатор ответа.
        answer_text (String): Текст ответа.
        answer_action (SmallInteger): Действие, связанное с ответом.
        is_system (Boolean): Признак системного ответа.
        answer_category (Integer): Идентификатор категории ответа.
        answer_color (Text): Цвет ответа.
    """
    __tablename__ = 'answers_list'

    answer_id = Column(Integer, primary_key=True)
    answer_text = Column(String(400), nullable=False)
    answer_action = Column(SmallInteger)
    is_system = Column(Boolean, server_default=text("false"))
    answer_category = Column(ForeignKey('answers_categories.answer_category'), nullable=False, index=True, server_default=text("1"))
    answer_color = Column(Text, nullable=False, server_default=text("'#BDF4A8'::text"))

    answers_category = relationship('AnswersCategory')


class UsersGroup(Base):
    """
    Модель для таблицы `users_groups`, представляющей связь между пользователями и группами.

    Атрибуты:
        user_id (CHAR(32)): Идентификатор пользователя.
        group_id (Integer): Идентификатор группы.
        user_role (Integer): Роль пользователя в группе.
    """
    __tablename__ = 'users_groups'

    user_id = Column(ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
    group_id = Column(ForeignKey('groups.group_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
    user_role = Column(Integer, nullable=False, server_default=text("0"))

    group = relationship('Group')
    user = relationship('User')
