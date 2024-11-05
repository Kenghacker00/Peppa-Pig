from models.movie import Movie
from utils.imdb import get_movie_details, search_movies

class MovieController:
    def __init__(self, db_path):
        self.movie_model = Movie(db_path)

    def get_movie_details(self, movie_id):
        # Aquí puedes obtener detalles de la película desde la API de IMDb
        return get_movie_details(movie_id)

    def search_movies(self, query):
        # Implementa la lógica de búsqueda aquí
        # Por ahora, retornamos las dos películas que tenemos como ejemplo
        return [
            {'imdb_id': 'tt1431045', 'title': 'Deadpool', 'year': 2016},
            {'imdb_id': 'tt1537481', 'title': 'Deadpool and Wolverine', 'year': 2024}
        ]
