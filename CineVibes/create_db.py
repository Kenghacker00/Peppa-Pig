import sqlite3
from config import Config

def create_database():
    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()

    # Crear tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("Base de datos y tabla de usuarios creadas exitosamente.")

if __name__ == '__main__':
    create_database()
