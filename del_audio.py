"""
Suppression d'une musique de la base SQLite et du dossier musiques/.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Optional

from add_audio import DB_PATH, DOWNLOAD_DIR

# Caractères interdits sur Windows que yt-dlp remplace par leur équivalent pleine largeur
_WIN_REPLACEMENTS = str.maketrans('"/\\|?*<>:', '＂／＼｜？＊＜＞：')


def _nom_to_filename(nom: str) -> str:
    """Convertit le Nom stocké en BDD vers le nom de fichier réel produit par yt-dlp."""
    return nom.translate(_WIN_REPLACEMENTS) + ".mp3"


def list_musiques(db_path: str = DB_PATH) -> list[tuple]:
    with sqlite3.connect(db_path) as conn:
        return conn.execute(
            "SELECT id, Nom, Artiste, Duree FROM Musique ORDER BY id"
        ).fetchall()


def delete_music(
    music_id: int,
    db_path: str = DB_PATH,
    download_dir: str = DOWNLOAD_DIR,
) -> dict:
    """
    Supprime la musique (id) de la base et le fichier MP3 correspondant.
    Retourne un dict avec les infos de ce qui a été supprimé.
    """
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT id, Nom, Artiste, Nom_Album, Duree FROM Musique WHERE id = ?",
            (music_id,),
        ).fetchone()

        if row is None:
            raise ValueError(f"Aucune musique avec l'id {music_id} en base.")

        music_id, nom, artiste, nom_album, duree = row

        conn.execute("DELETE FROM Musique WHERE id = ?", (music_id,))
        conn.commit()

    # Suppression du fichier MP3
    filename = _nom_to_filename(nom)
    filepath = os.path.join(download_dir, filename)
    file_deleted = False
    if os.path.exists(filepath):
        os.remove(filepath)
        file_deleted = True

    return {
        "id": music_id,
        "Nom": nom,
        "Artiste": artiste,
        "Nom_Album": nom_album,
        "Duree": duree,
        "fichier_supprime": file_deleted,
        "chemin": filepath,
    }


def _print_list(rows: list[tuple]) -> None:
    if not rows:
        print("  (aucune musique en base)")
        return
    print(f"\n  {'ID':<4} {'Artiste':<20} {'Nom'}")
    print("  " + "-" * 70)
    for row_id, nom, artiste, duree in rows:
        artiste_str = artiste or "?"
        duree_str = f"{duree}s" if duree else "?"
        print(f"  {row_id:<4} {artiste_str:<20} {nom}  [{duree_str}]")
    print()


def _ask_id(rows: list[tuple]) -> Optional[int]:
    ids = {r[0] for r in rows}
    while True:
        raw = input("ID à supprimer (ou 'back' pour annuler) : ").strip()
        if raw.lower() == "back":
            return None
        if raw.isdigit() and int(raw) in ids:
            return int(raw)
        print(f"  ID invalide. Choisissez parmi : {sorted(ids)}")


if __name__ == "__main__":
    print("\n=== Suppression de musiques (L.A.S.E.R) ===\n")

    while True:
        rows = list_musiques()
        _print_list(rows)

        if not rows:
            break

        music_id = _ask_id(rows)
        if music_id is None:
            print("Annulé.")
            break

        result = delete_music(music_id)

        print(f"\n  Supprimé de la base : [{result['id']}] {result['Nom']}")
        if result["fichier_supprime"]:
            print(f"  Fichier supprimé    : {result['chemin']}")
        else:
            print(f"  Fichier introuvable : {result['chemin']}")

        again = input("\nSupprimer une autre musique ? (o/n) : ").strip().lower()
        if again != "o":
            break

    print("Terminé.")
