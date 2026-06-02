import os
import platform

# --- Configuration du chemin vers les fichiers VLC locaux ---
vlc_path = os.path.join(os.getcwd(), "vlc_files")
os.environ['PATH'] += os.pathsep + vlc_path
import vlc

import time
from datetime import datetime

# Database
from db import SessionLocal
from models import Track
from sqlalchemy.exc import SQLAlchemyError

# ==============================================================================
# PLAYER.PY — Bibliothèque de lecture MP3 pour le projet L.A.S.E.R
# Utilise python-vlc pour contrôler la lecture audio sans interface graphique.
# Usage : importer la classe MusicPlayer dans main.py ou client_yt_music.py
# ==============================================================================


class MusicPlayer:
    """
    Lecteur MP3 basé sur python-vlc.

    Fonctionnalités :
      - Charger une playlist depuis un dossier
      - Play / Pause / Stop
      - Chanson suivante / précédente
      - Contrôle du volume (0-100)
      - Mode aléatoire (shuffle)
      - Mode répétition (repeat)
      - Récupérer les infos de la piste en cours
    """

    def __init__(self, music_folder: str = None):
        """
        Initialise le player VLC.

        :param music_folder: chemin vers le dossier contenant les fichiers MP3.
                             Si None, la playlist reste vide jusqu'à l'appel
                             de load_folder().
        """
        # --- Initialisation du moteur VLC ---
        vlc_args = ['--no-video', '--quiet', '--verbose=-1']
        if platform.system() == 'Linux':
            vlc_args.append('--aout=pulse')
        self._instance = vlc.Instance(vlc_args)
        self._instance.log_unset()
        self._list_player = self._instance.media_list_player_new()
        self._media_list = self._instance.media_list_new()
        self._list_player.set_media_list(self._media_list)

        # --- Récupération du lecteur interne pour les commandes avancées ---
        # MediaPlayer donne accès au volume, à la position, etc.
        self._player = self._list_player.get_media_player()

        # --- État interne ---
        self._playlist = []          # liste des chemins absolus des fichiers MP3
        self._current_index = 0      # index de la piste en cours dans _playlist
        self._volume = 80            # volume par défaut (0-100)
        self._shuffle = False        # mode aléatoire désactivé par défaut
        self._repeat = False         # mode répétition désactivé par défaut
        self._music_folder = os.path.abspath(music_folder) if music_folder else None

        # Note: Volume setting moved to after media loading to avoid initialization issues

        # --- Chargement automatique si un dossier est fourni ---
        if music_folder:
            self.load_folder(music_folder, recursive=True)

    # ==========================================================================
    # CHARGEMENT DE LA PLAYLIST
    # ==========================================================================

    def load_folder(self, folder_path: str, recursive: bool = False) -> int:
        """
        Analyse et met à jour les métadonnées des fichiers MP3 via Discogs.
        Gère les erreurs de manière robuste et ne bloque pas le démarrage.
        
        :param folder_path: chemin du dossier à scanner (défaut: MUSIC_FOLDER)
        :param recursive: si True, cherche dans les sous-dossiers aussi
        :return: nombre de fichiers MP3 trouvés et chargés.
        """
        if not os.path.isdir(folder_path):
            raise FileNotFoundError(f"Dossier introuvable : {folder_path}")

        # Réinitialise la playlist interne et la liste VLC
        self._playlist = []
        self._media_list = self._instance.media_list_new()

        # Collecte tous les fichiers audio pris en charge (récursivement si demandé)
        audio_exts = (".mp3", ".flac", ".wav", ".m4a", ".aac", ".ogg")
        audio_files = []
        if recursive:
            # Cherche dans tous les sous-dossiers
            for root, dirs, files in os.walk(folder_path):
                for filename in sorted(files):
                    if filename.lower().endswith(audio_exts):
                        full_path = os.path.join(root, filename)
                        audio_files.append(full_path)
        else:
            # Cherche seulement dans le dossier principal
            for filename in sorted(os.listdir(folder_path)):
                if filename.lower().endswith(audio_exts):
                    full_path = os.path.join(folder_path, filename)
                    audio_files.append(full_path)

        # Ajoute tous les fichiers à la playlist et à VLC
        for full_path in audio_files:
            self._playlist.append(full_path)
            media = self._instance.media_new(full_path)
            self._media_list.add_media(media)
            try:
                self._ensure_db_record(full_path)
            except Exception:
                pass

        # Associe la nouvelle liste VLC au player
        self._list_player.set_media_list(self._media_list)
        self._player = self._list_player.get_media_player()
        # Set volume after media list is configured
        try:
            self._player.audio_set_volume(self._volume)
        except Exception as e:
            print(f"[Player] Warning: Could not set initial volume: {e}")
        self._current_index = 0

        return len(self._playlist)

    def _extract_path_metadata(self, path: str):
        title = os.path.splitext(os.path.basename(path))[0]
        artist = ""
        album = ""
        if self._music_folder:
            try:
                rel_path = os.path.relpath(path, self._music_folder)
                parts = rel_path.split(os.sep)
                if len(parts) >= 3:
                    artist = parts[0]
                    album = parts[1]
                elif len(parts) == 2:
                    artist = parts[0]
            except Exception:
                pass
        return title, artist, album

    def _ensure_db_record(self, path: str):
        title, artist, album = self._extract_path_metadata(path)
        session = SessionLocal()
        try:
            track = session.query(Track).filter_by(path=path).first()
            if not track:
                track = Track(
                    path=path,
                    title=title,
                    artist=artist,
                    album=album,
                    scanned=False,
                    tagged=False,
                    play_count=0,
                    last_played=None,
                )
                session.add(track)
            else:
                if not track.title:
                    track.title = title
                if not track.artist and artist:
                    track.artist = artist
                if not track.album and album:
                    track.album = album
            session.commit()
        except SQLAlchemyError:
            session.rollback()
        finally:
            session.close()

    def add_track(self, file_path: str):
        """
        Analyse et ajoute un fichier MP3 à la playlist.
        Gère les erreurs de manière robuste et ne bloque pas le démarrage.
        
        :param file_path: chemin absolu ou relatif vers le fichier .mp3
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")
        if not file_path.lower().endswith(".mp3"):
            raise ValueError("Le fichier doit être un .mp3")

        self._playlist.append(file_path)
        media = self._instance.media_new(file_path)
        self._media_list.add_media(media)

    # ==========================================================================
    # CONTRÔLES DE LECTURE (Play / Pause / Stop)
    # ==========================================================================

    def play(self, index: int = None):
        """
        Analyse et démarre ou reprend la lecture audio.
        Gère les erreurs de manière robuste et ne bloque pas le démarrage.
        
        :param index: index de la piste à jouer, None pour reprendre la courante
        """
        if not self._playlist:
            print("[Player] La playlist est vide. Chargez des fichiers d'abord.")
            return

        if index is not None:
            # Validation de l'index
            if not (0 <= index < len(self._playlist)):
                raise IndexError(f"Index {index} hors de la playlist ({len(self._playlist)} pistes).")
            self._current_index = index
            # Navigue directement à la piste demandée dans la liste VLC
            self._list_player.play_item_at_index(self._current_index)
            # Enregistrer la lecture en base
            try:
                self._record_play()
            except Exception:
                pass
        else:
            # Reprend la lecture (ou démarre depuis le début si rien n'est en cours)
            self._list_player.play()
            try:
                self._record_play()
            except Exception:
                pass

    def pause(self):
        """
        Bascule entre pause et lecture en fonction de l'état actuel.
        Utilise le comportement de toggle de VLC.
        """
        # VLC gère automatiquement le toggle play/pause avec cette méthode
        self._list_player.pause()

    def stop(self):
        """
        Analyse et arrête la lecture audio.
        Gère les erreurs de manière robuste et remet la position à zéro.
        """
        self._list_player.stop()

    # ==========================================================================
    # NAVIGATION DANS LA PLAYLIST (Suivant / Précédent)
    # ==========================================================================

    def next_track(self):
        """
        Passe à la piste suivante dans la playlist.
        Revient à la première piste si on est à la fin (comportement cyclique).
        """
        if not self._playlist:
            return

        if self._shuffle:
            # Mode aléatoire : choisit un index différent de l'actuel
            import random
            candidates = [i for i in range(len(self._playlist)) if i != self._current_index]
            if candidates:
                self._current_index = random.choice(candidates)
        else:
            # Mode normal : piste suivante, retour au début si fin de liste
            self._current_index = (self._current_index + 1) % len(self._playlist)

        self._list_player.play_item_at_index(self._current_index)
        try:
            self._record_play()
        except Exception:
            pass

    def previous_track(self):
        """
        Revient à la piste précédente dans la playlist.
        Va à la dernière piste si on est à la première (comportement cyclique).
        """
        if not self._playlist:
            return

        self._current_index = (self._current_index - 1) % len(self._playlist)
        self._list_player.play_item_at_index(self._current_index)
        try:
            self._record_play()
        except Exception:
            pass

    def _record_play(self):
        """
        Met à jour les statistiques de lecture en base pour la piste courante.
        Incrémente `play_count` et met à jour `last_played`.
        """
        if not self._playlist:
            return

        path = self._playlist[self._current_index]
        session = SessionLocal()
        try:
            db_track = session.query(Track).filter_by(path=path).first()
            title, artist, album = self._extract_path_metadata(path)
            if not db_track:
                db_track = Track(
                    path=path,
                    title=title,
                    artist=artist,
                    album=album,
                    scanned=False,
                    tagged=False,
                    play_count=1,
                    last_played=datetime.utcnow(),
                )
                session.add(db_track)
            else:
                if not db_track.title:
                    db_track.title = title
                if not db_track.artist and artist:
                    db_track.artist = artist
                if not db_track.album and album:
                    db_track.album = album
                db_track.play_count = (db_track.play_count or 0) + 1
                db_track.last_played = datetime.utcnow()
            session.commit()
        except SQLAlchemyError:
            session.rollback()
        finally:
            session.close()

    # ==========================================================================
    # CONTRÔLE DU VOLUME
    # ==========================================================================

    def set_volume(self, volume: int):
        """
        Analyse et définit le volume de lecture audio.
        Gère les erreurs de manière robuste et valide les données.
        
        :param volume: entier entre 0 (muet) et 100 (maximum)
        """
        if not (0 <= volume <= 100):
            raise ValueError("Le volume doit être compris entre 0 et 100.")
        self._volume = volume
        try:
            self._player.audio_set_volume(self._volume)
        except Exception as e:
            print(f"[Player] Warning: Could not set volume to {self._volume}: {e}")

    def get_volume(self) -> int:
        """
        Analyse et retourne le niveau sonore actuel du lecteur.
        Normalise la valeur stockée en cas d'erreur.
        
        :return: volume entre 0 et 100
        """
        try:
            return self._player.audio_get_volume()
        except Exception as e:
            print(f"[Player] Warning: Could not get volume: {e}")
            return self._volume  # Return stored value as fallback

    def volume_up(self, step: int = 5):
        """
        Analyse et augmente le niveau sonore d'une valeur donnée.
        Ne dépasse pas le maximum de 100.
        
        :param step: nombre de points à ajouter (défaut : 5)
        """
        self.set_volume(min(100, self.get_volume() + step))

    def volume_down(self, step: int = 5):
        """
        Analyse et diminue le niveau sonore d'une valeur donnée.
        Ne descend pas en dessous de 0.
        
        :param step: nombre de points à retirer (défaut : 5)
        """
        self.set_volume(max(0, self.get_volume() - step))

    # ==========================================================================
    # MODES DE LECTURE (Shuffle / Repeat)
    # ==========================================================================

    def toggle_shuffle(self) -> bool:
        """
        Analyse et bascule l'activation du mode aléatoire.
        Retourne le nouvel état du shuffle.
        
        :return: True si shuffle est activé, False sinon
        """
        self._shuffle = not self._shuffle
        return self._shuffle

    def toggle_repeat(self) -> bool:
        """
        Analyse et bascule l'activation du mode répétition.
        Gère le mode boucle de VLC automatiquement.
        
        :return: True si repeat est activé, False sinon
        """
        self._repeat = not self._repeat
        if self._repeat:
            self._list_player.set_playback_mode(vlc.PlaybackMode.loop)
        else:
            self._list_player.set_playback_mode(vlc.PlaybackMode.default)
        return self._repeat

    # ==========================================================================
    # INFORMATIONS SUR LA PISTE EN COURS
    # ==========================================================================

    def get_current_track_name(self, show_path: bool = False) -> str:
        """
        Analyse et retourne le nom de la piste en cours de lecture.
        Option pour afficher le chemin relatif complet.
        
        :param show_path: si True, affiche le chemin complet
        :return: nom de la piste ou 'Aucune piste' si vide
        """
        if not self._playlist:
            return "Aucune piste"
        full_path = self._playlist[self._current_index]
        filename = os.path.basename(full_path)
        name = os.path.splitext(filename)[0]
        
        if show_path:
            # Affiche le chemin relatif avec les sous-dossiers
            return full_path.replace(os.sep, ' / ')
        return name

    def get_current_index(self) -> int:
        """
        Analyse et retourne l'index de la piste en cours.
        Utilise une numérotation 0-basée.
        
        :return: index de la piste courante
        """
        return self._current_index

    def get_playlist(self, show_path: bool = False) -> list:
        """
        Analyse et retourne la liste de toutes les pistes.
        Option pour afficher le chemin complet ou le nom seul.
        
        :param show_path: si True, retourne les chemins complets
        :return: liste de noms ou chemins de pistes
        """
        if show_path:
            return self._playlist
        return [
            os.path.splitext(os.path.basename(p))[0]
            for p in self._playlist
        ]

    def get_duration(self) -> float:
        """
        Analyse et retourne la durée totale de la piste en cours.
        Retourne -1 si la durée n'est pas disponible.
        
        :return: durée en secondes ou -1 si indisponible
        """
        ms = self._player.get_length()  # durée en millisecondes
        return ms / 1000 if ms > 0 else -1

    def get_position(self) -> float:
        """
        Analyse et retourne la position actuelle de la lecture.
        Retourne -1 si aucune piste n'est en cours.
        
        :return: position en secondes ou -1 si non disponible
        """
        ms = self._player.get_time()    # position en millisecondes
        return ms / 1000 if ms >= 0 else -1

    def seek(self, seconds: float):
        """
        Analyse et déplace la tête de lecture à une position donnée.
        Gère les erreurs de manière robuste et ne bloque pas le démarrage.
        
        :param seconds: position cible en secondes depuis le début
        """
        ms = int(seconds * 1000)
        self._player.set_time(ms)

    def is_playing(self) -> bool:
        """
        Analyse et vérifie l'état de lecture du lecteur.
        Indique si le lecteur est actuellement en train de jouer.
        
        :return: True si en lecture, False sinon
        """
        return self._player.is_playing() == 1

    def get_status(self) -> dict:
        """
        Analyse et retourne un dictionnaire récapitulatif de l'état du lecteur.
        Pratique pour afficher l'état dans main.py ou une interface CLI.
        
        :return: dict avec track, index, total, playing, volume, shuffle, repeat, position, duration
        """
        return {
            "track":    self.get_current_track_name(),
            "index":    self._current_index + 1,          # numérotation 1-based
            "total":    len(self._playlist),
            "playing":  self.is_playing(),
            "volume":   self.get_volume(),
            "shuffle":  self._shuffle,
            "repeat":   self._repeat,
            "position": round(self.get_position(), 1),
            "duration": round(self.get_duration(), 1),
        }


# ==============================================================================
# EXEMPLE D'UTILISATION — exécutable directement pour tester le player
# Ce bloc ne s'exécute PAS quand player.py est importé dans main.py
# ==============================================================================

if __name__ == "__main__":
    import sys

    # Dossier de musiques : argument en ligne de commande ou dossier courant
    folder = sys.argv[1] if len(sys.argv) > 1 else "."

    print("=== Test du MusicPlayer L.A.S.E.R ===\n")
    player = MusicPlayer(folder)

    nb = len(player.get_playlist())
    if nb == 0:
        print(f"Aucun fichier MP3 trouvé dans : {folder}")
        sys.exit(1)

    print(f"{nb} piste(s) chargée(s) :")
    for i, name in enumerate(player.get_playlist()):
        print(f"  {i + 1}. {name}")

    print("\nDémarrage de la lecture...")
    player.play()

    # Boucle de démonstration interactive simple
    COMMANDS = """
