-- Удаляем существующие таблицы с зависимостями
DROP TABLE IF EXISTS workflow CASCADE;
DROP TABLE IF EXISTS alerts_subscription CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS answers_list CASCADE;
DROP TABLE IF EXISTS answers_categories CASCADE;
DROP TABLE IF EXISTS equipment CASCADE;
DROP TABLE IF EXISTS users_groups CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS groups CASCADE;

-- Создание таблиц
CREATE TABLE groups (
    group_id SERIAL PRIMARY KEY,
    parent_id INTEGER,
    group_name VARCHAR(200),
    group_status INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE users (
    user_id CHAR(32) PRIMARY KEY,
    user_name VARCHAR(50),
    user_full_name VARCHAR(250),
    user_mail VARCHAR(250),
    user_password VARCHAR(400),
    user_role INTEGER NOT NULL DEFAULT 0,
    user_auth_type INTEGER NOT NULL DEFAULT 0,
    user_status INTEGER NOT NULL DEFAULT 1,
    salt VARCHAR(400),
    last_device_id VARCHAR(400),
    create_time TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    update_time TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    bad_tries SMALLINT NOT NULL DEFAULT 0
);

CREATE TABLE users_groups (
    user_id CHAR(32) NOT NULL,
    group_id INTEGER NOT NULL,
    user_role INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (group_id) REFERENCES groups (group_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE equipment (
    equipment_id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(group_id),
    equipment_name VARCHAR(200),
    equipment_status INTEGER NOT NULL DEFAULT 0,
    plan_val FLOAT,
    mac_address VARCHAR(50),
    use_align_filter BOOLEAN DEFAULT FALSE,
    align_filter_secs BIGINT DEFAULT 15,
    std_window_secs BIGINT DEFAULT 5,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE answers_categories (
    answer_category SERIAL PRIMARY KEY,
    name TEXT
);

CREATE TABLE answers_list (
    answer_id SERIAL PRIMARY KEY,
    answer_text VARCHAR(400) NOT NULL,
    answer_action SMALLINT,
    is_system BOOLEAN DEFAULT FALSE,
    answer_category INTEGER NOT NULL DEFAULT 1,
    answer_color TEXT NOT NULL DEFAULT '#BDF4A8',
    FOREIGN KEY (answer_category) REFERENCES answers_categories (answer_category)
);

CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    equipment_id INTEGER NOT NULL REFERENCES equipment(equipment_id),
    start_id BIGINT NOT NULL,
    user_id CHAR(32) NOT NULL REFERENCES users(user_id),
    open_time TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    close_time TIMESTAMP WITH TIME ZONE,
    answer_id INTEGER,
    alarm_type INTEGER NOT NULL DEFAULT 0,
    minutes_to_live INTEGER DEFAULT 30
);

CREATE TABLE alerts_subscription (
    id BIGSERIAL PRIMARY KEY,
    equipment_id INTEGER NOT NULL REFERENCES equipment(equipment_id),
    user_id CHAR(32) NOT NULL REFERENCES users(user_id),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    subscribe_time TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    unsubscribe_time TIMESTAMP WITH TIME ZONE,
    minutes_to_live INTEGER NOT NULL DEFAULT 480,
    subscribe_action INTEGER
);

CREATE TABLE workflow (
    equipment_id BIGINT NOT NULL REFERENCES equipment(equipment_id),
    start_id BIGINT NOT NULL,
    stop_id BIGINT,
    answer_id INTEGER DEFAULT 0,
    is_alerted BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (equipment_id, start_id)
);

-- Заполнение тестовыми данными
INSERT INTO groups (group_name, group_status) VALUES 
('ЦЕХ 50', 1), 
('ЦЕХ 51', 1);

INSERT INTO users (user_id, user_name, user_full_name, user_mail, user_password, user_role, user_auth_type, user_status, bad_tries) VALUES
('user1', 'ivan', 'Ivan Ivanov', 'ivan@example.com', 'scrypt:32768:8:1$HtAgAMD4MxZXPu6A$a7129b9915284722591100ad6a8e7c52e5d9b27fe8b084735e0e2b77b588a2bc15708f82036190c86da87c612166ce9319a5a8af00cc6aedc078405dab839ec2', 1, 1, 1, 0),
('user2', 'petr', 'Petr Petrov', 'petr@example.com', 'scrypt:32768:8:1$pqjOeo5TrEjzu9hh$2a16c1133342d92ddad9f9f8da1bc4ef0ebd83f477d328ca0c07a665b42bcd6d6a1fc193f1734b2505addd32a2bfb9ad51c42a59ede2959ce56d730f25c7577e', 1, 1, 1, 0);

INSERT INTO users_groups (user_id, group_id, user_role) VALUES
('user1', 1, 1),
('user2', 2, 1);

INSERT INTO equipment (group_id, equipment_name, equipment_status) VALUES
(1, 'Станок 1', 0),
(2, 'Станок 2', 0),
(2, 'Станок 3', 0);

INSERT INTO answers_categories (name) VALUES
('Причина 1'),
('Причина 2');

INSERT INTO answers_list (answer_id, answer_text, answer_category, answer_color) VALUES
(1, 'Ответ 1', 1, '#BDF4A8'),
(2, 'Ответ 2', 2, '#BDF4A8');

INSERT INTO alerts (equipment_id, start_id, user_id, open_time, alarm_type, minutes_to_live) VALUES
(1, 1000, 'user1', CURRENT_TIMESTAMP, 0, 30),
(2, 1001, 'user1', CURRENT_TIMESTAMP, 0, 30);

INSERT INTO alerts_subscription (equipment_id, user_id, active, subscribe_time, minutes_to_live) VALUES
(1, 'user1', TRUE, CURRENT_TIMESTAMP, 480),
(2, 'user2', TRUE, CURRENT_TIMESTAMP, 480);

INSERT INTO workflow (equipment_id, start_id, answer_id, is_alerted) VALUES
(1, 1000, 0, FALSE),
(2, 1001, 0, FALSE);
