# Kiosk

## Система Управления Сменами и Простоями Оборудования

### Описание
Это веб-приложение предназначено для управления сменами рабочих и отслеживания простоев оборудования на производстве. Оно позволяет пользователям регистрировать начало и окончание смен, а также управлять простоями оборудования.

### Основные функции
- **Аутентификация и управление сессиями пользователей**
- **Управление сменами и простоями через веб-интерфейс**
- **Динамическое отображение и обновление статусов оборудования**

### Технологии
- **FastAPI**: для создания веб-сервера и API.
- **SQLAlchemy** (Async): для асинхронной работы с базой данных.
- **PostgreSQL**: в качестве системы управления базами данных.
- **Uvicorn**: ASGI сервер для запуска приложения.

### Запуск проекта
1. Установите Python 3.9 или выше.
2. Откройте терминал или подключитесь к серверу через SSH. Проверьте версию Git, чтобы узнать, установлен ли он. Введите следующую команду: `git --version`. Если Git не установлен, то при попытке выполнить команду git --version, вы увидите сообщение об ошибке. 

Для установки Git можно использовать команды, соответствующие вашей операционной системе на сервере.
Например для Ubuntu/Debian:

`sudo apt update`
`sudo apt install git`

После установки гита клонируйте репозиторий на сервер `git clone https://github.com/potashka/kiosk.git`

3. Создайте виртуальное окружение и активируйте его.
4. Установите зависимости: `pip install -r requirements.txt`
5. Запустите проект: 

Например,  `uvicorn app.main:app --reload --port 8080` или

`uvicorn app.main:app --reload --host 0.0.0.0 --port 8080` для внешнего хоста

### Структура проекта
- `/app`: основная директория с исходным кодом.
  - `database.py`: конфигурация базы данных (url базы данных)
  - `dependencies.py`: зависимости приложения, включая сессии базы данных.
  - `models.py`: модели базы данных.
  - `main.py`: основной файл приложения с маршрутами API.
- `/templates`: HTML шаблоны для интерфейса пользователя.
- `/static`: статические файлы, такие как CSS.

### Логика работы системы

#### Аутентификация и выбор смены

1. **Выбор цеха:** Оператор выбирает цех из списка. Информация о цехах загружается из базы данных.
2. **Получение списка пользователей:** После выбора цеха на киоске отображается список операторов.
3. **Вход в систему:** Оператор выбирает своё имя из списка и вводит пароль для входа.
4. **Выход из системы:** Можно выйти из системы нажатием кнопки или после тайм-аута.

#### Работа в системе

1. **Постановка на смену:** На дашборде отображается список станков. Оператор может встать на смену или завершить её.
2. **Журнал простоев:** Рядом с каждым станком есть кнопка для просмотра журнала простоев.
3. **Причины простоев:** Оператор может выбрать причину простоя из списка и сохранить информацию.

### API Эндпоинты
- **GET `/`**: приветственная страница.
- **GET `/select-group`**: выбор группы пользователем.
- **POST `/set-group`**: установка выбранной группы в сессию пользователя.
- **GET `/select-user`**: выбор пользователя для аутентификации.
- **POST `/login`**: вход пользователя в систему.
- **GET `/logout`**: выход пользователя из системы.
- **GET `/dashboard/{group_id}`**: панель управления для отображения оборудования.
- **GET `/equipment/{group_id}`**: получение списка оборудования по группе.
- **POST `/toggle-equipment/{equipment_id}`**: переключение статуса оборудования.
- **GET `/downtimes/{equipment_id}`**: получение списка простоев оборудования.
- **POST `/update-downtime/{equipment_id}/{start_id}`**: обновление информации о простое.
- **GET `/answers`**: получение списка возможных ответов для оборудования.

### JavaScript в dashboard.html
В dashboard.html используется JavaScript для управления элементами пользовательского интерфейса, такими как кнопки переключения статуса оборудования и отображение информации о простоях. Скрипт асинхронно обращается к серверу за данными об оборудовании, обновляет информацию на странице без перезагрузки и обрабатывает пользовательские действия, такие как переключение статусов и обновление причин простоев.

### Примеры использования
- **Переключение статуса оборудования**: Пользователи могут включать и выключать оборудование через интерфейс, что инициирует POST запрос на `/toggle-equipment/{equipmentId}`.
- **Управление простоями**: При нажатии на кнопку "Простои", скрипт запрашивает данные о простоях для конкретного оборудования и отображает их. Пользователи могут выбирать причины простоев из выпадающего списка, что отправляет POST запрос на `/update-downtime/{equipmentId}/{startId}`.

# Инструкция по использованию приложения

