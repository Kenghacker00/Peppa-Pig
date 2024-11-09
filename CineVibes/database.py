import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self):
        # Asegurarse de que existe el directorio database
        database_dir = 'database'
        if not os.path.exists(database_dir):
            os.makedirs(database_dir)

        self.db_path = os.path.join(database_dir, 'cinevibes.db')
        self.init_db()

    def get_db(self):
        """Obtener conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Inicializar la base de datos y crear todas las tablas"""
        with self.get_db() as conn:
            # Crear tabla de usuarios
            conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                is_verified BOOLEAN DEFAULT 0,
                verification_code TEXT,
                profile_pic TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Crear tabla de películas
            conn.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                imdb_id TEXT UNIQUE,
                title TEXT NOT NULL,
                year INTEGER,
                poster TEXT,
                plot TEXT,
                director TEXT,
                actors TEXT,
                genres TEXT,
                imdb_rating REAL,
                release_date TIMESTAMP
            )
            ''')

            # Crear tabla de reseñas
            conn.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_id INTEGER,
                review_text TEXT,
                rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (movie_id) REFERENCES movies (id)
            )
            ''')

            # Crear tabla de favoritos
            conn.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (movie_id) REFERENCES movies (id),
                UNIQUE(user_id, movie_id)
            )
            ''')

            # Crear tabla de códigos de verificación
            conn.execute('''
            CREATE TABLE IF NOT EXISTS verification_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_used BOOLEAN DEFAULT 0
            )
            ''')

            # Crear tabla de preferencias de usuario
            conn.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                preferred_genres TEXT,
                preferred_actors TEXT,
                preferred_directors TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')

            # Crear tabla de historial de visualización
            conn.execute('''
            CREATE TABLE IF NOT EXISTS watch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_id INTEGER,
                watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (movie_id) REFERENCES movies (id)
            )
            ''')

            # Crear índices
            conn.execute('CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_movies_imdb_id ON movies(imdb_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_reviews_movie_id ON reviews(movie_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_favorites_movie_id ON favorites(movie_id)')

            # Crear vistas
            conn.execute('''
            CREATE VIEW IF NOT EXISTS movie_ratings AS
            SELECT
                movie_id,
                COUNT(*) as review_count,
                AVG(rating) as average_rating
            FROM reviews
            GROUP BY movie_id
            ''')

            conn.execute('''
            CREATE VIEW IF NOT EXISTS user_activity AS
            SELECT
                users.id as user_id,
                users.nickname,
                COUNT(DISTINCT reviews.id) as review_count,
                COUNT(DISTINCT favorites.id) as favorite_count,
                COUNT(DISTINCT watch_history.id) as watched_count
            FROM users
            LEFT JOIN reviews ON users.id = reviews.user_id
            LEFT JOIN favorites ON users.id = favorites.user_id
            LEFT JOIN watch_history ON users.id = watch_history.user_id
            GROUP BY users.id
            ''')

            conn.commit()

    def query_db(self, query, args=(), one=False):
        """Ejecutar una consulta en la base de datos"""
        with self.get_db() as conn:
            cur = conn.execute(query, args)
            rv = cur.fetchall()
            return (rv[0] if rv else None) if one else rv

# Crear una instancia global de la base de datos
db = Database()