Commandes disponibles :
  p  → play/pause   s  → stop         n  → suivante
  b  → précédente   +  → volume +5    -  → volume -5
  r  → repeat       x  → shuffle      i  → infos
  q  → quitter
"""
    print(COMMANDS)

    while True:
        cmd = input("Commande > ").strip().lower()

        if cmd == "q":
            player.stop()
            print("Arrêt du player. À bientôt !")
            break
        elif cmd == "p":
            player.pause()
            print("Play/Pause")
        elif cmd == "s":
            player.stop()
            print("Stop")
        elif cmd == "n":
            player.next_track()
            print(f"Piste suivante → {player.get_current_track_name()}")
        elif cmd == "b":
            player.previous_track()
            print(f"Piste précédente → {player.get_current_track_name()}")
        elif cmd == "+":
            player.volume_up()
            print(f"Volume : {player.get_volume()}")
        elif cmd == "-":
            player.volume_down()
            print(f"Volume : {player.get_volume()}")
        elif cmd == "r":
            state = player.toggle_repeat()
            print(f"Repeat : {'ON' if state else 'OFF'}")
        elif cmd == "x":
            state = player.toggle_shuffle()
            print(f"Shuffle : {'ON' if state else 'OFF'}")
        elif cmd == "i":
            status = player.get_status()
            print(
                f"\n🎵 {status['track']}\n"
                f"   Piste {status['index']}/{status['total']} | "
                f"{'▶ lecture' if status['playing'] else '⏸ pause'} | "
                f"Volume : {status['volume']} | "
                f"Position : {status['position']}s / {status['duration']}s\n"
                f"   Shuffle : {'ON' if status['shuffle'] else 'OFF'} | "
                f"Repeat : {'ON' if status['repeat'] else 'OFF'}\n"
            )
        else:
            print("Commande inconnue. Tapez 'q' pour quitter.")