## Оглавление
1. [Общая информация](#общая-информация)
2. [Выбор группы и авторизация](#выбор-группы-и-авторизация)
3. [Панель управления](#панель-управления)
4. [Описание основных функций](#описание-основных-функций)
   - [Кнопка "Смена"](#кнопка-смена)
   - [Кнопка "Простои"](#кнопка-простои)
   - [Изменение причины простоя](#изменение-причины-простоя)
   - [Навигация по страницам](#навигация-по-страницам)
5. [Таймаут и выход из системы](#таймаут-и-выход-из-системы)

## Общая информация

Данное приложение предназначено для управления оборудованием и мониторинга его состояния. Пользователи могут выбирать группы оборудования, входить в систему с использованием табельного номера и пароля, просматривать текущие простои и изменять их причины.

## Выбор группы и авторизация

1. **Выбор группы**:
    - После открытия приложения пользователь должен выбрать группу оборудования (цех), с которой он будет работать.
    - После выбора группы пользователь будет перенаправлен на страницу авторизации.
    - если приложение запущено командой GROUP_ID=1 uvicorn app.main:app --host 0.0.0.0 --port 8000, то группу выбирать не надо, приложение запускается в меню выбра пользователя в группе 1

2. **Авторизация**:
    - Пользователь вводит свой табельный номер.
    - Затем вводится пароль для подтверждения личности.
    - После успешной авторизации пользователь будет перенаправлен на панель управления.

## Панель управления

Панель управления отображает список оборудования, связанного с выбранной группой. Для каждого оборудования отображаются следующие элементы:

- Название оборудования.
- Кнопки "Поставить на смену/Снять со смены" и "Простои".
- Имя ответственного пользователя (если назначен).

## Описание основных функций


### Кнопка "Поставить на смену"

- **Назначение**: Эта кнопка позволяет пользователю занять оборудование. Если оборудование уже занято другим пользователем, система проверит права текущего пользователя на изменение статуса.
- **Действие**: При нажатии кнопки система переключает статус оборудования (занято/свободно) и название кнопки изменится на "Снять со смены". Если операция успешна, система обновит статус оборудования на странице и подтвердит информационным сообщением.

### Кнопка "Простои"

- **Назначение**: Отображает список простоев для выбранного оборудования.
- **Действие**: При первом нажатии кнопки отображается список всех простоев, включая их время начала и окончания, а также причину простоя. При повторном нажатии список скрывается.

### Изменение причины простоя

- **Назначение**: Позволяет изменить или назначить причину простоя.
- **Действие**:
  - Если простоя еще не была назначена причина, пользователь может выбрать причину из выпадающего списка, нажав кнопку "Изменить".

### Кнопка "поставить на смену"

- **Назначение**: Эта кнопка позволяет пользователю занять оборудование. Если оборудование уже занято другим пользователем, система проверит права текущего пользователя на изменение статуса.
- **Действие**: При нажатии кнопки система переключает статус оборудования (занято/свободно) и название кнопки изменится на "Снять со смены". Если операция успешна, система обновит статус оборудования на странице и подтвердит информационным сообщением.

### Кнопка "Простои"

- **Назначение**: Отображает список простоев для выбранного оборудования.
- **Действие**: При первом нажатии кнопки отображается список всех простоев, включая их время начала и окончания, а также причину простоя. При повторном нажатии список скрывается.

### Изменение причины простоя

- **Назначение**: Позволяет изменить или назначить причину простоя.
- **Действие**:
  - Если еще не была назначена причина простоя, пользователь может выбрать причину из выпадающего списка, нажав кнопку "Изменить" и выбрать причину простоя из информационного списка.
  - Если причина уже назначена, пользователь может нажать кнопку "Изменить", чтобы снова открыть список для выбора причины.
  - После выбора причины простоя необходимо нажать кнопку "Сохранить".

### Навигация по страницам

- **Назначение**: Переключение между страницами списка простоев.
- **Действие**: Для навигации по страницам используются кнопки "<<<" (предыдущая страница) и ">>>" (следующая страница). Нажатие этих кнопок переключает текущую страницу.

## Таймаут и выход из системы

- **Назначение**: Автоматический выход из системы при бездействии пользователя.
- **Действие**: Если пользователь не выполняет действий в течение 5 минут, система автоматически выполнит выход и перенаправит на страницу входа.

## Примечание
- Для корректной работы приложения необходимо обеспечить правильную конфигурацию сервера и баз данных. Убедитесь, что все зависимости установлены и база данных настроена.

Если возникнут вопросы по работе приложения или понадобятся дополнительные функции, обращайтесь за поддержкой.


### Заключение
Это приложение представляет собой инструмент для управления производственными процессами, обеспечивая простоту в использовании и высокую степень кастомизации для конкретных производственных нужд.

