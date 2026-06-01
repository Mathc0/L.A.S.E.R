import time
import client_yt_music
from player import MusicPlayer
import os
from mp3_tagger import tag_mp3_file
from tkinter import Tk, filedialog
# ==============================================================================
# MAIN.PY — Point d'entrée du projet L.A.S.E.R
# Intègre le MusicPlayer (fichiers MP3 locaux) et le client YouTube Music.
# ==============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Dossier contenant les fichiers MP3 locaux (par défaut)
MUSIC_FOLDER = os.path.join(BASE_DIR, "musiques")

def browse_music_folder():
    """
    Ouvre un explorateur de fichiers pour sélectionner un dossier de musiques.
    Retourne le chemin du dossier sélectionné ou None si annulation.
    """
    root = Tk()
    root.withdraw()  # Masque la fenêtre principale de Tkinter
    root.attributes('-topmost', True)  # Place la fenêtre de dialogue au premier plan
    
    folder_path = filedialog.askdirectory(
        title="Sélectionner un dossier de musiques",
        initialdir=os.path.expanduser("~")
    )
    root.destroy()
    
    return folder_path if folder_path else None

def browse_music_files():
    """
    Ouvre un explorateur de fichiers pour sélectionner des fichiers MP3 individuels.
    Retourne une liste de chemins de fichiers ou une liste vide si annulation.
    """
    root = Tk()
    root.withdraw()  # Masque la fenêtre principale de Tkinter
    root.attributes('-topmost', True)
    
    file_paths = filedialog.askopenfilenames(
        title="Sélectionner des fichiers MP3",
        initialdir=os.path.expanduser("~"),
        filetypes=[("Fichiers MP3", "*.mp3"), ("Tous les fichiers", "*.*")]
    )
    root.destroy()
    
    return list(file_paths) if file_paths else []

def auto_tag_music_folder(folder_path: str = None, recursive: bool = True):
    """
    Analyse et met à jour les métadonnées des fichiers MP3 via Discogs.
    Gère les erreurs de manière robuste et ne bloque pas le démarrage.
    
    :param folder_path: chemin du dossier à scanner (défaut: MUSIC_FOLDER)
    :param recursive: si True, cherche dans les sous-dossiers aussi
    """
    if folder_path is None:
        folder_path = MUSIC_FOLDER
    
    if not os.path.isdir(folder_path):
        print(f"⚠️  Dossier '{folder_path}' non trouvé. Ignoré le tagging.")
        return
    
    # Collecte tous les fichiers MP3
    mp3_files = []
    if recursive:
        # Cherche dans tous les sous-dossiers
        for root, dirs, files in os.walk(folder_path):
            for filename in sorted(files):
                if filename.lower().endswith(".mp3"):
                    full_path = os.path.join(root, filename)
                    mp3_files.append(full_path)
    else:
        # Cherche seulement dans le dossier principal
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".mp3"):
                full_path = os.path.join(folder_path, filename)
                mp3_files.append(full_path)
    
    if not mp3_files:
        print(f"ℹ️  Aucun fichier MP3 trouvé dans '{folder_path}'.")
        return
    
    print(f"\n🏷️  Tagging des métadonnées MP3 ({len(mp3_files)} fichier(s))...\n")
    success_count = 0
    
    for file_path in sorted(mp3_files):
        print(f"🔍 Traitement de : {os.path.basename(file_path)}")
        try:
            if tag_mp3_file(file_path):
                success_count += 1
        except Exception as e:
            print(f"   ❌ Erreur inattendue : {e}")
    
    print(f"\n✅ Tagging terminé : {success_count}/{len(mp3_files)} fichier(s) mis à jour.\n")

# Tagging automatique au démarrage (sans bloquer)
try:
    auto_tag_music_folder()
except Exception as e:
    print(f"⚠️  Erreur lors du tagging automatique : {e}\n")


