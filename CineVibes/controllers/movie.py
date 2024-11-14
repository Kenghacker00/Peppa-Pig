from models.movie import Movie
from utils.imdb import get_movie_details, search_movies as search_movies_api
import sqlite3

class MovieController:
    def __init__(self, db_path):
        self.movie_model = Movie(db_path)
        self.db_path = db_path

    def search_movies(self, query):
        # Llama a la función de búsqueda de la API
        results = search_movies_api(query)

        # Filtrar resultados para incluir solo películas
        if 'Search' in results:
            # Filtrar solo los resultados que son películas
            filtered_results = [movie for movie in results['Search'] if movie['Type'] == 'movie']

            # Verificar si las películas están disponibles en la base de datos
            available_movies = self.get_available_movies()

            # Marcar las películas disponibles
            for movie in filtered_results:
                movie['is_available'] = movie['imdbID'] in available_movies

            results['Search'] = filtered_results

        return results

    def get_movie_details(self, movie_id):
        movie_details = get_movie_details(movie_id)
        if movie_details and 'errorMessage' not in movie_details:
            return {
                'imdb_id': movie_id,
                'title': movie_details.get('Title', 'N/A'),
                'year': movie_details.get('Year', 'N/A'),
                'poster': movie_details.get('Poster', 'N/A'),
                'director': movie_details.get('Director', 'N/A'),
                'plot': movie_details.get('Plot', 'N/A'),
                'imdb_rating': movie_details.get('imdbRating', 'N/A'),
                'runtime': movie_details.get('Runtime', 'N/A'),
                'language': movie_details.get('Language', 'N/A'),
                'country': movie_details.get('Country', 'N/A'),
                'awards': movie_details.get('Awards', 'N/A'),
                'actors': movie_details.get('Actors', 'N/A'),
                'genre': movie_details.get('Genre', 'N/A')
            }
        return None

    def get_all_movies(self):
        return self.movie_model.get_all_movies()

    def get_available_movies(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT imdb_id FROM movies WHERE available = 1')
            available_movie_ids = [row[0] for row in cursor.fetchall()]

        movies_details = []
        for movie_id in available_movie_ids:
            movie_details = get_movie_details(movie_id)
            if movie_details and 'errorMessage' not in movie_details:
                movies_details.append({
                    'imdb_id': movie_id,
                    'title': movie_details.get('Title', 'N/A'),
                    'year': movie_details.get('Year', 'N/A'),
                    'poster': movie_details.get('Poster', 'N/A'),
                    'director': movie_details.get('Director', 'N/A'),
                    'plot': movie_details.get('Plot', 'N/A')
                })

        return movies_details
