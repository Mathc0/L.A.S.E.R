import eyed3
import os
import re
import musicbrainzngs
from typing import Tuple

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
    Parse le nom du fichier pour extraire artiste, album et titre.
    Supporte les formats courants comme "Artist - Album - 01 - Title.mp3"
    
    :param filename: nom du fichier (avec ou sans extension)
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
    Recherche un album dans MusicBrainz par artiste et titre de release.
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
    Met à jour les métadonnées MP3 en utilisant l'API MusicBrainz.
    Utilise le nom du fichier si les métadonnées actuelles sont incomplètes.
    """
    if not mb:
        print(f"⚠️  Client MusicBrainz non disponible pour {os.path.basename(file_path)}")
        return False
    
    try:
        audiofile = eyed3.load(file_path)
        if audiofile is None:
            print(f"⚠️  Impossible de charger {os.path.basename(file_path)}")
            return False
        
        tag = audiofile.tag
        if tag is None:
            print(f"⚠️  Pas de tag MP3 trouvé pour {os.path.basename(file_path)}")
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
        return True
    except Exception as e:
        print(f"   ❌ Erreur lors du tagging de {os.path.basename(file_path)} : {e}")
        return False