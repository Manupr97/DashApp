class Config:
    SECRET_KEY = 'claveultrasecreta123'  # Usa una clave FIJA para pruebas
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'