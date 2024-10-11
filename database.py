import sqlite3

class SQLighter:

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def select_all(self):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM users').fetchall()

    def insert_new(self, id, username, age):
        """ Добавляем нового пользователя"""
        with self.connection:
            return self.cursor.execute('INSERT INTO users (telegram_id, username, telegram_age) VALUES ({0}, {1}, {2})'.format(id, username, age))

    def select_single(self, rownum):
        with self.connection:
            return self.cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (rownum,)).fetchall()[0]

    def count_rows(self):
        """ Считаем количество строк """
        with self.connection:
            result = self.cursor.execute('SELECT * FROM users').fetchall()
            return len(result)

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()