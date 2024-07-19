from werkzeug.security import generate_password_hash

# Генерация хешей паролей
password_hash1 = generate_password_hash("password1")
password_hash2 = generate_password_hash("password2")

# Скрипт для вставки данных в базу данных
populate_data = f"""
INSERT INTO groups (group_id, group_name, group_status) VALUES 
(1, 'ЦЕХ 50', 1), 
(2, 'ЦЕХ 51', 1);

INSERT INTO users (user_id, user_name, user_full_name, user_mail, user_password, user_role, user_auth_type, user_status, bad_tries) VALUES
('user1', 'ivan', 'Ivan Ivanov', 'ivan@example.com', '{password_hash1}', 1, 1, 1, 0),
('user2', 'petr', 'Petr Petrov', 'petr@example.com', '{password_hash2}', 1, 1, 1, 0);

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
(1, 1, 'user1', 1, CURRENT_TIMESTAMP, 480),
(2, 2, 'user2', 1, CURRENT_TIMESTAMP, 480);

INSERT INTO workflow (equipment_id, start_id, answer_id, is_alerted) VALUES
(1, 1000, 0, 0),
(2, 1001, 0, 0);
"""

# Записать скрипт в файл
with open("populate_data.sql", "w", encoding="utf-8") as f:
    f.write(populate_data)
