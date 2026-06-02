import eyed3
import os
import re
import musicbrainzngs
from typing import Tuple
from datetime import datetime

# Database
from db import SessionLocal
from models import Track
from sqlalchemy.exc import SQLAlchemyError

# Initialize the MusicBrainz client with error handling
try:
    musicbrainzngs.set_useragent(
        "L.A.S.E.R-mp3-tagger",
        "1.0",
        "contact@laser.local"
    )
    mb = musicbrainzngs
except Exception as e:
    print(f"⚠️  Impossible d'initialiser le client MusicBrainz : {e}")
    mb = None

def parse_filename_metadata(filename: str) -> Tuple[str, str, str]:
    """
    Analyse et extrait les métadonnées depuis le nom du fichier.
    Supporte les formats courants comme "Artist - Album - 01 - Title.mp3".
    
    :param filename: nom du fichier avec ou sans extension
    :return: tuple (artist, album, title)
    """
    name = os.path.splitext(filename)[0]
    
    pattern1 = r'^(.+?)\s*-\s*(.+?)\s*-\s*\d+\s*-\s*(.+)$'
    match1 = re.match(pattern1, name)
    if match1:
        artist, album, title = match1.groups()
        return artist.strip(), album.strip(), title.strip()
    
    pattern2 = r'^(.+?)\s*-\s*(.+)$'
    match2 = re.match(pattern2, name)
    if match2:
        artist, title = match2.groups()
        return artist.strip(), "", title.strip()
    
    return "", "", name.strip()

def search_release(artist: str, album: str):
    """
    Recherche un album dans MusicBrainz par artiste et titre.
    Retourne le premier résultat trouvé ou None.
    
    :param artist: nom de l'artiste
    :param album: titre de l'album
    """
    try:
        result = mb.search_releases(artist=artist, release=album, limit=5)
        releases = result.get('release-list', [])
        return releases[0] if releases else None
    except Exception as e:
        print(f"   ❌ Erreur de recherche MusicBrainz (release): {e}")
        return None

def search_recording(artist: str, title: str):
    """
    Recherche un enregistrement dans MusicBrainz par artiste et titre.
    Retourne le premier résultat trouvé ou None.
    
    :param artist: nom de l'artiste
    :param title: titre de la musique
    """
    try:
        result = mb.search_recordings(artist=artist, recording=title, limit=5)
        recordings = result.get('recording-list', [])
        return recordings[0] if recordings else None
    except Exception as e:
        print(f"   ❌ Erreur de recherche MusicBrainz (recording): {e}")
        return None

def safe_artist_name(artist_credit) -> str:
    if not artist_credit:
        return ""
    first = artist_credit[0]
    if isinstance(first, dict):
        return first.get('artist', {}).get('name', '')
    return str(first)

