import smtplib
from email.mime.text import MIMEText
from config import Config

def send_verification_email(to_email, verification_code):
    subject = "Código de Verificación"
    body = f"Tu código de verificación es: {verification_code}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = Config.EMAIL_SENDER
    msg['To'] = to_email

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
        server.sendmail(Config.EMAIL_SENDER, to_email, msg.as_string())

def send_movie_request_email(to_email, movie_title, user_email, additional_info=None):
    subject = f"Solicitud de película: {movie_title}"
    body = f"""Se ha recibido una solicitud para la película '{movie_title}'
Del usuario: {user_email}
Información adicional: {additional_info or 'No proporcionada'}"""

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = Config.EMAIL_SENDER
    msg['To'] = to_email

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
        server.sendmail(Config.EMAIL_SENDER, to_email, msg.as_string())
