import openai
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Lade Umgebungsvariablen aus der .env Datei
load_dotenv()

# Setze OpenAI-API-Zugangsdaten
openai.api_key = os.getenv("OPENAI_API_KEY")

# Setze Spotify-API-Zugangsdaten
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                                               client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                                               redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                                               scope=("playlist-modify-public", "playlist-modify-private", "user-library-modify"),
                                               cache_path=".spotipy_cache"))

# Benutzereingaben
playlist_theme = input("Thema oder Musikart: ")
playlist_name = input("Name der Playlist: ")
playlist_length = int(input("Wie viele Songs sollen in die Playlist (max. 50): "))

# Funktion zum Abrufen von Song-Vorschlägen von der ChatGPT-API
def get_song_suggestions(theme, length):
    try:
        prompt = f"Create a Spotify Playlist with {length} Songs for the theme '{theme}'. Provide song titles."
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.5
        )
        song_suggestions = response.choices[0].message['content'].strip().split("\n")
        return song_suggestions
    except openai.error.OpenAIError as e:
        print(f"Fehler bei der Anfrage an OpenAI: {e}")
        return []

# Erstelle eine Spotify-Playlist
def create_spotify_playlist(song_ids, playlist_name, description):
    try:
        user_id = sp.me()["id"]
        playlist = sp.user_playlist_create(user_id, playlist_name, public=True, description=description)
        sp.playlist_add_items(playlist["id"], song_ids)
        return playlist
    except spotipy.exceptions.SpotifyException as e:
        print(f"Fehler beim Erstellen der Spotify-Playlist: {e}")
        return None

# Hole die Spotify-IDs der Songs
def get_song_ids(song_titles):
    song_ids = []
    for title in song_titles:
        try:
            results = sp.search(q=title, type="track", limit=1)
            if results["tracks"]["items"]:
                song_ids.append(results["tracks"]["items"][0]["id"])
        except spotipy.exceptions.SpotifyException as e:
            print(f"Fehler bei der Spotify-Suche nach dem Song '{title}': {e}")
    return song_ids

if __name__ == "__main__":
    song_titles = get_song_suggestions(playlist_theme, playlist_length)
    if song_titles:
        print("Song Vorschläge:", song_titles)
        song_ids = get_song_ids(song_titles)
        if song_ids:
            playlist = create_spotify_playlist(song_ids, playlist_name, f"Eine Playlist zum Thema: {playlist_theme}")
            if playlist:
                print(f"Die Playlist '{playlist_name}' wurde erstellt: {playlist['external_urls']['spotify']}")
            else:
                print("Fehler beim Erstellen der Playlist.")
        else:
            print("Keine passenden Songs gefunden.")
    else:
        print("Keine Song-Vorschläge erhalten.")