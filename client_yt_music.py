"""
YouTube Music Client - L.A.S.E.R
Lecteur audio YouTube avec streaming VLC.
Interface identique à MusicPlayer pour une utilisation uniforme.
"""

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import static_ffmpeg
import contextlib
import io
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
            return entry.get('title'), audio_url

    def download_audio(self, query, output_path='%(title)s.%(ext)s'):
        """Télécharge l'audio de la première vidéo YouTube correspondant à la recherche."""
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            static_ffmpeg.add_paths()

        def _progress_hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '').strip()
                print(f"\rTéléchargement... {percent}", end='', flush=True)
            elif d['status'] == 'finished':
                print("\rTéléchargement... 100%           ")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [_progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # Robustesse réseau : retries + fragments + user-agent navigateur
            'retries': 10,
            'fragment_retries': 10,
            'http_chunk_size': 1048576,  # 1 Mo par fragment pour éviter les coupures
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/124.0.0.0 Safari/537.36'
                ),
            },
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