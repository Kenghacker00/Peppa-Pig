import sqlite3
from utils.imdb import get_movie_details, search_movies

class Movie:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_movie_by_id(self, movie_id):
        conn = sqlite3.connect(self.db_path)
        movie = conn.execute('SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()
        conn.close()
        return movie

    # Aquí puedes agregar más métodos relacionados con las películas