def show_music_progress(player: MusicPlayer):
    """
    Affiche une barre de progression en temps réel pendant la lecture.
    Se met à jour toutes les secondes en fonction de la position réelle dans la piste.
    
    :param player: instance du lecteur de musique
    """
    print()  # saut de ligne avant la barre
    while player.is_playing():
        duration = player.get_duration()
        position = player.get_position()

        # Si la durée n'est pas encore disponible, on attend
        if duration <= 0:
            time.sleep(0.5)
            continue

        # Calcul du pourcentage de progression
        progress = min(position / duration, 1.0)
        filled = int(progress * 30)
        bar = '█' * filled + '-' * (30 - filled)
        percent = int(progress * 100)

        # Affichage de la barre + infos sur la même ligne (écrase la ligne précédente)
        print(
            f"\r🎵 {player.get_current_track_name()} "
            f"|{bar}| {percent}% "
            f"({int(position)}s / {int(duration)}s)",
            end=""
        )
        time.sleep(1)

    print()  # saut de ligne propre après la fin de la barre


def show_status(player: MusicPlayer):
    """
    Affiche l'état complet du lecteur.
    Présente la piste, le volume et les modes actifs.
    
    :param player: instance du lecteur de musique
    """
    s = player.get_status()
    print(
        f"\n🎵 Piste    : {s['track']}\n"
        f"   [{s['index']}/{s['total']}] | "
        f"{'▶  lecture' if s['playing'] else '⏸  pause'} | "
        f"Volume : {s['volume']}/100\n"
        f"   Shuffle : {'ON' if s['shuffle'] else 'OFF'} | "
        f"Repeat  : {'ON' if s['repeat'] else 'OFF'}\n"
    )


def show_playlist(player: MusicPlayer):
    """
    Affiche toutes les pistes chargées dans la playlist locale.
    Indique la piste en cours avec une flèche et le chemin si nécessaire.
    
    :param player: instance du lecteur de musique
    """
    playlist = player.get_playlist()
    playlist_paths = player.get_playlist(show_path=True)
    if not playlist:
        print("⚠️  Aucune piste dans la playlist.")
        return

    # Détermine s'il y a des sous-dossiers
    has_subdirs = any(os.path.dirname(p) != os.path.dirname(playlist_paths[0]) for p in playlist_paths)

    print(f"\n📋 Playlist ({len(playlist)} piste(s)) :")
    for i, name in enumerate(playlist):
        marker = "▶ " if i == player.get_current_index() else "  "
        if has_subdirs and i < len(playlist_paths):
            # Affiche le chemin relatif avec les sous-dossiers
            display_name = os.path.basename(playlist_paths[i])
            parent_dir = os.path.dirname(playlist_paths[i])
            if parent_dir and parent_dir != ".":
                display_name = f"{os.path.basename(parent_dir)} / {display_name}"
            print(f"  {marker}{i + 1}. {display_name}")
        else:
            print(f"  {marker}{i + 1}. {name}")
    print()


