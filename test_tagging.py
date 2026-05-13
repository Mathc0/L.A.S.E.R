#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(__file__))

from mp3_tagger import tag_mp3_file

# Test sur un fichier spécifique
test_file = r"musiques/Absolution/Muse - Absolution - 01 - Intro.mp3"
if os.path.exists(test_file):
    print(f"Test du tagging sur : {test_file}")
    result = tag_mp3_file(test_file)
    print(f"Résultat : {'Succès' if result else 'Échec'}")
else:
    print(f"Fichier test non trouvé : {test_file}")
    # Liste des fichiers disponibles
    print("Fichiers disponibles dans musiques/:")
    for root, dirs, files in os.walk("musiques"):
        for file in files:
            if file.lower().endswith('.mp3'):
                print(f"  {os.path.join(root, file)}")