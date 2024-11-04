import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, db_path):
        self.db_path = db_path

    def create_user(self, nickname, email, password):
        hashed_password = generate_password_hash(password, method='sha256')
        conn = sqlite3.connect(self.db_path)
        conn.execute('INSERT INTO users (nickname, email, password) VALUES (?, ?, ?)',
                     (nickname, email, hashed_password))
        conn.commit()
        conn.close()

    def get_user_by_email(self, email):
        conn = sqlite3.connect(self.db_path)
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        return user

    def get_user_by_id(self, user_id):
        conn = sqlite3.connect(self.db_path)
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        return user