def generic_player_menu(player, player_type: str):
    """
    Menu de contrôle générique pour un lecteur (local ou YouTube).
    Offre un ensemble de commandes unifié pour piloter la lecture.
    
    :param player: instance du lecteur (MusicPlayer ou YouTubeMusicClient)
    :param player_type: type de lecteur ('local' ou 'youtube')
    """
    local_help = """
Commandes disponibles :
  play / pause  → reprendre ou mettre en pause
  stop          → arrêter la lecture
  next          → piste suivante
  prev          → piste précédente
  volume [0-100]→ régler le volume  (ex: volume 70)
  shuffle       → activer/désactiver le mode aléatoire
  repeat        → activer/désactiver la répétition
  playlist      → afficher toutes les pistes
  status        → afficher l'état du player
  progress      → afficher la barre de progression
  help          → afficher cette aide
  back          → retourner au menu principal
"""
    youtube_help = """
Commandes disponibles :
  search music [query]    → rechercher et lire une musique  (ex: search music daft punk)
  search playlist [query] → rechercher et lire une playlist (ex: search playlist daft punk)
  add [query]             → ajouter une musique à la playlist
  play / pause            → reprendre ou mettre en pause
  stop                    → arrêter la lecture
  next                    → piste suivante
  prev                    → piste précédente
  volume [0-100]          → régler le volume  (ex: volume 70)
  shuffle                 → activer/désactiver le mode aléatoire
  repeat                  → activer/désactiver la répétition
  playlist                → afficher toutes les pistes
  status                  → afficher l'état du player
  progress                → afficher la barre de progression
  help                    → afficher cette aide
  back                    → retourner au menu principal
"""
    HELP = youtube_help if player_type == 'youtube' else local_help
    print(HELP)

    while True:
        try:
            cmd_full = input("Commande > ").strip()
            cmd_parts = cmd_full.lower().split()
            cmd = cmd_parts[0] if cmd_parts else ""
        except KeyboardInterrupt:
            print("\nRetour au menu principal.")
            player.stop()
            break

        if not cmd:
            continue

        # Commandes spécifiques à YouTube
        if player_type == 'youtube':
            if cmd == "search":
                if len(cmd_parts) < 2:
                    print("Usage : search music [query] | search playlist [query]")
                    continue

                subcommand = cmd_parts[1]

                if subcommand == "music":
                    query = " ".join(cmd_parts[2:])
                    if not query:
                        print("Usage : search music [nom de la musique]")
                        continue
                    try:
                        print(f"🔎 Recherche de '{query}'...")
                        title = player.search_and_play(query)
                        print(f"🎵 Lecture de : {title}")
                        show_status(player)
                    except Exception as e:
                        print(f"⚠️ Erreur de recherche : {e}")

                elif subcommand == "playlist":
                    query = " ".join(cmd_parts[2:])
                    if not query:
                        print("Usage : search playlist [nom de la playlist]")
                        continue
                    try:
                        print(f"🔎 Recherche de la playlist '{query}'...")
                        playlist_title, nb_tracks = player.search_playlist_and_play(query)
                        print(f"🎵 Lecture de la playlist : {playlist_title} ({nb_tracks} pistes)")
                        show_status(player)
                    except Exception as e:
                        print(f"⚠️ Erreur de recherche : {e}")

                else:
                    print("Usage : search music [query] | search playlist [query]")

                continue

            elif cmd == "add":
                query = " ".join(cmd_parts[1:])
                if not query:
                    print("Usage : add [nom de la musique]")
                    continue
                try:
                    print(f"🔎 Recherche et ajout de '{query}'...")
                    title = player.search_and_queue(query)
                    print(f"✅ Ajouté à la playlist : {title}")
                except Exception as e:
                    print(f"⚠️ Erreur d'ajout : {e}")
                continue

        # Commandes communes
        if cmd in ("play", "pause"):
            player.pause()
            print("▶  Lecture" if player.is_playing() else "⏸  Pause")

        elif cmd == "stop":
            player.stop()
            print("⏹  Lecture arrêtée.")

        elif cmd == "next":
            player.next_track()
            print(f"⏭  {player.get_current_track_name()}")

        elif cmd == "prev":
            player.previous_track()
            print(f"⏮  {player.get_current_track_name()}")

        elif cmd == "volume":
            if len(cmd_parts) == 2 and cmd_parts[1].isdigit():
                player.set_volume(int(cmd_parts[1]))
                print(f"🔊 Volume : {player.get_volume()}/100")
            else:
                print("Usage : volume [0-100]  (ex: volume 75)")

        elif cmd == "shuffle":
            state = player.toggle_shuffle()
            print(f"🔀 Shuffle : {'ON' if state else 'OFF'}")

        elif cmd == "repeat":
            state = player.toggle_repeat()
            print(f"🔁 Repeat : {'ON' if state else 'OFF'}")

        elif cmd == "playlist":
            show_playlist(player)

        elif cmd == "status":
            show_status(player)

        elif cmd == "progress":
            try:
                show_music_progress(player)
            except KeyboardInterrupt:
                print("\nProgression interrompue.")
                continue

        elif cmd == "help":
            print(HELP)

        elif cmd == "back":
            player.stop()
            print("Retour au menu principal.")
            break

        else:
            print("Commande inconnue. Tapez 'help' pour la liste des commandes.")


