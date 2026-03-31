import pygame
import sys

def play_mp3(filename):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        
        print(f"Lecture de: {filename}")
        
        while pygame.mixer.music.get_busy():
            pass
        
        print("Lecture terminée")
    except FileNotFoundError:
        print(f"Erreur: Le fichier '{filename}' n'existe pas")
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        pygame.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        play_mp3(filename)
    else:
        print("Usage: python main.py <chemin_du_fichier.mp3>")