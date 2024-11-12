import sqlite3

class ReviewController:
    def __init__(self, db_path):
        self.db_path = db_path

    def add_review(self, user_id, movie_id, review_text, rating):
        """
        Añade una nueva reseña
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO reviews (user_id, movie_id, review_text, rating) VALUES (?, ?, ?, ?)',
                (user_id, movie_id, review_text, rating)
            )
            conn.commit()
        return {'success': True, 'message': 'Reseña enviada.'}

    def get_user_reviews(self, user_id):
        """
        Obtiene todas las reseñas de un usuario específico
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, m.title as movie_title
                FROM reviews r
                JOIN movies m ON r.movie_id = m.id
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC
            ''', (user_id,))
            reviews = cursor.fetchall()

            # Convertir los resultados a una lista de diccionarios
            return [{
                'id': review['id'],
                'movie_title': review['movie_title'],
                'review_text': review['review_text'],
                'rating': review['rating'],
                'created_at': review['created_at']
            } for review in reviews]

    def get_movie_reviews(self, movie_id):
        """
        Obtiene todas las reseñas de una película específica
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, u.nickname as user_nickname, u.profile_pic as user_profile_pic
                FROM reviews r
                JOIN users u ON r.user_id = u.id
                WHERE r.movie_id = ?
                ORDER BY r.created_at DESC
            ''', (movie_id,))
            reviews = cursor.fetchall()

            # Convertir los resultados a una lista de diccionarios
            return [{
                'id': review['id'],
                'user_nickname': review['user_nickname'],
                'user_profile_pic': review['user_profile_pic'],
                'review_text': review['review_text'],
                'rating': review['rating'],
                'created_at': review['created_at']
            } for review in reviews]

    def delete_review(self, review_id, user_id):
        """
        Elimina una reseña específica (solo si pertenece al usuario)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM reviews WHERE id = ? AND user_id = ?',
                (review_id, user_id)
            )
            conn.commit()
            if cursor.rowcount > 0:
                return {'success': True, 'message': 'Reseña eliminada.'}
            return {'success': False, 'message': 'No se pudo eliminar la reseña.'}

    def update_review(self, review_id, user_id, review_text, rating):
        """
        Actualiza una reseña existente
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE reviews
                SET review_text = ?, rating = ?
                WHERE id = ? AND user_id = ?
            ''', (review_text, rating, review_id, user_id))
            conn.commit()
            if cursor.rowcount > 0:
                return {'success': True, 'message': 'Reseña actualizada.'}
            return {'success': False, 'message': 'No se pudo actualizar la reseña.'}