def menu_local(player: MusicPlayer):
    """
    Sous-menu de contrôle du lecteur MP3 local.
    Offre le choix entre parcourir un dossier, des fichiers ou le dossier par défaut.
    
    :param player: instance du lecteur de musique local
    """
    print("\n--- Mode MP3 Local ---")
    print("Comment voulez-vous charger vos musiques ?")
    print("  1. Parcourir un dossier")
    print("  2. Sélectionner des fichiers MP3")
    print("  3. Utiliser le dossier par défaut (./musiques)")
    print("  4. Annuler")
    
    choice = input("\nVotre choix : ").strip().lower()
    
    folder_to_load = None
    files_to_load = []
    recursive = False
    
    if choice in ("1", "parcourir"):
        print("\n📂 Ouverture de l'explorateur de fichiers...")
        folder_to_load = browse_music_folder()
        if not folder_to_load:
            print("Aucun dossier sélectionné. Retour au menu principal.")
            return
        print(f"Dossier sélectionné : {folder_to_load}")
        recursive = True  # Par défaut, inclure les sous-dossiers
        
    elif choice in ("2", "fichiers"):
        print("\n📂 Ouverture de l'explorateur de fichiers...")
        files_to_load = browse_music_files()
        if not files_to_load:
            print("Aucun fichier sélectionné. Retour au menu principal.")
            return
        print(f"{len(files_to_load)} fichier(s) sélectionné(s).")
        
    elif choice in ("3", "défaut"):
        folder_to_load = MUSIC_FOLDER
        recursive = True
        print(f"Dossier par défaut : {folder_to_load}")
        
    else:
        print("Retour au menu principal.")
        return
    
    # Chargement de la playlist
    try:
        if folder_to_load:
            nb = player.load_folder(folder_to_load, recursive=recursive)
        else:
            # Charger les fichiers individuels manuellement
            player._playlist = []
            player._media_list = player._instance.media_list_new()
            for file_path in files_to_load:
                player._playlist.append(file_path)
                media = player._instance.media_new(file_path)
                player._media_list.add_media(media)
            player._list_player.set_media_list(player._media_list)
            player._player = player._list_player.get_media_player()
            try:
                player._player.audio_set_volume(player._volume)
            except Exception as e:
                print(f"[Player] Warning: Could not set initial volume: {e}")
            player._current_index = 0
            nb = len(files_to_load)
        
        if nb == 0:
            print(f"⚠️  Aucun fichier MP3 trouvé.")
            return
        print(f"✅  {nb} piste(s) chargée(s).\n")
        
        # Tagging automatique des métadonnées
        try:
            if folder_to_load:
                auto_tag_music_folder(folder_to_load, recursive=recursive)
            else:
                # Pour les fichiers individuels, on tagge chaque fichier
                print(f"\n🏷️  Tagging des métadonnées MP3 ({len(files_to_load)} fichier(s))...\n")
                success_count = 0
                for file_path in sorted(files_to_load):
                    print(f"🔍 Traitement de : {os.path.basename(file_path)}")
                    try:
                        if tag_mp3_file(file_path):
                            success_count += 1
                    except Exception as e:
                        print(f"   ❌ Erreur inattendue : {e}")
                print(f"\n✅ Tagging terminé : {success_count}/{len(files_to_load)} fichier(s) mis à jour.\n")
        except Exception as e:
            print(f"⚠️  Erreur lors du tagging automatique : {e}\n")
        
    except FileNotFoundError:
        print(f"⚠️  Le dossier sélectionné n'existe pas.")
        return
    except Exception as e:
        print(f"⚠️  Erreur lors du chargement : {e}")
        return
    
    # Démarrage automatique de la première piste
    player.play()
    show_status(player)
    generic_player_menu(player, 'local')


