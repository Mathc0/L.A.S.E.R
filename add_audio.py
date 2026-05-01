"""
Ajout d'une musique téléchargée depuis YouTube Music dans une base SQLite.

Ce module :
- crée la base de données SQLite si elle n'existe pas ;
- crée la table Musique si elle n'existe pas ;
- télécharge l'audio via la méthode download_audio de client_yt_music.py ;
- récupère les métadonnées de la première vidéo trouvée ;
- insère les informations dans la base.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Dict, Optional

from yt_dlp import YoutubeDL

from client_yt_music import YouTubeMusicClient

DB_PATH = os.path.join(os.path.dirname(__file__), "laser_music.db")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "musiques")
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS Musique (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Nom TEXT NOT NULL,
    Artiste TEXT,
    Nom_Album TEXT,
    Duree INTEGER
);
"""


class MusicDatabase:
    """Gestion simple de la base SQLite des musiques."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(SCHEMA_SQL)
            conn.commit()

    def insert_music(self, nom: str, artiste: Optional[str], nom_album: Optional[str], duree: Optional[int]) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO Musique (Nom, Artiste, Nom_Album, Duree)
                VALUES (?, ?, ?, ?)
                """,
                (nom, artiste, nom_album, duree),
            )
            conn.commit()
            return int(cursor.lastrowid)


def ensure_download_dir(path: str = DOWNLOAD_DIR) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def fetch_music_metadata(query: str) -> Dict[str, Optional[object]]:
    """Récupère les métadonnées de la première vidéo YouTube trouvée pour la requête."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)

    if not info or not info.get("entries"):
        raise ValueError("Aucune musique trouvée pour récupérer les métadonnées.")

    entry = info["entries"][0]
    artistes = entry.get("artists") or []
    artiste = None
    if artistes and isinstance(artistes, list):
        first_artist = artistes[0]
        if isinstance(first_artist, dict):
            artiste = first_artist.get("name")
        else:
            artiste = str(first_artist)

    if not artiste:
        artiste = entry.get("artist") or entry.get("uploader") or entry.get("channel")

    album = entry.get("album")
    duree = entry.get("duration")

    return {
        "Nom": entry.get("title"),
        "Artiste": artiste,
        "Nom_Album": album,
        "Duree": int(duree) if isinstance(duree, (int, float)) else None,
    }


def add_audio_to_database(query: str, db_path: str = DB_PATH, download_dir: str = DOWNLOAD_DIR) -> Dict[str, Optional[object]]:
    """
    Télécharge l'audio via download_audio(), puis ajoute ses métadonnées à la base SQLite.

    :param query: recherche YouTube Music / YouTube.
    :param db_path: chemin vers la base SQLite.
    :param download_dir: dossier de destination des MP3.
    :return: dictionnaire des données insérées.
    """
    ensure_download_dir(download_dir)

    client = YouTubeMusicClient()
    db = MusicDatabase(db_path)

    output_template = "./musiques/%(title)s.%(ext)s"
    downloaded_title = client.download_audio(query, output_path=output_template)
    metadata = fetch_music_metadata(query)

    # En cas de métadonnée absente, on réutilise le titre renvoyé par download_audio.
    metadata["Nom"] = metadata.get("Nom") or downloaded_title

    music_id = db.insert_music(
        nom=str(metadata.get("Nom") or downloaded_title),
        artiste=metadata.get("Artiste"),
        nom_album=metadata.get("Nom_Album"),
        duree=metadata.get("Duree"),
    )

    metadata["id"] = music_id
    return metadata


if __name__ == "__main__":
    query = input("Nom de la musique à télécharger et ajouter en base : ").strip()
    if not query:
        raise ValueError("La recherche ne peut pas être vide.")

    inserted = add_audio_to_database(query)
    print("Musique ajoutée avec succès :")
    print(f"  ID        : {inserted['id']}")
    print(f"  Nom       : {inserted['Nom']}")
    print(f"  Artiste   : {inserted['Artiste']}")
    print(f"  Nom_Album : {inserted['Nom_Album']}")
    print(f"  Duree     : {inserted['Duree']} secondes")
    print(f"  Base      : {DB_PATH}")