def tag_mp3_file(file_path: str) -> bool:
    """
    Analyse et met à jour les métadonnées des fichiers MP3 via MusicBrainz.
    Gère les erreurs de manière robuste et ne bloque pas le démarrage.
    
    :param file_path: chemin du fichier MP3 à tagger
    :return: True si le tagging a réussi, False sinon
    """
    if not mb:
        print(f"⚠️  Client MusicBrainz non disponible pour {os.path.basename(file_path)}")
        return False

    session = SessionLocal()
    track = None
    try:
        # Si le fichier a déjà été scanné, on saute pour éviter les doublons
        track = session.query(Track).filter_by(path=file_path).first()
        if track and track.scanned:
            print(f"   ℹ️  {os.path.basename(file_path)} déjà scanné, saut du tagging.")
            return False

        audiofile = eyed3.load(file_path)
        if audiofile is None:
            print(f"⚠️  Impossible de charger {os.path.basename(file_path)}")
            # enregistrer comme scanné même si on ne peut pas charger
            if track is None:
                try:
                    track = Track(path=file_path, title=os.path.splitext(os.path.basename(file_path))[0], scanned=True, tagged=False)
                    session.add(track)
                    session.commit()
                except SQLAlchemyError:
                    session.rollback()
            return False
        
        tag = audiofile.tag
        if tag is None:
            print(f"⚠️  Pas de tag MP3 trouvé pour {os.path.basename(file_path)}")
            # marquer comme scanné (mais non taggé)
            try:
                if track is None:
                    track = Track(path=file_path, title=os.path.splitext(os.path.basename(file_path))[0], scanned=True, tagged=False)
                    session.add(track)
                else:
                    track.scanned = True
                    track.tagged = False
                session.commit()
            except SQLAlchemyError:
                session.rollback()
            return False
        
        current_title = tag.title or ""
        current_artist = tag.artist or ""
        current_album = tag.album or ""
        
        filename = os.path.basename(file_path)
        file_artist, file_album, file_title = parse_filename_metadata(filename)
        
        use_file_metadata = (
            not current_title or
            not current_artist or
            current_title == os.path.splitext(filename)[0] or
            len(current_title.split()) < 2
        )
        
        if use_file_metadata and (file_artist or file_title):
            search_artist = file_artist or current_artist or ""
            search_album = file_album or current_album or ""
            search_title = file_title or current_title or ""
        else:
            search_artist = current_artist
            search_album = current_album
            search_title = current_title
        
        print(f"   📊 Métadonnées actuelles:")
        print(f"      • Titre: {current_title}")
        print(f"      • Artiste: {current_artist}")
        print(f"      • Album: {current_album}")
        
        if use_file_metadata:
            print(f"   📁 Utilisation des infos du fichier:")
            print(f"      • Artiste: {search_artist}")
            print(f"      • Album: {search_album}")
            print(f"      • Titre: {search_title}")
        
        release = None
        recording = None
        if search_artist and search_album:
            release = search_release(search_artist, search_album)
        if not release and search_artist and search_title:
            recording = search_recording(search_artist, search_title)
        
        if not release and not recording:
            print(f"   ℹ️  Aucun résultat trouvé sur MusicBrainz pour '{search_artist} {search_album or search_title}'")
            return False
        
        artist_name = search_artist
        album_name = search_album or current_album
        final_title = search_title
        
        if release:
            artist_name = safe_artist_name(release.get('artist-credit', [])) or search_artist
            album_name = release.get('title', search_album)
        elif recording:
            artist_name = safe_artist_name(recording.get('artist-credit', [])) or search_artist
            final_title = recording.get('title', search_title)
            release_list = recording.get('release-list', [])
            if release_list:
                album_name = release_list[0].get('title', album_name)
        
        if not final_title:
            final_title = os.path.splitext(filename)[0]
        if not artist_name:
            artist_name = current_artist or file_artist or "Unknown"
        if not album_name:
            album_name = current_album or file_album or "Unknown"
        
        tag.title = final_title
        tag.artist = artist_name
        tag.album = album_name
        tag.save()
        print(f"   ✅ Métadonnées mises à jour:")
        print(f"      • Titre: {final_title}")
        print(f"      • Artiste: {artist_name}")
        print(f"      • Album: {album_name}")
        # Mettre à jour / créer l'enregistrement en base
        try:
            if track is None:
                track = Track(path=file_path)
                session.add(track)
            track.title = final_title
            track.artist = artist_name
            track.album = album_name
            track.scanned = True
            track.tagged = True
            session.commit()
        except SQLAlchemyError:
            session.rollback()

        return True
    except Exception as e:
        # En cas d'erreur imprévue, s'assurer qu'on marque le fichier comme scanné
        try:
            if track is None:
                track = Track(path=file_path, title=current_title or os.path.splitext(os.path.basename(file_path))[0], artist=current_artist, album=current_album, scanned=True, tagged=False)
                session.add(track)
            else:
                track.scanned = True
                track.tagged = False
            session.commit()
        except Exception:
            try:
                session.rollback()
            except Exception:
                pass
        print(f"   ❌ Erreur lors du tagging de {os.path.basename(file_path)} : {e}")
        return False
    finally:
        session.close()


def tag_youtube_track(path: str, title: str, artist: str, album: str = None) -> bool:
    """
    Analyse et enregistre les métadonnées d'une musique YouTube en base de données.
    Gère les erreurs de manière robuste sans interruption.
    
    :param path: URL ou chemin unique de la musique
    :param title: titre de la musique
    :param artist: artiste de la musique
    :param album: album ou canal (optionnel)
    :return: True si succès, False sinon
    """
    session = SessionLocal()
    try:
        # Chercher ou créer l'entrée
        track = session.query(Track).filter_by(path=path).first()
        
        if not track:
            track = Track(
                path=path,
                title=title,
                artist=artist,
                album=album or "YouTube",
                scanned=True,
                tagged=True,
                play_count=0,
            )
            session.add(track)
            print(f"   ✅ Nouvelle entrée créée : {title} par {artist}")
        else:
            # Mettre à jour si les données manquent
            updated = False
            if not track.title or track.title == "Unknown":
                track.title = title
                updated = True
            if not track.artist or track.artist == "Unknown Artist":
                track.artist = artist
                updated = True
            if not track.album or track.album == "YouTube":
                track.album = album or "YouTube"
                updated = True
            
            track.scanned = True
            track.tagged = True
            
            if updated:
                print(f"   ✅ Métadonnées mises à jour : {title} par {artist}")
            else:
                print(f"   ℹ️  {title} déjà taggé correctement")
        
        session.commit()
        return True
        
    except SQLAlchemyError as e:
        session.rollback()
        print(f"   ❌ Erreur DB lors du tagging YouTube : {e}")
        return False
    except Exception as e:
        session.rollback()
        print(f"   ❌ Erreur lors du tagging YouTube : {e}")
        return False
    finally:
        session.close()