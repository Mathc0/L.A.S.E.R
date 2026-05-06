import time
import client_yt_music
from player import MusicPlayer
from add_audio import add_audio_to_database, DB_PATH
from del_audio import list_musiques, delete_music
import os
# ==============================================================================
# MAIN.PY — Point d'entrée du projet L.A.S.E.R
# Intègre le MusicPlayer (fichiers MP3 locaux) et le client YouTube Music.
# ==============================================================================

# Dossier contenant les fichiers MP3 locaux
MUSIC_FOLDER = "./musiques"


def show_music_progress(player: MusicPlayer):
    """
    Affiche une barre de progression en temps réel pendant la lecture.
    Se met à jour toutes les secondes en fonction de la position réelle dans la piste.
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
    Affiche l'état complet du player : piste, volume, modes actifs.
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
    Indique la piste en cours avec une flèche.
    """
    playlist = player.get_playlist()
    if not playlist:
        print("⚠️  Aucune piste dans la playlist.")
        return

    print(f"\n📋 Playlist ({len(playlist)} piste(s)) :")
    for i, name in enumerate(playlist):
        marker = "▶ " if i == player.get_current_index() else "  "
        print(f"  {marker}{i + 1}. {name}")
    print()


def generic_player_menu(player, player_type: str):
    """
    Menu de contrôle générique pour un lecteur (local ou YouTube).
    Offre un ensemble de commandes unifié pour piloter la lecture.
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
  search [query]→ rechercher et lire une musique (ex: search daft punk)
  add [query]   → ajouter une musique à la playlist
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
                query = " ".join(cmd_parts[1:])
                if not query:
                    print("Usage : search [nom de la musique]")
                    continue
                try:
                    print(f"🔎 Recherche de '{query}'...")
                    title = player.search_and_play(query)
                    print(f"🎵 Lecture de : {title}")
                    show_status(player)
                except Exception as e:
                    print(f"⚠️ Erreur de recherche : {e}")
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
    Sous-menu de contrôle du player MP3 local.
    Permet de contrôler la lecture, le volume, la navigation et les modes.
    """
    print("\n--- Mode MP3 Local ---")
    print("Dossier :", MUSIC_FOLDER)

    # Chargement de la playlist depuis le dossier
    try:
        nb = player.load_folder(MUSIC_FOLDER)
        if nb == 0:
            print(f"⚠️  Aucun fichier MP3 trouvé dans '{MUSIC_FOLDER}'.")
            print("    Ajoutez des fichiers .mp3 dans ce dossier et réessayez.")
            return
        print(f"✅  {nb} piste(s) chargée(s).\n")
    except FileNotFoundError:
        print(f"⚠️  Le dossier '{MUSIC_FOLDER}' n'existe pas.")
        print("    Créez un dossier 'musiques/' à la racine du projet et ajoutez vos MP3.")
        return

    # Démarrage automatique de la première piste
    player.play()
    show_status(player)
    generic_player_menu(player, 'local')


def menu_youtube():
    """
    Sous-menu de recherche et lecture via YouTube Music.
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
        print("  3. download → Télécharger + ajouter en base + lire")
        print("  4. delete   → Supprimer une musique de la base et du dossier")
        print("  5. quit     → Quitter\n")

        try:
            choice = input("Votre choix : ").strip().lower()
        except KeyboardInterrupt:
            print("\nAu revoir !")
            break

        if choice in ("1", "local"):
            menu_local(player)

        elif choice in ("2", "youtube"):
            menu_youtube()

        elif choice in ("3", "download"):
            try:
                query = input("Nom de la musique à télécharger : ")

                # Télécharge + ajoute en base
                result = add_audio_to_database(query, db_path=DB_PATH)

                print(f"\n✅ Ajouté en base : {result['Nom']} - {result['Artiste']}")

                # Chemin du fichier téléchargé
                music_folder = "./musiques"

                # Recharge le player avec les nouvelles musiques
                player.load_folder(music_folder)

                # Trouver l'index de la musique téléchargée
                playlist = player.get_playlist()

                # On cherche la musique par nom
                index = next(
                    (i for i, name in enumerate(playlist) if result['Nom'].lower() in name.lower()),
                    None
                )

                if index is not None:
                    player.play(index)
                    print(f"▶ Lecture : {player.get_current_track_name()}")
                else:
                    print("⚠️ Musique téléchargée mais non trouvée dans la playlist.")

            except Exception as e:
                print(f"❌ Erreur : {e}")

        elif choice in ("4", "delete"):
            rows = list_musiques()
            if not rows:
                print("⚠️  Aucune musique en base.\n")
            else:
                print(f"\n  {'ID':<4} {'Artiste':<20} Nom")
                print("  " + "-" * 65)
                for row_id, nom, artiste, duree in rows:
                    duree_str = f"{duree}s" if duree else "?"
                    print(f"  {row_id:<4} {(artiste or '?'):<20} {nom}  [{duree_str}]")
                print()
                try:
                    raw = input("ID à supprimer (ou 'back' pour annuler) : ").strip()
                    if raw.lower() != "back" and raw.isdigit():
                        music_id = int(raw)
                        if any(r[0] == music_id for r in rows):
                            result = delete_music(music_id)
                            print(f"✅ Supprimé : {result['Nom']}")
                            if result["fichier_supprime"]:
                                print(f"   Fichier supprimé : {result['chemin']}")
                            else:
                                print(f"⚠️  Fichier introuvable : {result['chemin']}")
                        else:
                            print("❌ ID invalide.")
                    else:
                        print("Annulé.")
                except KeyboardInterrupt:
                    print("\nAnnulé.")
            print()

        elif choice in ("5", "quit"):
            print("Merci d'avoir utilisé L.A.S.E.R. À bientôt !")
            break

        else:
            print("Choix invalide, veuillez réessayer.\n")


main()