def menu_tagging():
    """
    Sous-menu pour lancer le tagger manuellement depuis le menu principal.
    Permet de sélectionner des dossiers ou fichiers à tagger avec MusicBrainz.
    """
    print("\n--- Tagging MP3 ---")
    print("  1. Tagger le dossier par défaut ('./musiques')")
    print("  2. Sélectionner un dossier à tagger")
    print("  3. Sélectionner des fichiers MP3 à tagger")
    print("  4. Annuler")

    choice = input("Votre choix : ").strip().lower()

    if choice in ("1", "défaut"):
        folder_path = MUSIC_FOLDER
        recursive = True
    elif choice in ("2", "dossier"):
        folder_path = browse_music_folder()
        if not folder_path:
            print("Aucun dossier sélectionné. Retour au menu principal.")
            return
        recursive = True
    elif choice in ("3", "fichiers"):
        file_paths = browse_music_files()
        if not file_paths:
            print("Aucun fichier sélectionné. Retour au menu principal.")
            return
        print(f"\n🏷️  Tagging des métadonnées MP3 ({len(file_paths)} fichier(s))...\n")
        success_count = 0
        for file_path in sorted(file_paths):
            print(f"🔍 Traitement de : {os.path.basename(file_path)}")
            try:
                if tag_mp3_file(file_path):
                    success_count += 1
            except Exception as e:
                print(f"   ❌ Erreur inattendue : {e}")
        print(f"\n✅ Tagging terminé : {success_count}/{len(file_paths)} fichier(s) mis à jour.\n")
        return
    else:
        print("Retour au menu principal.")
        return

    auto_tag_music_folder(folder_path, recursive=recursive)


def menu_youtube():
    """
    Sous-menu de recherche et lecture via YouTube Music.
    Permet de chercher et lire des musiques depuis YouTube.
    """
    print("\n--- Mode YouTube Music ---")
    client = client_yt_music.YouTubeMusicClient()
    print("Utilisez 'search [musique]' pour commencer ou 'help' pour les commandes.")
    generic_player_menu(client, 'youtube')


def main():
    """
    Menu principal de L.A.S.E.R.
    Permet de choisir entre le mode MP3 local et le mode YouTube Music.
    """
    # Initialisation du player local (sans charger de dossier pour l'instant)
    player = MusicPlayer()

    print("╔══════════════════════════════════════════════╗")
    print("║  Bienvenue dans L.A.S.E.R                    ║")
    print("║  Lecteur Audio de Streaming pour la Musique  ║")
    print("╚══════════════════════════════════════════════╝\n")

    while True:
        print("Que voulez-vous faire ?")
        print("  1. local    → Lire des MP3 depuis le dossier 'musiques/'")
        print("  2. youtube  → Rechercher une musique sur YouTube Music")
        print("  3. tag      → Tagger des MP3 avec MusicBrainz")
        print("  4. quit     → Quitter\n")

        try:
            choice = input("Votre choix : ").strip().lower()
        except KeyboardInterrupt:
            print("\nAu revoir !")
            break

        if choice in ("1", "local"):
            menu_local(player)

        elif choice in ("2", "youtube"):
            menu_youtube()

        elif choice in ("3", "tag"):
            menu_tagging()

        elif choice in ("4", "quit"):
            print("Merci d'avoir utilisé L.A.S.E.R. À bientôt !")
            break

        else:
            print("Choix invalide, veuillez réessayer.\n")


main()