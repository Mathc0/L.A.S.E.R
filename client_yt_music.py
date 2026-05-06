"""
YouTube Music Client - L.A.S.E.R
Lecteur audio YouTube avec streaming VLC.
Interface identique à MusicPlayer pour une utilisation uniforme.
"""

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import os
import random
import subprocess

vlc_path = os.path.join(os.getcwd(), "vlc_files")
os.environ['PATH'] += os.pathsep + vlc_path
import vlc


class YouTubeMusicClient:
    """
    Client YouTube Music avec streaming VLC.

    Fonctionnalités (identiques à MusicPlayer) :
      - Rechercher et ajouter des pistes YouTube dans une playlist
      - Play / Pause / Stop
      - Piste suivante / précédente
      - Contrôle du volume (0-100)
      - Mode aléatoire (shuffle)
      - Mode répétition (repeat)
      - Seek (déplacement dans la piste)
      - Récupérer les infos de la piste en cours
      - Télécharger l'audio d'une piste
    """

    def __init__(self):
        # Configure VLC to avoid PipeWire issues
        vlc_args = [
            '--no-video',  # No video output needed
            '--aout=pulse',  # Use PulseAudio directly
            '--audio-filter=',  # Disable audio filters that might cause issues
        ]
        self._vlc_instance = vlc.Instance(vlc_args)
        self._player = self._vlc_instance.media_player_new()

        # Playlist interne : liste de dicts {title, url}
        self._playlist = []
        self._current_index = 0
        self._volume = 80
        self._shuffle = False
        self._repeat = False

        # Note: Volume setting moved to after media loading to avoid initialization issues

        # Gestionnaire d'événements pour la fin de piste
        self._event_manager = self._player.event_manager()
        self._event_manager.event_attach(
            vlc.EventType.MediaPlayerEndReached, self._on_end_reached
        )


    def __del__(self):
        try:
            self._player.stop()
            self._player.release()
            self._vlc_instance.release()
        except Exception:
            pass

    # ==========================================================================
    # RECHERCHE ET AJOUT DE PISTES
    # ==========================================================================

    def search_and_play(self, query: str) -> str:
        """
        Recherche une piste YouTube, l'ajoute à la playlist et la lit.

        :param query: terme de recherche.
        :return: titre de la piste trouvée.
        """
        title, url = self._fetch_info(query)
        self._playlist.append({"title": title, "url": url})
        self._current_index = len(self._playlist) - 1
        self._play_url(url)
        return title

    def search_and_queue(self, query: str) -> str:
        """
        Recherche une piste YouTube et l'ajoute à la fin de la playlist
        sans démarrer la lecture.

        :param query: terme de recherche.
        :return: titre de la piste ajoutée.
        """
        title, url = self._fetch_info(query)
        self._playlist.append({"title": title, "url": url})
        return title

    def _fetch_info(self, query: str) -> tuple:
        """
        Récupère le titre et l'URL audio d'une recherche YouTube.

        :return: tuple (title, audio_url)
        """
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)

            if not info or not info.get('entries'):
                raise ValueError("Aucune musique trouvée")

            entry = info['entries'][0]
            audio_url = entry.get('url')

            if not audio_url:
                audio_formats = [
                    f for f in entry.get('formats', [])
                    if f.get('acodec') != 'none' and f.get('url')
                ]
                if not audio_formats:
                    raise ValueError("Aucun format audio disponible")

                best_format = max(
                    audio_formats,
                    key=lambda f: f.get('abr') or f.get('tbr') or f.get('quality') or 0
                )
                audio_url = best_format['url']

            return entry.get('title', query), audio_url

    # ==========================================================================
    # CONTRÔLES DE LECTURE (Play / Pause / Stop)
    # ==========================================================================

    def play(self, index: int = None):
        """
        Démarre ou reprend la lecture.

        :param index: si fourni, joue directement la piste à cet index.
                      Si None, reprend la piste en cours.
        """
        if not self._playlist:
            print("[YouTube] La playlist est vide. Recherchez une piste d'abord.")
            return

        if index is not None:
            if not (0 <= index < len(self._playlist)):
                raise IndexError(f"Index {index} hors de la playlist ({len(self._playlist)} pistes).")
            self._current_index = index
            self._play_url(self._playlist[self._current_index]['url'])
        else:
            # Reprend si en pause, sinon joue la piste courante depuis le début
            state = self._player.get_state()
            if state == vlc.State.Paused:
                self._player.pause()  # toggle pause → lecture
            else:
                self._play_url(self._playlist[self._current_index]['url'])

    def pause(self):
        """
        Met en pause si en lecture, reprend si en pause (toggle).
        """
        self._player.pause()

    def stop(self):
        """
        Arrête complètement la lecture.
        """
        self._player.stop()

    # ==========================================================================
    # NAVIGATION DANS LA PLAYLIST (Suivant / Précédent)
    # ==========================================================================

    def next_track(self):
        """
        Passe à la piste suivante dans la playlist (cyclique).
        En mode shuffle, choisit une piste aléatoire différente.
        """
        if not self._playlist:
            return

        if self._shuffle:
            candidates = [i for i in range(len(self._playlist)) if i != self._current_index]
            if candidates:
                self._current_index = random.choice(candidates)
        else:
            self._current_index = (self._current_index + 1) % len(self._playlist)

        self._play_url(self._playlist[self._current_index]['url'])

    def previous_track(self):
        """
        Revient à la piste précédente dans la playlist (cyclique).
        """
        if not self._playlist:
            return

        self._current_index = (self._current_index - 1) % len(self._playlist)
        self._play_url(self._playlist[self._current_index]['url'])

    # ==========================================================================
    # CONTRÔLE DU VOLUME
    # ==========================================================================

    def set_volume(self, volume: int):
        """
        Définit le volume de lecture.

        :param volume: entier entre 0 (muet) et 100 (maximum).
        """
        if not (0 <= volume <= 100):
            raise ValueError("Le volume doit être compris entre 0 et 100.")
        self._volume = volume
        try:
            self._player.audio_set_volume(self._volume)
        except Exception as e:
            print(f"[YouTube] Warning: Could not set volume to {self._volume}: {e}")

    def get_volume(self) -> int:
        """Retourne le volume actuel (0-100)."""
        try:
            return self._player.audio_get_volume()
        except Exception as e:
            print(f"[YouTube] Warning: Could not get volume: {e}")
            return self._volume  # Return stored value as fallback

    def volume_up(self, step: int = 5):
        """Augmente le volume d'un certain nombre de points (défaut : 5)."""
        self.set_volume(min(100, self.get_volume() + step))

    def volume_down(self, step: int = 5):
        """Diminue le volume d'un certain nombre de points (défaut : 5)."""
        self.set_volume(max(0, self.get_volume() - step))

    # ==========================================================================
    # MODES DE LECTURE (Shuffle / Repeat)
    # ==========================================================================

    def toggle_shuffle(self) -> bool:
        """
        Active ou désactive le mode aléatoire.

        :return: True si le shuffle est maintenant actif, False sinon.
        """
        self._shuffle = not self._shuffle
        return self._shuffle

    def toggle_repeat(self) -> bool:
        """
        Active ou désactive la répétition de la playlist.

        :return: True si le repeat est maintenant actif, False sinon.
        """
        self._repeat = not self._repeat
        return self._repeat

    # ==========================================================================
    # INFORMATIONS SUR LA PISTE EN COURS
    # ==========================================================================

    def get_current_track_name(self) -> str:
        """Retourne le titre de la piste en cours."""
        if not self._playlist:
            return "Aucune piste"
        return self._playlist[self._current_index]['title']

    def get_current_index(self) -> int:
        """Retourne l'index (0-based) de la piste en cours."""
        return self._current_index

    def get_playlist(self) -> list:
        """Retourne la liste des titres de la playlist."""
        return [track['title'] for track in self._playlist]

    def get_duration(self) -> float:
        """
        Retourne la durée totale de la piste en cours en secondes.
        Retourne -1 si non disponible.
        """
        ms = self._player.get_length()
        return ms / 1000 if ms > 0 else -1

    def get_position(self) -> float:
        """
        Retourne la position de lecture actuelle en secondes.
        Retourne -1 si aucune piste n'est en cours.
        """
        ms = self._player.get_time()
        return ms / 1000 if ms >= 0 else -1

    def seek(self, seconds: float):
        """
        Déplace la tête de lecture à une position donnée en secondes.

        :param seconds: position cible en secondes depuis le début.
        """
        ms = int(seconds * 1000)
        self._player.set_time(ms)

    def is_playing(self) -> bool:
        """Retourne True si une piste est en cours de lecture."""
        return self._player.is_playing() == 1

    def get_status(self) -> dict:
        """
        Retourne un dictionnaire récapitulatif de l'état complet du client.
        Interface identique à MusicPlayer.get_status().

        :return: dict avec les clés : track, index, total, playing,
                 volume, shuffle, repeat, position, duration.
        """
        return {
            "track":    self.get_current_track_name(),
            "index":    self._current_index + 1,
            "total":    len(self._playlist),
            "playing":  self.is_playing(),
            "volume":   self.get_volume(),
            "shuffle":  self._shuffle,
            "repeat":   self._repeat,
            "position": round(self.get_position(), 1),
            "duration": round(self.get_duration(), 1),
        }

    # ==========================================================================
    # TÉLÉCHARGEMENT
    # ==========================================================================

    def download_audio(self, query: str, output_path: str = '%(title)s.%(ext)s') -> str:
        """
        Télécharge l'audio de la première vidéo YouTube correspondant à la recherche.

        :param query: terme de recherche.
        :param output_path: chemin de sortie (template yt-dlp).
        :return: titre de la piste téléchargée.
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=True)

                if not info or not info.get('entries'):
                    raise ValueError("Aucune musique trouvée")

                return info['entries'][0].get('title')

        except DownloadError as e:
            raise RuntimeError(f"Échec du téléchargement : {e}") from e

    # ==========================================================================
    # GESTION DES ÉVÉNEMENTS VLC
    # ==========================================================================

    def _on_end_reached(self, event):
        """
        Callback exécuté par VLC à la fin d'une piste.
        Passe automatiquement à la piste suivante et gère la répétition.
        """
        is_last_track = self._current_index == len(self._playlist) - 1

        if not is_last_track:
            # Pas la dernière piste, on passe à la suivante
            self.next_track()
        elif self._repeat:
            # C'est la dernière piste et le mode repeat est activé, on boucle
            self.next_track()
        # Sinon (dernière piste et pas de repeat), la lecture s'arrête.


    # ==========================================================================
    # MÉTHODE INTERNE
    # ==========================================================================

    def _play_url(self, url: str):
        """Arrête la lecture précédente et démarre le nouveau flux."""
        self._player.stop()
        media = self._vlc_instance.media_new(url)
        self._player.set_media(media)
        try:
            self._player.audio_set_volume(self._volume)
        except Exception as e:
            print(f"[YouTube] Warning: Could not set volume: {e}")
        self._player.play()