from models.movie import Movie
from utils.imdb import get_movie_details, search_movies

class MovieController:
    def __init__(self, db_path):
        self.movie_model = Movie(db_path)

    def search_movies(self, query):
        return search_movies(query)

    def get_movie_details(self, movie_id):  # Añadido el parámetro self
        movie_details = get_movie_details(movie_id)  # Llamada a la API
        return {
            'title': movie_details.get('Title'),
            'year': movie_details.get('Year'),
            'poster': movie_details.get('Poster'),
            'imdb_rating': movie_details.get('imdbRating', 'N/A'),
            'director': movie_details.get('Director', 'N/A'),
            'runtime': movie_details.get('Runtime', 'N/A'),
            'plot': movie_details.get('Plot', 'N/A'),
            'imdb_id': movie_id
        }
