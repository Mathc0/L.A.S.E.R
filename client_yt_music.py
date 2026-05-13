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
import urllib.parse

import platform

vlc_path = os.path.join(os.getcwd(), "vlc_files")
os.environ['PATH'] += os.pathsep + vlc_path
import vlc


class YouTubeMusicClient:
    """
    Client YouTube Music avec streaming VLC.

    Fonctionnalités :
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
        vlc_args = ['--no-video', '--quiet', '--verbose=-1']
        if platform.system() == 'Linux':
            vlc_args.append('--aout=pulse')
        self._vlc_instance = vlc.Instance(vlc_args)
        self._vlc_instance.log_unset()
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
        self._playlist.append({"title": title, "url": url, "video_url": None})
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
        self._playlist.append({"title": title, "url": url, "video_url": None})
        return title

    def search_playlist_and_play(self, query: str) -> tuple:
        """
        Recherche une playlist YouTube, charge toutes ses pistes (lazy)
        et démarre la lecture de la première.

        :param query: terme de recherche de la playlist.
        :return: (titre_playlist, nombre_de_pistes)
        """
        playlist_title, tracks = self._fetch_playlist_videos(query)

        if not tracks:
            raise ValueError("Aucune piste trouvée dans la playlist")

        start_index = len(self._playlist)
        for title, video_url in tracks:
            self._playlist.append({"title": title, "url": None, "video_url": video_url})

        self._current_index = start_index
        self._play_current_track()
        return playlist_title, len(tracks)

    def _fetch_playlist_videos(self, query: str) -> tuple:
        """
        Recherche une playlist YouTube et retourne (titre_playlist, [(titre, video_url)]).
        Utilise le filtre playlist de YouTube pour ne chercher que des playlists.
        """
        encoded_query = urllib.parse.quote_plus(query)
        # sp=EgIQAw%3D%3D filtre les résultats pour n'afficher que les playlists
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAw%3D%3D"

        flat_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlistend': 3,
        }

        with YoutubeDL(flat_opts) as ydl:
            search_results = ydl.extract_info(search_url, download=False)

        if not search_results or not search_results.get('entries'):
            raise ValueError("Aucune playlist trouvée pour cette recherche")

        first_result = search_results['entries'][0]
        playlist_url = first_result.get('url') or first_result.get('webpage_url', '')
        playlist_id = first_result.get('id', '')
        if playlist_id and not playlist_url.startswith('http'):
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        playlist_title = first_result.get('title', query)

        tracks_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        tracks = []
        with YoutubeDL(tracks_opts) as ydl:
            playlist_data = ydl.extract_info(playlist_url, download=False)

        if not playlist_data:
            raise ValueError("Impossible d'extraire les données de la playlist")

        for entry in playlist_data.get('entries') or []:
            if not entry:
                continue
            title = entry.get('title', 'Titre inconnu')
            video_id = entry.get('id', '')
            video_url = entry.get('url') or entry.get('webpage_url', '')
            if video_id and not (video_url and video_url.startswith('http')):
                video_url = f"https://www.youtube.com/watch?v={video_id}"
            if video_url:
                tracks.append((title, video_url))

        if not tracks:
            raise ValueError("La playlist est vide ou inaccessible")

        return playlist_title, tracks

    def _resolve_audio_url(self, video_url: str) -> str:
        """Résout l'URL du flux audio à partir de l'URL d'une vidéo YouTube."""
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        if not info:
            raise ValueError(f"Impossible d'extraire l'audio : {video_url}")

        audio_url = info.get('url')
        if not audio_url:
            audio_formats = [
                f for f in info.get('formats', [])
                if f.get('acodec') != 'none' and f.get('url')
            ]
            if not audio_formats:
                raise ValueError("Aucun format audio disponible")
            best_format = max(
                audio_formats,
                key=lambda f: f.get('abr') or f.get('tbr') or f.get('quality') or 0
            )
            audio_url = best_format['url']

        return audio_url

    def _play_current_track(self):
        """Joue la piste courante, en résolvant l'URL audio si nécessaire."""
        track = self._playlist[self._current_index]
        if not track.get('url'):
            if not track.get('video_url'):
                raise ValueError("Aucune URL disponible pour cette piste")
            track['url'] = self._resolve_audio_url(track['video_url'])
        self._play_url(track['url'])

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

    def get_current_track_name(self) -> str:
        """Retourne le titre de la piste actuellement sélectionnée."""
        if not self._playlist:
            return "Aucune piste"
        return self._playlist[self._current_index]["title"]

    def get_current_index(self) -> int:
        return self._current_index

    def get_playlist(self) -> list:
        return [item["title"] for item in self._playlist]

    def get_volume(self) -> int:
        return self._volume

    def set_volume(self, value: int):
        self._volume = max(0, min(100, int(value)))
        try:
            self._player.audio_set_volume(self._volume)
        except Exception:
            pass

    def pause(self):
        """Met en pause ou reprend la lecture."""
        self._player.pause()

    def stop(self):
        self._player.stop()

    def next_track(self):
        if not self._playlist:
            return
        if self._shuffle:
            self._current_index = random.randrange(len(self._playlist))
        else:
            self._current_index = (self._current_index + 1) % len(self._playlist)
        self._play_current_track()

    def previous_track(self):
        if not self._playlist:
            return
        if self._shuffle:
            self._current_index = random.randrange(len(self._playlist))
        else:
            self._current_index = (self._current_index - 1) % len(self._playlist)
        self._play_current_track()

    def toggle_shuffle(self) -> bool:
        self._shuffle = not self._shuffle
        return self._shuffle

    def toggle_repeat(self) -> bool:
        self._repeat = not self._repeat
        return self._repeat

    def get_status(self) -> dict:
        return {
            "track": self.get_current_track_name(),
            "index": self._current_index + 1,
            "total": len(self._playlist),
            "playing": self.is_playing(),
            "volume": self.get_volume(),
            "shuffle": self._shuffle,
            "repeat": self._repeat,
            "position": round(self.get_position(), 1),
            "duration": round(self.get_duration(), 1),
        }

    def is_playing(self) -> bool:
        return self._player.is_playing() == 1

    def get_duration(self) -> float:
        ms = self._player.get_length()
        return ms / 1000 if ms > 0 else -1

    def get_position(self) -> float:
        ms = self._player.get_time()
        return ms / 1000 if ms >= 0 else -1