import psycopg2

from tenderchad_scraper.settings import DATABASE_NAME, DATABASE_PASSWORD, DATABASE_USER, DATABASE_HOST, DATABASE_PORT

class PostgresConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connection = psycopg2.connect(
                host=DATABASE_HOST,
                port=DATABASE_PORT,
                database=DATABASE_NAME,
                user=DATABASE_USER,
                password=DATABASE_PASSWORD
            )
        return cls._instance
    

