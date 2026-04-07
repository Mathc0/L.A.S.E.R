"""
YouTube Music Client - L.A.S.E.R
Lecteur audio YouTube avec streaming VLC
"""

import os
import sys
from io import BytesIO
from urllib.request import urlopen
from yt_dlp import YoutubeDL
from PIL import Image
import vlc


class YouTubeMusicClient:
    """
    Client pour écouter de la musique depuis YouTube en streaming direct avec VLC.
    """

    def __init__(self):
        """Initialise le player VLC pour le streaming."""
        # Initialisation VLC pour le streaming
        self.vlc_instance = vlc.Instance()
        self.vlc_player = self.vlc_instance.media_player_new()

        # État de lecture
        self.is_playing = False

    def search_and_play(self, query):
        """
        Recherche et joue une musique YouTube en streaming.

        Args:
            query (str): Terme de recherche
        """
        print(f"🔍 Recherche de: {query}")
        self._play_stream(query)

    def _play_stream(self, query):
        """Mode streaming : joue directement depuis YouTube via VLC."""
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)

                if not info or not info.get('entries'):
                    print("❌ Aucune musique trouvée")
                    return

                entry = info['entries'][0]

                # Trouver le meilleur format audio disponible
                if 'formats' not in entry:
                    print("❌ Formats audio non disponibles")
                    return

                audio_formats = [f for f in entry['formats'] if f.get('acodec') != 'none']
                if not audio_formats:
                    print("❌ Aucun format audio trouvé")
                    return

                # Sélectionner le format avec le meilleur bitrate
                best_format = max(audio_formats,
                                key=lambda f: f.get('abr', 0) or f.get('quality', 0))

                # Afficher la pochette et lancer le stream
                self.display_cover_ascii(entry.get('thumbnail'))
                self.play(best_format['url'], entry['title'])

        except Exception as e:
            print(f"❌ Erreur streaming: {e}")

    def play(self, url=None, title=None):
        """Joue un stream audio avec VLC."""
        if url and title:
            try:
                media = self.vlc_instance.media_new(url)
                self.vlc_player.set_media(media)
                self.vlc_player.play()
                self.is_playing = True
                print(f"🎵 Streaming: {title}")
            except Exception as e:
                print(f"❌ Erreur lors du streaming: {e}")
        else:
            # Reprendre la lecture si elle était en pause
            self.vlc_player.play()
            self.is_playing = True
            print("▶️  Reprise")

    def pause(self):
        """Met en pause la lecture en cours."""
        if self.is_playing:
            self.vlc_player.pause()
            self.is_playing = False
            print("⏸️  Pause")

    def resume(self):
        """Reprend la lecture."""
        self.vlc_player.play()
        self.is_playing = True
        print("▶️  Reprise")

    def stop(self):
        """Arrête complètement la lecture."""
        self.vlc_player.stop()
        self.is_playing = False
        print("⏹️  Arrêt")

    def download_image(self, url):
        """Télécharge une image depuis une URL."""
        with urlopen(url, timeout=15) as response:
            return Image.open(BytesIO(response.read()))

    def image_to_ascii(self, image, width=60):
        """
        Convertit une image en art ASCII.

        Args:
            image: Objet PIL Image
            width: Largeur maximale en caractères

        Returns:
            str: Représentation ASCII de l'image
        """
        # Conversion en niveaux de gris
        image = image.convert("L")

        # Calcul de la taille adaptée au terminal
        try:
            terminal_width = min(width, os.get_terminal_size().columns)
        except OSError:
            terminal_width = width

        orig_w, orig_h = image.size
        new_width = min(terminal_width, orig_w)
        new_height = max(1, int((orig_h / orig_w) * new_width * 0.55))

        # Redimensionnement
        image = image.resize((new_width, new_height))

        # Conversion pixels -> caractères ASCII
        chars = "@%#*+=-:. "
        pixels = list(image.getdata())
        ascii_str = "".join(chars[pixel * len(chars) // 256] for pixel in pixels)

        # Formatage en lignes
        return "\n".join(ascii_str[i:i+new_width]
                        for i in range(0, len(ascii_str), new_width))

    def display_cover_ascii(self, thumbnail_url):
        """Affiche la pochette d'album en ASCII."""
        if not thumbnail_url:
            print("📀 Aucune miniature disponible.")
            return

        print("🎨 Pochette en ASCII:")
        try:
            image = self.download_image(thumbnail_url)
            print(self.image_to_ascii(image))
        except Exception as e:
            print(f"❌ Impossible d'afficher la pochette: {e}")

    def run(self):
        """Boucle principale de l'interface CLI."""
        print("🎵 YouTube Music Client - L.A.S.E.R")
        print("Commandes disponibles:")
        print("  play <recherche>     - Stream direct ⚡ (VLC)")
        print("  pause | resume | stop - Contrôles de lecture")
        print("  quit                 - Quitter l'application")
        print()

        while True:
            try:
                cmd = input("> ").strip().split(maxsplit=1)
                if not cmd:
                    continue

                action = cmd[0].lower()

                if action == "play" and len(cmd) > 1:
                    self.search_and_play(cmd[1])
                elif action == "pause":
                    self.pause()
                elif action == "resume":
                    self.resume()
                elif action == "stop":
                    self.stop()
                elif action == "quit":
                    print("👋 Au revoir !")
                    break
                else:
                    print("❓ Commande inconnue. Tapez 'help' pour voir les commandes.")

            except KeyboardInterrupt:
                print("\n👋 Arrêt de L.A.S.E.R...")
                break


if __name__ == "__main__":
    client = YouTubeMusicClient()
    client.run()