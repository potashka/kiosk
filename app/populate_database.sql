DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS users_groups;
DROP TABLE IF EXISTS equipment;
DROP TABLE IF EXISTS answers_categories;
DROP TABLE IF EXISTS answers_list;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS alerts_subscription;
DROP TABLE IF EXISTS workflow;

-- Создание таблиц
CREATE TABLE groups (
    group_id INTEGER PRIMARY KEY,
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
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
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
    equipment_id INTEGER PRIMARY KEY,
    group_id INTEGER,
    equipment_name VARCHAR(200),
    equipment_status INTEGER NOT NULL DEFAULT 0,
    plan_val FLOAT,
    mac_address VARCHAR(50),
    use_align_filter BOOLEAN DEFAULT 0,
    align_filter_secs BIGINT DEFAULT 15,
    std_window_secs BIGINT DEFAULT 5,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE answers_categories (
    answer_category INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE answers_list (
    answer_id INTEGER PRIMARY KEY,
    answer_text VARCHAR(400) NOT NULL,
    answer_action SMALLINT,
    is_system BOOLEAN DEFAULT 0,
    answer_category INTEGER NOT NULL DEFAULT 1,
    answer_color TEXT NOT NULL DEFAULT '#BDF4A8',
    FOREIGN KEY (answer_category) REFERENCES answers_categories (answer_category)
);

CREATE TABLE alerts (
    id BIGINT PRIMARY KEY,
    equipment_id INTEGER NOT NULL,
    start_id BIGINT NOT NULL,
    user_id CHAR(32) NOT NULL,
    open_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    close_time DATETIME,
    answer_id INTEGER,
    alarm_type INTEGER NOT NULL DEFAULT 0,
    minutes_to_live INTEGER DEFAULT 30
);

CREATE TABLE alerts_subscription (
    id VARCHAR(36) PRIMARY KEY,
    equipment_id INTEGER NOT NULL,
    user_id CHAR(32) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT 1,
    subscribe_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    unsubscribe_time DATETIME,
    minutes_to_live INTEGER NOT NULL DEFAULT 480,
    subscribe_action INTEGER
);

CREATE TABLE workflow (
    equipment_id BIGINT NOT NULL,
    start_id BIGINT NOT NULL,
    stop_id BIGINT,
    answer_id INTEGER DEFAULT 0,
    is_alerted BOOLEAN DEFAULT 0,
    PRIMARY KEY (equipment_id, start_id)
);

--DELETE FROM groups;
--DELETE FROM users;
--DELETE FROM users_groups;
--DELETE FROM equipment;
--DELETE FROM answers_categories;
--DELETE FROM answers_list;
--DELETE FROM alerts;
--DELETE FROM alerts_subscription;
--DELETE FROM workflow;


-- Заполнение тестовыми данными
INSERT INTO groups (group_id, group_name, group_status) VALUES 
(1, 'ЦЕХ 50', 1), 
(2, 'ЦЕХ 51', 1);

INSERT INTO users (user_id, user_name, user_full_name, user_mail, user_password, user_role, user_auth_type, user_status, bad_tries) VALUES
('user1', 'ivan', 'Ivan Ivanov', 'ivan@example.com', 'scrypt:32768:8:1$HtAgAMD4MxZXPu6A$a7129b9915284722591100ad6a8e7c52e5d9b27fe8b084735e0e2b77b588a2bc15708f82036190c86da87c612166ce9319a5a8af00cc6aedc078405dab839ec2', 1, 1, 1, 0),
('user2', 'petr', 'Petr Petrov', 'petr@example.com', 'scrypt:32768:8:1$pqjOeo5TrEjzu9hh$2a16c1133342d92ddad9f9f8da1bc4ef0ebd83f477d328ca0c07a665b42bcd6d6a1fc193f1734b2505addd32a2bfb9ad51c42a59ede2959ce56d730f25c7577e', 1, 1, 1, 0);

INSERT INTO users_groups (user_id, group_id, user_role) VALUES
('user1', 1, 1),
('user2', 2, 1);

INSERT INTO equipment (equipment_id, group_id, equipment_name, equipment_status) VALUES
(1, 1, 'Станок 1', 0),
(2, 1, 'Станок 2', 0),
(3, 2, 'Станок 3', 0);

INSERT INTO answers_categories (answer_category, name) VALUES
(1, 'Причина 1'),
(2, 'Причина 2');

INSERT INTO answers_list (answer_id, answer_text, answer_category, answer_color) VALUES
(1, 'Ответ 1', 1, '#BDF4A8'),
(2, 'Ответ 2', 2, '#BDF4A8');

INSERT INTO alerts (id, equipment_id, start_id, user_id, open_time, alarm_type, minutes_to_live) VALUES
(1, 1, 1000, 'user1', CURRENT_TIMESTAMP, 0, 30),
(2, 2, 1001, 'user1', CURRENT_TIMESTAMP, 0, 30);

INSERT INTO alerts_subscription (id, equipment_id, user_id, active, subscribe_time, minutes_to_live) VALUES
('uuid1', 1, 'user1', 1, CURRENT_TIMESTAMP, 480),
('uuid2', 2, 'user2', 1, CURRENT_TIMESTAMP, 480);


INSERT INTO workflow (equipment_id, start_id, answer_id, is_alerted) VALUES
(1, 1000, 0, 0),
(2, 1001, 0, 0);
