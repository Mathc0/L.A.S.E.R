import eyed3
import os
import discogs_client as discogs
from typing import Optional

# Initialize the Discogs client with error handling
try:
    d = discogs.Client('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36')
except Exception as e:
    print(f"⚠️  Impossible d'initialiser le client Discogs : {e}")
    d = None

def tag_mp3_file(file_path: str) -> bool:
    """
    Met à jour les métadonnées MP3 en utilisant l'API Discogs.
    
    :param file_path: chemin vers le fichier MP3
    :return: True si succès, False sinon
    """
    if not d:
        print(f"⚠️  Client Discogs non disponible pour {os.path.basename(file_path)}")
        return False
    
    try:
        # Charge le fichier MP3
        audiofile = eyed3.load(file_path)
        
        if audiofile is None:
            print(f"⚠️  Impossible de charger {os.path.basename(file_path)}")
            return False
        
        # Récupère les métadonnées existantes (avec valeurs par défaut)
        tag = audiofile.tag
        if tag is None:
            print(f"⚠️  Pas de tag MP3 trouvé pour {os.path.basename(file_path)}")
            return False
        
        title = tag.title or "Unknown"
        artist = tag.artist or "Unknown"
        album = tag.album or "Unknown"
        
        print(f"   📊 Métadonnées actuelles:")
        print(f"      • Titre: {title}")
        print(f"      • Artiste: {artist}")
        print(f"      • Album: {album}")
        
        # Recherche sur Discogs
        search_query = f"{artist} - {title}"
        try:
            results = d.search(search_query, type='release')
        except Exception as e:
            print(f"   ❌ Erreur de requête Discogs : {e}")
            return False
        
        if not results:
            print(f"   ℹ️  Aucun résultat trouvé sur Discogs pour '{search_query}'")
            return False
        
        try:
            release = results[0]
            release_artists = release.artists if release.artists else []
            
            if not release_artists:
                print(f"   ⚠️  Pas d'artiste trouvé dans la release Discogs")
                return False
            
            artist_name = release_artists[0].name
            
            # Met à jour les métadonnées
            tag.title = release.title
            tag.artist = artist_name
            tag.album = release.title
            
            # Sauvegarde
            tag.save()
            print(f"   ✅ Métadonnées mises à jour:")
            print(f"      • Titre: {release.title}")
            print(f"      • Artiste: {artist_name}")
            print(f"      • Album: {release.title}")
            return True
            
        except (AttributeError, IndexError) as e:
            print(f"   ❌ Erreur lors du traitement de la release Discogs : {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors du tagging de {os.path.basename(file_path)} : {e}")
        return False