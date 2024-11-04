class ReviewController:
    def __init__(self, db_path):
        self.db_path = db_path

    def add_review(self, user_id, movie_id, review_text):
        conn = sqlite3.connect(self.db_path)
        conn.execute('INSERT INTO reviews (user_id, movie_id, review_text) VALUES (?, ?, ?)',
                     (user_id, movie_id, review_text))
        conn.commit()
        conn.close()
        return {'success': True, 'message': 'Reseña enviada.'}
