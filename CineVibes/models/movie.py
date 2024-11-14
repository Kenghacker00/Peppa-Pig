import sqlite3
from utils.imdb import get_movie_details, search_movies

class Movie:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_movie_by_id(self, movie_id):
        with sqlite3.connect(self.db_path) as conn:
            movie = conn.execute('SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()
        return movie

    def add_movie(self, imdb_id, title, year, poster):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO movies (imdb_id, title, year, poster)
                VALUES (?, ?, ?, ?)
            ''', (imdb_id, title, year, poster))
            conn.commit()

    def get_all_movies(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            movies = conn.execute('SELECT imdb_id FROM movies').fetchall()
        return [movie['imdb_id'] for movie in movies]

    # Aquí puedes agregar más métodos relacionados con las películas
