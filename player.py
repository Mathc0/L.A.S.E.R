import os

# --- Configuration du chemin vers les fichiers VLC locaux ---
# Ces lignes permettent à Python de trouver les DLL de VLC
# dans le sous-dossier "vlc_files" du projet, sans avoir besoin
# que VLC soit installé sur le système.
vlc_path = os.path.join(os.getcwd(), "vlc_files")
os.environ['PATH'] += os.pathsep + vlc_path
import vlc

import time

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
        # On crée une instance VLC (le moteur principal) ainsi qu'un
        # MediaListPlayer qui gère la lecture d'une liste de pistes.
        self._instance = vlc.Instance()
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

        # Applique le volume par défaut
        self._player.audio_set_volume(self._volume)

        # --- Chargement automatique si un dossier est fourni ---
        if music_folder:
            self.load_folder(music_folder)

    # ==========================================================================
    # CHARGEMENT DE LA PLAYLIST
    # ==========================================================================

    def load_folder(self, folder_path: str) -> int:
        """
        Charge tous les fichiers MP3 d'un dossier dans la playlist.
        Efface l'ancienne playlist avant de charger la nouvelle.

        :param folder_path: chemin du dossier à scanner.
        :return: nombre de fichiers MP3 trouvés et chargés.
        """
        if not os.path.isdir(folder_path):
            raise FileNotFoundError(f"Dossier introuvable : {folder_path}")

        # Réinitialise la playlist interne et la liste VLC
        self._playlist = []
        self._media_list = self._instance.media_list_new()

        # Parcourt le dossier et ajoute chaque .mp3 à la playlist
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".mp3"):
                full_path = os.path.join(folder_path, filename)
                self._playlist.append(full_path)
                # Crée un objet Media VLC et l'ajoute à la liste VLC
                media = self._instance.media_new(full_path)
                self._media_list.add_media(media)

        # Associe la nouvelle liste VLC au player
        self._list_player.set_media_list(self._media_list)
        self._player = self._list_player.get_media_player()
        self._player.audio_set_volume(self._volume)
        self._current_index = 0

        return len(self._playlist)

    def add_track(self, file_path: str):
        """
        Ajoute un seul fichier MP3 à la playlist existante.

        :param file_path: chemin absolu ou relatif vers le fichier .mp3.
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
        Démarre ou reprend la lecture.

        :param index: si fourni, démarre directement la piste à cet index.
                      Si None, reprend la piste en cours (ou la première).
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
        else:
            # Reprend la lecture (ou démarre depuis le début si rien n'est en cours)
            self._list_player.play()

    def pause(self):
        """
        Met en pause si en lecture, reprend si en pause (toggle).
        """
        # VLC gère automatiquement le toggle play/pause avec cette méthode
        self._list_player.pause()

    def stop(self):
        """
        Arrête complètement la lecture et remet la position à zéro.
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

    def previous_track(self):
        """
        Revient à la piste précédente dans la playlist.
        Va à la dernière piste si on est à la première (comportement cyclique).
        """
        if not self._playlist:
            return

        self._current_index = (self._current_index - 1) % len(self._playlist)
        self._list_player.play_item_at_index(self._current_index)

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
        self._player.audio_set_volume(self._volume)

    def get_volume(self) -> int:
        """
        Retourne le volume actuel (0-100).
        """
        return self._player.audio_get_volume()

    def volume_up(self, step: int = 5):
        """
        Augmente le volume d'un certain nombre de points.

        :param step: nombre de points à ajouter (défaut : 5).
        """
        self.set_volume(min(100, self.get_volume() + step))

    def volume_down(self, step: int = 5):
        """
        Diminue le volume d'un certain nombre de points.

        :param step: nombre de points à retirer (défaut : 5).
        """
        self.set_volume(max(0, self.get_volume() - step))

    # ==========================================================================
    # MODES DE LECTURE (Shuffle / Repeat)
    # ==========================================================================

    def toggle_shuffle(self) -> bool:
        """
        Active ou désactive le mode aléatoire (shuffle).

        :return: True si le shuffle est maintenant actif, False sinon.
        """
        self._shuffle = not self._shuffle
        return self._shuffle

    def toggle_repeat(self) -> bool:
        """
        Active ou désactive la répétition de la playlist complète.
        En mode repeat, la playlist recommence automatiquement à la fin.

        :return: True si le repeat est maintenant actif, False sinon.
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

    def get_current_track_name(self) -> str:
        """
        Retourne le nom du fichier de la piste en cours (sans l'extension).

        :return: nom de la piste ou "Aucune piste" si la playlist est vide.
        """
        if not self._playlist:
            return "Aucune piste"
        filename = os.path.basename(self._playlist[self._current_index])
        return os.path.splitext(filename)[0]   # supprime l'extension .mp3

    def get_current_index(self) -> int:
        """
        Retourne l'index (0-based) de la piste en cours de lecture.
        """
        return self._current_index

    def get_playlist(self) -> list:
        """
        Retourne la liste de tous les noms de pistes (sans extension) de la playlist.

        :return: liste de chaînes de caractères.
        """
        return [
            os.path.splitext(os.path.basename(p))[0]
            for p in self._playlist
        ]

    def get_duration(self) -> float:
        """
        Retourne la durée totale de la piste en cours en secondes.
        Retourne -1 si la durée n'est pas encore disponible (piste non chargée).
        """
        ms = self._player.get_length()  # durée en millisecondes
        return ms / 1000 if ms > 0 else -1

    def get_position(self) -> float:
        """
        Retourne la position de lecture actuelle en secondes.
        Retourne -1 si aucune piste n'est en cours.
        """
        ms = self._player.get_time()    # position en millisecondes
        return ms / 1000 if ms >= 0 else -1

    def seek(self, seconds: float):
        """
        Déplace la tête de lecture à une position donnée en secondes.

        :param seconds: position cible en secondes depuis le début.
        """
        ms = int(seconds * 1000)
        self._player.set_time(ms)

    def is_playing(self) -> bool:
        """
        Indique si le player est actuellement en train de lire.

        :return: True si en lecture, False sinon.
        """
        return self._player.is_playing() == 1

    def get_status(self) -> dict:
        """
        Retourne un dictionnaire récapitulatif de l'état complet du player.
        Pratique pour afficher l'état dans main.py ou une interface CLI.

        :return: dict avec les clés : track, index, total, playing,
                 volume, shuffle, repeat, position, duration.
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