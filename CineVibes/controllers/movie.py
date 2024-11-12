from models.movie import Movie
from utils.imdb import get_movie_details, search_movies as search_movies_api
import sqlite3

class MovieController:
    def __init__(self, db_path):
        self.movie_model = Movie(db_path)

    def search_movies(self, query):
        return search_movies_api(query)  # Llama a la función de búsqueda de la API

    def get_movie_details(self, movie_id):
        movie_details = get_movie_details(movie_id)  # Llamada a la API
        if 'errorMessage' in movie_details:
            return None  # Manejo de errores si no se obtienen detalles

        return {
            'title': movie_details.get('Title', 'N/A'),
            'year': movie_details.get('Year', 'N/A'),
            'poster': movie_details.get('Poster', 'N/A'),
            'imdb_rating': movie_details.get('imdbRating', 'N/A'),
            'director': movie_details.get('Director', 'N/A'),
            'runtime': movie_details.get('Runtime', 'N/A'),
            'plot': movie_details.get('Plot', 'N/A'),
            'imdb_id': movie_id,
            'language': movie_details.get('Language', 'N/A'),
            'country': movie_details.get('Country', 'N/A'),
            'awards': movie_details.get('Awards', 'N/A'),
            'actors': movie_details.get('Actors', 'N/A'),
            'genre': movie_details.get('Genre', 'N/A')
        }

    def get_all_movies(self):
        return self.movie_model.get_all_movies()

    def get_available_movies(self):
        # Aquí deberías implementar la lógica para obtener los imdb_id de las películas disponibles
        with sqlite3.connect(self.movie_model.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT imdb_id FROM movies WHERE available = 1')  # Asegúrate de que la columna 'available' exista
            available_movies = [row[0] for row in cursor.fetchall()]
        return available_movies
