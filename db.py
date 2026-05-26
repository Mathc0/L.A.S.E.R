import os
import mysql.connector
from mysql.connector import errorcode
import eyed3


class DatabaseManager:
    """Gestion basique de la connexion MySQL et de l'enregistrement des musiques."""

    def __init__(self, host='localhost', user='root', password='', database='laser_db'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.connect()
        self.ensure_tables()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                auth_plugin='mysql_native_password'
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                raise RuntimeError(
                    f"La base de données '{self.database}' n'existe pas ou n'est pas accessible."
                ) from err
            raise RuntimeError(f"Erreur de connexion MySQL : {err}") from err

    def ensure_tables(self):
        if not self.conn:
            return

        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS musics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_path VARCHAR(1024) NOT NULL UNIQUE,
                file_name VARCHAR(255) NOT NULL,
                title VARCHAR(255),
                artist VARCHAR(255),
                album VARCHAR(255),
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        self.conn.commit()
        cursor.close()

    def insert_track(self, file_path: str, title: str = None, artist: str = None, album: str = None):
        if not self.conn:
            return

        file_name = os.path.basename(file_path)
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO musics (file_path, file_name, title, artist, album)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                artist = VALUES(artist),
                album = VALUES(album)
            """,
            (file_path, file_name, title, artist, album)
        )
        self.conn.commit()
        cursor.close()

    def insert_track_from_file(self, file_path: str):
        title = None
        artist = None
        album = None

        try:
            audiofile = eyed3.load(file_path)
            if audiofile and audiofile.tag:
                title = audiofile.tag.title
                artist = audiofile.tag.artist
                album = audiofile.tag.album
        except Exception:
            pass

        self.insert_track(file_path, title, artist, album)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
