import random
from models.users import User
from werkzeug.security import generate_password_hash, check_password_hash
from utils.email import send_verification_email

class AuthController:
    def __init__(self, db_path):
        self.user_model = User(db_path)
        self.verification_codes = {}  # Almacena códigos de verificación

    def register(self, nickname, email, password):
        hashed_password = generate_password_hash(password)
        self.user_model.create_user(nickname, email, hashed_password)

    def verify_code(self, email, code):
        if email in self.verification_codes and self.verification_codes[email] == code:
            # Eliminar el código después de la verificación
            del self.verification_codes[email]
            # Aquí puedes guardar el usuario en la base de datos
            # Asegúrate de que el usuario no exista ya
            user = self.user_model.get_user_by_email(email)
            if user:
                return {'success': False, 'message': 'El usuario ya existe.'}
            # Si el usuario no existe, crea uno nuevo
            self.user_model.create_user(nickname, email, generate_password_hash(password))  # Asegúrate de que el nickname y password estén disponibles
            return {'success': True, 'message': 'Verificación exitosa. Usuario registrado.'}
        return {'success': False, 'message': 'Código de verificación incorrecto.'}

    def login(self, email, password):
        user = self.get_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            return {'success': True, 'user_id': user['id']}
        return {'success': False, 'message': 'Correo o contraseña incorrectos.'}
