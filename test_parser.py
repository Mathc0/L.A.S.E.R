from mp3_tagger import parse_filename_metadata

test_files = [
    'Muse - Absolution - 01 - Intro.mp3',
    'Muse - Absolution - 02 - Apocalypse Please.mp3',
    'Muse - Absolution - 03 - Time Is Running Out.mp3',
    'Artist - Title.mp3',
    'Just a title.mp3'
]

print("Test du parsing des noms de fichiers:")
for f in test_files:
    artist, album, title = parse_filename_metadata(f)
    print(f'{f}')
    print(f'  -> Artiste: "{artist}", Album: "{album}", Titre: "{title}"')
    print()