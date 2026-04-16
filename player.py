import os
vlc_path = os.path.join(os.getcwd(), "vlc_files")
os.environ['PATH'] += os.pathsep + vlc_path
import vlc