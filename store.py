"""Shared data contract for the two feature branches."""

import sqlite3
from datetime import datetime
from pathlib import Path

DEVICE_TYPES = ('Ноутбук', 'Смартфон', 'Планшет', 'Компьютер', 'Бытовая техника', 'Другое')
PRIORITIES = ('Обычный', 'Высокий', 'Срочный')
STATUSES = ('Новая', 'В работе', 'Готова', 'Выдана')


def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL, phone TEXT NOT NULL,
            device TEXT NOT NULL, device_type TEXT NOT NULL,
            problem TEXT NOT NULL, priority TEXT NOT NULL,
            status TEXT NOT NULL, created TEXT NOT NULL, updated TEXT NOT NULL
        )''')


def validate(values):
    limits = {'client': 100, 'phone': 30, 'device': 150, 'problem': 2000}
    cleaned = {}
    errors = {}
    for name, limit in limits.items():
        value = values.get(name, '')
        value = value.strip() if isinstance(value, str) else ''
        cleaned[name] = value
        if not value:
            errors[name] = 'Заполните это поле.'
        elif len(value) > limit:
            errors[name] = f'Максимум {limit} символов.'
    if cleaned['phone'] and not 7 <= sum(c.isdigit() for c in cleaned['phone']) <= 15:
        errors['phone'] = 'Укажите телефон с 7–15 цифрами.'
    for name, options in [('device_type', DEVICE_TYPES), ('priority', PRIORITIES), ('status', STATUSES)]:
        value = values.get(name, '')
        cleaned[name] = value
        if value not in options:
            errors[name] = 'Выберите значение из списка.'
    return cleaned, errors


def create_request(path, values):
    now = datetime.now().isoformat(timespec='seconds')
    with connect(path) as db:
        return db.execute('''INSERT INTO requests
            (client,phone,device,device_type,problem,priority,status,created,updated)
            VALUES (:client,:phone,:device,:device_type,:problem,:priority,:status,:created,:updated)
        ''', {**values, 'created': now, 'updated': now}).lastrowid


def get_request(path, request_id):
    with connect(path) as db:
        return db.execute('SELECT * FROM requests WHERE id=?', (request_id,)).fetchone()
