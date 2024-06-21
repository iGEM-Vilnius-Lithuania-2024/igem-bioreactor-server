import os

DB_HOST = "dpg-cpq8g7ks1f4s73cgl3ug-a.frankfurt-postgres.render.com"
DB_NAME = "igem_bioreactor_db"
DB_USER = "ingvaras"
DB_PASS = os.getenv('DB_PASS')
DB_PORT = "5432"

class Config:
    SQLALCHEMY_DATABASE_URI =  f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False