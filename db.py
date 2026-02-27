import psycopg2
from config import FEATURE_DB_URL


def get_connection():
    return psycopg2.connect(FEATURE_DB_URL)