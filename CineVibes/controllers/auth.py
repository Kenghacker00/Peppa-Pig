import random
import string
from models.users import User
from utils.email import send_verification_email

class AuthController:
    def __init__(self, db_path):
        self.user_model = User(db_path)

    def register(self, nickname, email, password):
        # Generar un código de verificación
        verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Guardar el usuario con el código de verificación
        user_id = self.user_model.create_user(nickname, email, password, verification_code)

        # Enviar el correo de verificación
        send_verification_email(email, verification_code)

        return user_id

    def verify_code(self, email, code):
        user = self.user_model.get_user_by_email(email)
        if user and user['verification_code'] == code:
            # Marcar al usuario como verificado
            self.user_model.set_user_verified(user['id'])
            return True
        return False

    def get_user_profile(self, user_id):
        user = self.user_model.get_user_by_id(user_id)
        if user:
            return {
                'id': user['id'],
                'nickname': user['nickname'],
                'email': user['email'],
                'profile_pic': user['profile_pic'],
                'is_verified': user['is_verified']
            }
        return None

    def update_profile_pic(self, user_id, profile_pic_path):
        # Actualiza la foto de perfil del usuario usando el modelo User
        self.user_model.update_profile_pic(user_id, profile_pic_path)
