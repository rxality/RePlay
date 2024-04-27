# RePlay, An MP3 player program.
# Copyright (C) 2024  Ruben

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import io
import json
import pathlib
import random
import shutil
import tkinter
import typing
import webbrowser
from enum import Enum
from tkinter import filedialog, ttk

import pygame
from PIL import Image, ImageTk
from tinytag import TinyTag

backup_dir = pathlib.Path("backup")
backup_settings = pathlib.Path("backup\\settings.json")
settings = pathlib.Path("settings.json")

if not backup_dir.exists():
    backup_dir.mkdir()

if not settings.exists() and backup_settings.exists():
    shutil.copy(backup_settings, settings)

if not settings.exists() and not backup_settings.exists():
    default_settings = {
        "theme": 1,
        "directory": "tracks\\",
        "volume": 50
    }

    with open("settings.json", "w") as file:
        json.dump(default_settings, file, indent=4)

with open(settings, "r") as file:
    SETTINGS = json.load(file)

DEFAULT = {
    "title": "RePlay: MP3 Player",
    "geometry": "768x576", # Aspect Ratio 1.33 (4:3)
    "resizable": {"width": False, "height": False},
}

class Mode(Enum):
    """An enumeration to define the theme modes for the music player.

    Attributes:
        LIGHT_MODE (int): Represents the light theme mode.
        DARK_MODE (int): Represents the dark theme mode.
    """
    LIGHT_MODE = 1
    DARK_MODE = 2

class Repeat(Enum):
    """An enumeration to define the repeat modes for the music player.

    Attributes:
        OFF (int): Represents the mode where no track is repeated.
        ONE (int): Represents the mode where the current track is repeated.
        ALL (int): Represents the mode where all tracks in the playlist are repeated.
    """
    OFF = 0
    ONE = 1
    ALL = 2

class Player(tkinter.Tk):
    """A class representing the main window of the MP3 player application, inheriting from tkinter.Tk.
    
    This class encapsulates the functionality of the MP3 player, including UI setup, event handling,
    audio playback control, and playlist management. It utilizes pygame for audio playback and tkinter
    for the graphical user interface.
    
    Attributes:
        playlist (dict): A dictionary storing the playlist where keys are track indices and values are track information.
        now_playing (dict): A dictionary storing information about the currently playing track.
        existing_tracks (list): A list of paths to tracks that have been added to the playlist.
        volume (int): The current volume level of the player, loaded from settings.
        track_progress (int): The current playback position of the currently playing track in seconds.
        track_duration (int): The duration of the currently playing track in seconds.
        is_muted (bool): A flag indicating whether the audio is currently muted.
        is_playing (bool): A flag indicating whether a track is currently playing.
        show_artwork (bool): A flag indicating whether the artwork of the currently playing track should be displayed.
        selected_index (int | None): The index of the currently selected track in the playlist, if any.
        can_shuffle (bool): A flag indicating whether the playlist can be shuffled.
        can_reorder (bool): A flag indicating whether tracks in the playlist can be reordered.
        can_edit (bool): A flag indicating whether the application is currently able to edit settings or track information.
    
    Methods:
        __init__(self): Initializes the Player class, setting up the main window, loading settings, and initializing audio playback.
        mode(self) -> Mode: Gets the current theme mode of the application.
        mode(self, value: str) -> None: Sets the theme mode of the application.
        repeat(self) -> Repeat: Gets the current repeat mode of the player.
        repeat(self, value: Repeat) -> None: Sets the repeat mode of the player.
        update_repeat(self) -> None: Cycles through the repeat modes of the music player.
        toggle_mute(self) -> None: Toggles the mute state of the player.
        readable_duration(self, duration: int | float) -> str: Converts a duration in seconds to a human-readable format.
        update_track_progress(self): Updates the track's progress every second when a track is playing.
        populate_track_info(self, path: pathlib.WindowsPath) -> int | None: Adds a track to the playlist and returns its index.
        play(self): Initiates playback of the current or first track in the playlist.
        update_playing_track(self, index: int, track_info: dict) -> None: Updates the player with the currently selected track's information.
        restart(self) -> None: Restarts the current track or plays the previous track if the current track has just started.
        previous(self) -> None: Plays the previous track in the playlist or restarts the current track.
        next(self, finished: bool = False) -> None: Advances to the next track in the playlist or handles repeat functionality.
        toggle_playback(self) -> None: Toggles the playback state of the media player.
        get_now_playing(self) -> typing.Tuple[int, dict]: Retrieves the index and information of the currently playing track.
        shuffle_tracks(self) -> None: Shuffles the tracks in the playlist.
        decrease_volume(self) -> None: Decreases the volume of the audio playback.
        increase_volume(self) -> None: Increases the volume of the audio playback.
        backup_settings(self) -> None: Backs up the settings.json file on startup.
        load_backup(self) -> None: Loads the settings.json file from the backup.
        updating_volume(self) -> None: Updates the volume setting in the settings.json file.
        adjust_volume(self, value: str) -> None: Adjusts the volume of the audio playback based on the slider value.
        toggle_artwork(self) -> None: Toggles the display of the artwork for the currently playing track.
        reorder_now_playing(self) -> None: Reorders the tracks in the UI and highlights the currently playing track.
        set_to_default(self) -> None: Resets the player UI to its default state when no track is playing.
        play_selected_track(self, event: tkinter.Event) -> None: Plays a track selected from the listbox.
        set_track_position(self, event: tkinter.Event): Sets the playback position based on user interaction with the progress bar.
        select_track(self, event: tkinter.Event): Selects a track from the listbox based on the mouse click position.
        swap_track_index(self, event: tkinter.Event) -> None: Reorders tracks in the playlist based on drag-and-drop actions.
        remove_tracks(self) -> None: Removes selected tracks from the playlist and filesystem.
        add_tracks(self) -> None: Adds selected tracks to the playlist.
    """
    playlist = {}
    now_playing = {}

    existing_tracks = []

    volume = SETTINGS["volume"]

    track_progress = 0
    track_duration = 0

    is_muted = False
    is_playing = False
    show_artwork = False
    selected_index = None
    can_shuffle = True
    can_reorder = True
    can_edit = True

    def __init__(self):
        """Initializes the Player class, setting up the main window, loading settings, initializing the pygame mixer for audio playback,
        and loading assets for both light and dark themes.
        """
        super().__init__()
        self._repeat = Repeat.OFF
        self._mode = Mode(SETTINGS["theme"]).name.lower()
        self.startup_theme = tkinter.IntVar(value=SETTINGS["theme"])
        
        pygame.mixer.init()
        self.mixer = pygame.mixer.music
        self.mixer.set_volume(self.volume / 100)
        
        for key, value in DEFAULT.items():
            func = getattr(self, f"wm_{key}")
            func(**value) if isinstance(value, dict) else func(value)
        
        self.wm_iconbitmap("assets\\icon.ico")

        light_path = pathlib.Path("assets\\light_mode\\")
        dark_path = pathlib.Path("assets\\dark_mode\\")
        for file in light_path.iterdir():
            if file.suffix in [".png"]:
                name = file.stem.upper()
                if "ALT_" in name:
                    value = ImageTk.PhotoImage(Image.open(file).resize((256, 256)))

                else:
                    value = ImageTk.PhotoImage(Image.open(file).resize((32, 32)))
                
                setattr(self, f"{light_path.name}_{name}".upper(), value)

        for file in dark_path.iterdir():
            if file.suffix in [".png"]:
                name = file.stem.upper()
                if "ALT_" in name:
                    value = ImageTk.PhotoImage(Image.open(file).resize((256, 256)))

                else:
                    value = ImageTk.PhotoImage(Image.open(file).resize((32, 32)))

                setattr(self, f"{dark_path.name}_{name}".upper(), value)

        self.columnconfigure(8, weight=1)
        self.rowconfigure(16, weight=1)

        self.canvas()
        self.watchdog()

    @property
    def mode(self) -> Mode:
        """Gets the current mode.

        Returns:
            Repeat: The current mode as defined by the Mode enum (LIGHT_MODE, DARK_MODE).
        """
        return self._mode

    @mode.setter
    def mode(self, value: str) -> int:
        """Sets the application's theme mode to either light or dark.

        Args:
            value (str): The theme mode to set. Must be either 'light_mode' or 'dark_mode'.

        Raises:
            ValueError: If the provided value is not 'light_mode' or 'dark_mode'.
        """
        if value not in ["light_mode", "dark_mode"]:
            raise ValueError("Mode must be 'light_mode' or 'dark_mode'")

        self._mode = value
        self.update_theme()

    @property
    def repeat(self) -> Repeat:
        """Gets the current repeat mode.

        Returns:
            Repeat: The current repeat mode as defined by the Repeat enum (OFF, ONE, ALL).
        """
        return self._repeat

    @repeat.setter
    def repeat(self, value: Repeat) -> None:
        """Sets the repeat mode.

        Args:
            value (Repeat): The repeat mode to set.

        Raises:
            ValueError: If the provided value is not an instance of the Repeat enum.
        """
        if not isinstance(value, Repeat):
            raise ValueError("repeat must be an instance of Repeat Enum")

        self._repeat = value
        if self._repeat == Repeat.OFF:
            self.repeat_button.configure(image=self.LIGHT_MODE_REPEAT if self.mode == "light_mode" else self.DARK_MODE_REPEAT)

        elif self._repeat == Repeat.ONE:
            self.repeat_button.configure(image=self.LIGHT_MODE_REPEAT_TRACK if self.mode == "light_mode" else self.DARK_MODE_REPEAT_TRACK)

        else:
            self.repeat_button.configure(image=self.LIGHT_MODE_REPEAT_ALL if self.mode == "light_mode" else self.DARK_MODE_REPEAT_ALL)

    def update_repeat(self) -> None:
        """Cycles through the repeat modes of the music player.

        This method cycles the player's repeat mode in the following order:
        OFF -> ONE -> ALL -> OFF. It updates the player's repeat state accordingly.
        """
        if self.repeat == Repeat.OFF:
            self.repeat = Repeat.ONE
        
        elif self.repeat == Repeat.ONE:
            self.repeat = Repeat.ALL
        
        else:
            self.repeat = Repeat.OFF

    def toggle_mute(self) -> None:
        """Toggles the mute state of the player.
        """
        if not self.is_muted:
            self.is_muted = True
            self.muted_unmuted.config(image=self.LIGHT_MODE_MUTED if self.mode == "light_mode" else self.DARK_MODE_MUTED)
            self.mixer.set_volume(0)

        else:
            self.is_muted = False
            self.muted_unmuted.config(image=self.LIGHT_MODE_UNMUTED if self.mode == "light_mode" else self.DARK_MODE_UNMUTED)
            self.mixer.set_volume(self.volume / 100)
    
    def readable_duration(self, duration: int | float) -> str:
        """Converts a duration from seconds into a human-readable HH:MM:SS format.

        Args:
            duration (int | float): The duration in seconds to be converted.

        Returns:
            str: The duration formatted as a string in HH:MM:SS format.
        """
        hours = int(duration / 3600)
        minutes = int((duration - hours * 3600) / 60)
        seconds = int((duration - hours * 3600 - minutes * 60))
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def update_track_progress(self):
        """Updates the track's progress every second when a track is playing.
        """
        try:
            self.after_cancel(self.repeater)
        except AttributeError:
            ...

        if self.is_playing:
            if self.track_progress < self.track_duration:
                self.track_progress += 1
                self.track_position.configure(value=self.track_progress)
                self.track_duration_text.configure(text=self.readable_duration(self.track_duration - self.track_progress))
                self.updater = self.after(1000, self.update_track_progress)
            
            elif self.track_progress >= self.track_duration:
                self.next(finished=True)
            
        else:
            self.repeater = self.after(1000, self.update_track_progress)

    def populate_track_info(self, path: pathlib.WindowsPath) -> int | None:
        """Populates the track information into the playlist from a given file path.

        Args:
            path (pathlib.WindowsPath): The file path of the audio track to be added to the playlist.

        Returns:
            int | None: The index of the track in the playlist if added successfully, None if the track is already in the playlist.
        """
        track_path = path.as_posix().replace("/", "\\")
        index = len(self.playlist)
        audio = TinyTag.get(track_path, image=True)
        title = audio.title
        album = audio.album
        artist = audio.artist
        duration = audio.duration
        artwork = audio.get_image()

        for _, track_info in self.playlist.items():
            if track_info["path"] == track_path:
                return
        
        try:
            track_path: pathlib.WindowsPath = shutil.copy2(track_path, pathlib.Path(SETTINGS["directory"]))
        except shutil.SameFileError:
            ...
        
        if track_path not in self.existing_tracks:
            self.existing_tracks.append(track_path)

        min_max_coordinates = 396 / duration
        coordinate_ranges = {}
        start = 0
        end = min_max_coordinates
        for segment in range(round(duration)):
            coordinate_ranges[segment] = (start, end)
            start = end
            end += min_max_coordinates

        self.playlist[index] = {
            "album": album,
            "artist": artist,
            "duration": duration,
            "title": title,
            "artwork": ImageTk.PhotoImage(Image.open(io.BytesIO(artwork)).resize((256, 256))) if artwork else None,
            "path": track_path,
            "coordinates": coordinate_ranges,
        }

        return index
    
    def play(self):
        """Initiates playback of the current track in the playlist or the first track if no track is currently playing.
        """
        if self.now_playing:
            index, track_info = self.get_now_playing()
            self.update_playing_track(index, track_info)
        
        elif not self.now_playing and self.existing_tracks:
            self.update_playing_track(0, self.playlist[0])

    def update_playing_track(self, index: int, track_info: dict) -> None:
        """Updates the player with the currently selected track's information and initiates playback.

        Args:
            index (int): The index of the currently selected track in the playlist.
            track_info (dict): A dictionary containing the track's metadata, including title, album, artist, duration, and artwork.
        """
        try:
            self.after_cancel(self.updater)
        except AttributeError:
            ...

        self.now_playing.clear()

        title = track_info["title"]
        album = track_info["album"]
        artwork = track_info["artwork"]
        artist = track_info["artist"]
        duration = track_info["duration"]
        path = track_info["path"]

        self.now_playing[index] = track_info
        self.track_duration = duration
        self.track_progress = 0
        self.is_playing = True

        self.reorder_now_playing()

        self.track_title.configure(text=f"{title or 'N/A'} {f'- {album}' if album else ''}")
        if artwork:
            self.artwork.configure(image=artwork)
            self.show_artwork = True
        else:
            self.artwork.configure(image=self.LIGHT_MODE_ALT_ARTWORK if self.mode == "light_mode" else self.DARK_MODE_ARTWORK)
            
        self.track_artist.configure(text=artist or "N/A")
        self.track_duration_text.configure(text=self.readable_duration(duration))
        self.play_pause_button.configure(image=self.LIGHT_MODE_PAUSE if self.mode == "light_mode" else self.DARK_MODE_PAUSE)
        self.track_position.configure(maximum=duration)

        self.update_track_progress()
        
        self.mixer.load(path)
        self.mixer.play(fade_ms=3000)

    def restart(self) -> None:
        """Restarts the current track if it has been playing for more than 2 seconds, otherwise plays the previous track.
        """
        if self.track_progress > 2:
            index, track_info = self.get_now_playing()
            self.update_playing_track(index, track_info)
            return

        index, _ = self.get_now_playing()
        track_info = self.playlist.get(index - 1)
        last_index = list(self.playlist)[-1]

        if not track_info:
            self.now_playing.clear()
            if index <= index:
                self.update_playing_track(last_index, self.playlist[last_index])
                return
            
            self.play()
        
        else:
            self.now_playing.clear()
            self.update_playing_track(index - 1, track_info)

    def previous(self) -> None:
        """Handles the action to play the previous track in the playlist or restart the current track.
        """
        if not self.now_playing:
            self.play()
        
        elif self.now_playing:
            self.restart()

    def next(self, finished: bool = False) -> None:
        """Advances to the next track in the playlist or handles repeat functionality.

        Args:
            finished (bool): Indicates whether the current track has finished playing and is the final track. Defaults to False.
        """
        if not self.now_playing:
            self.play()
            return

        index, _ = self.get_now_playing()
        track_info = self.playlist.get(index + 1)

        if self.repeat == Repeat.ONE and self.track_progress >= self.track_duration:
            index, track_info = self.get_now_playing()
            self.update_playing_track(index, track_info)
    
        elif not track_info:
            self.now_playing.clear()
            if self.repeat == Repeat.OFF and finished:
                self.play_pause_button.configure(image=self.LIGHT_MODE_PLAY if self.mode == "light_mode" else self.DARK_MODE_PLAY)
                self.after_cancel(self.updater)

            elif list(self.playlist)[-1] >= index:
                self.update_playing_track(0, self.playlist[0])

            else:
                self.play()
        
        else:
            self.now_playing.clear()
            self.update_playing_track(index + 1, track_info)

    def toggle_playback(self) -> None:
        """Toggles the playback state of the media player.
        """
        if self.is_playing:
            self.is_playing = False
            self.play_pause_button.config(image=self.LIGHT_MODE_PLAY if self.mode == "light_mode" else self.DARK_MODE_PLAY)
            self.mixer.pause()
            return

        self.is_playing = True
        self.play_pause_button.config(image=self.LIGHT_MODE_PAUSE if self.mode == "light_mode" else self.DARK_MODE_PAUSE)
        if self.playlist and not self.now_playing:
            self.play()

        elif self.playlist and self.now_playing:
            self.mixer.unpause()

    def get_now_playing(self) -> typing.Tuple[int, dict]:
        """Retrieves the index and information of the currently playing track.

        Returns:
            typing.Tuple[int, dict]: A tuple containing the index of the currently playing track as an integer, and its metadata as a dictionary.
        """
        index, track = next(iter(self.now_playing.items()))
        return index, track

    def shuffle_tracks(self) -> None:
        """Shuffles the tracks in the playlist and updates the display order.
        """
        if not self.can_shuffle:
            return

        self.can_shuffle = False
        random.shuffle(self.playlist)
        self.reorder_now_playing()
        
        self.can_shuffle = True
    
    def decrease_volume(self) -> None:
        """Decreases the volume of the audio playback by 10 units.
        """
        self.volume -= 10
        if self.volume <= 0:
            self.volume = 0
        
        self.volume_slider.set(self.volume)
        self.mixer.set_volume(self.volume / 100)
        self.updating_volume()

    def increase_volume(self) -> None:
        """Increases the volume of the audio playback by 10 units.
        """
        self.volume += 10
        if self.volume >= 100:
            self.volume = 100
        
        self.volume_slider.set(self.volume)
        self.mixer.set_volume(self.volume / 100)
        self.updating_volume()
    
    def backup_settings(self) -> None:
        """Backs up the settings.json file on startup.
        """
        try:
            backup_file_name = f"backup\\settings.json"
            shutil.copyfile("settings.json", backup_file_name)
        except shutil.Error:
            ...

    def load_backup(self) -> None:
        """Loads the settings.json file from the backup folder.
        """
        shutil.copyfile("backup\\settings.json", "settings.json")

    def updating_volume(self) -> None:
        """Updates the volume setting in the settings.json file and handles automatic backup and retry mechanisms.
        """    
        try:
            self.after_cancel(self.volume_updater)
        except AttributeError:
            ...

        if self.can_edit:
            self.can_edit = False
            try:
                with open("settings.json", "w") as file:
                    SETTINGS["volume"] = self.volume
                    json.dump(SETTINGS, file, indent=4)
            except KeyError:
                self.load_backup()
                self.updating_volume()
                
            self.can_edit = True
        
        else:
            self.volume_updater = self.after(15000, self.updating_volume)

    def adjust_volume(self, value: str) -> None:
        """Adjusts the volume of the audio playback based on the given value from the volume slider.

        Args:
            value (str): The volume level to set, represented as a string. This value is converted to an integer.
        """
        self.volume = int(value)
        if self.volume == 0:
            self.is_muted = True
            self.muted_unmuted.config(image=self.LIGHT_MODE_MUTED if self.mode == "light_mode" else self.DARK_MODE_MUTED)
        
        elif self.volume > 1:
            self.is_muted = False
            self.muted_unmuted.config(image=self.LIGHT_MODE_UNMUTED if self.mode == "light_mode" else self.DARK_MODE_UNMUTED)
        
        self.mixer.set_volume(self.volume / 100)
        self.updating_volume()

    def toggle_artwork(self) -> None:
        """Toggles the display of the artwork for the currently playing track.
        """
        if self.now_playing:
            if self.show_artwork:
                self.show_artwork = False
                self.artwork.configure(image=self.LIGHT_MODE_ALT_ARTWORK if self.mode == "light_mode" else self.DARK_MODE_ALT_ARTWORK, background="white" if self.mode == "light_mode" else "black", activebackground="black" if self.mode == "light_mode" else "white")
                return
            
            _, now_playing_info = self.get_now_playing()
            self.show_artwork = True
            self.artwork.configure(image=now_playing_info["artwork"])

    def reorder_now_playing(self) -> None:
        """Reorders the tracks displayed in the UI based on the current state of the playlist and highlights the currently playing track.
        """
        self.tracks.delete(0, tkinter.END)
        playlist = self.playlist.copy()
        self.playlist.clear()
        for track_index, pair in enumerate(playlist.items()):
            key, value = pair
            track_string = f"{track_index + 1}. " + (f"{value['title'] or ''}") + (f" - {value['album']}" if value['album'] else '') + (f" - {value['artist'] if value['artist'] else ''}")
            
            if self.now_playing:
                _, now_playing_info = self.get_now_playing()
                now_playing_track_string = f"{track_index + 1}. [Now Playing]: " + (f"{now_playing_info['title'] or ''}") + (f" - {now_playing_info['album']}" if now_playing_info['album'] else '') + (f" - {now_playing_info['artist'] if now_playing_info['artist'] else ''}")
                self.tracks.insert(key, track_string if playlist[key] != now_playing_info else now_playing_track_string)
                if playlist[key] == now_playing_info:
                    self.now_playing.clear()
                    self.now_playing[track_index] = now_playing_info
            else:
                self.tracks.insert(track_index, track_string)
            
            
            self.playlist[track_index] = value
        
        if len(self.playlist) == 0 and self.now_playing:
            self.now_playing.clear()
            self.set_to_default()
            self.mixer.unload()
            self.mixer.stop()
            
    def set_to_default(self) -> None:
        """Resets the UI elements to their default states.
        """
        try:
            self.after_cancel(self.repeater)
        except AttributeError:
            ...

        self.track_progress = 0
        self.track_duration = 0

        self.artwork.configure(image=self.LIGHT_MODE_ALT_ARTWORK if self.mode == "light_mode" else self.DARK_MODE_ALT_ARTWORK)
        self.play_pause_button.configure(image=self.LIGHT_MODE_PLAY if self.mode == "light_mode" else self.DARK_MODE_PLAY)
        self.track_title.configure(text="Title")
        self.track_artist.configure(text="Artist")
        self.track_position.configure(value=self.track_progress)
        self.track_duration_text.configure(text="00:00:00")
    
    def play_selected_track(self, event: tkinter.Event) -> None:
        """Handles the event to play a track selected from the listbox.

        Args:
            event (tkinter.Event): The event object containing information about the double-click event.
        """
        index = self.tracks.curselection()
        self.update_playing_track(index[0], self.playlist[index[0]])

    def set_track_position(self, event: tkinter.Event):
        """Sets the track's playback position based on the user's click position on the progress bar.

        Args:
            event (tkinter.Event): The event object containing information about the click event, including the x-coordinate.
        """
        if 0 <= event.x <= 396 and self.now_playing:
            _, now_playing_info = self.get_now_playing()
            for coordinate_index in now_playing_info["coordinates"]:
                min_coordinate, max_coordinate = now_playing_info["coordinates"][coordinate_index]
                if min_coordinate <= event.x <= max_coordinate:
                    self.track_progress = coordinate_index
                    self.mixer.set_pos(self.track_progress)
        
        if not self.is_playing:
            self.track_position.configure(value=self.track_progress)
            self.track_duration_text.configure(text=self.readable_duration(self.track_duration - self.track_progress))

    def select_track(self, event: tkinter.Event):
        """Selects a track from the listbox based on the mouse click position.

        Args:
            event (tkinter.Event): The event object containing information about the mouse click, including the y-coordinate of the click position.
        """
        index = self.tracks.nearest(event.y)
        self.tracks.selection_set(index)
        self.selected_index = index

    def swap_track_index(self, event: tkinter.Event) -> None:
        """Handles the reordering of tracks in the playlist based on drag-and-drop actions in the UI.

        Args:
            event (tkinter.Event): The event object containing information about the drag-and-drop action, including the
            y-coordinate of the drop position.
        """
        if not self.can_reorder:
            return
        
        self.can_reorder = False
        index = self.tracks.nearest(event.y)
        update_tracks = False
        if index < self.selected_index:

            self.playlist.update({
                index: self.playlist[self.selected_index],
                self.selected_index: self.playlist[index]
            })

            track = self.tracks.get(index)
            self.tracks.delete(index)
            self.tracks.insert(index + 1, track)
            self.selected_index = index
            update_tracks = True

        elif index > self.selected_index:

            self.playlist.update({
                index: self.playlist[self.selected_index],
                self.selected_index: self.playlist[index]
            })

            track = self.tracks.get(index)
            self.tracks.delete(index)
            self.tracks.insert(index - 1, track)
            self.selected_index = index
            update_tracks = True
        
        if update_tracks:
            self.reorder_now_playing()
        
        self.can_reorder = True
    
    def remove_tracks(self) -> None:
        """Opens a file dialog for the user to select audio tracks to remove, and then deletes the selected files from the filesystem.
        """
        file_paths = filedialog.askopenfilenames(title="Select Tracks", initialdir=SETTINGS["directory"], filetypes=(("MP3 Files", "*.mp3"), ("WAV Files", "*.wav"), ("OGG Files", "*.ogg")))
        for file_path in file_paths:
            pathlib.Path(file_path).unlink(missing_ok=True)

    def add_tracks(self) -> None:
        """Opens a file dialog for the user to select audio tracks to add to the playlist, and copies the selected files to the tracks directory.
        """
        file_paths = filedialog.askopenfilenames(title="Select Tracks", filetypes=(("MP3 Files", "*.mp3"), ("WAV Files", "*.wav"), ("OGG Files", "*.ogg")))
        for file_path in file_paths:
            try:
                shutil.copy2(file_path, pathlib.Path(SETTINGS["directory"]))
            except shutil.SameFileError:
                ...

    def add_existing_tracks(self):
        """Scans the tracks directory for audio files with extensions .mp3, .wav, or .ogg, and adds them to the playlist.
        """
        path = pathlib.Path(SETTINGS["directory"])
        for file in path.iterdir():
            if file.suffix in [".mp3", ".wav", ".ogg"]:
                index = self.populate_track_info(file)
                track_string = f"{index + 1}. " + (f"{self.playlist[index]['title'] or ''}") + (f" - {self.playlist[index]['album']}" if self.playlist[index]['album'] else '') + (f" - {self.playlist[index]['artist'] if self.playlist[index]['artist'] else ''}")
                self.tracks.insert(index, track_string)
    
    def watchdog(self) -> None:
        """Monitors the tracks directory for any changes in the files present, such as additions or deletions of audio files.
        If a file has been added or removed, it updates the playlist and the UI accordingly.
        """
        path = pathlib.Path(SETTINGS["directory"])
        files = []
        for file in path.iterdir():
            if file.suffix in [".mp3", ".wav", ".ogg"]:
                files.append(str(file))
        
        old = set(self.existing_tracks)
        new = set(files)

        update_tracks = False
        
        # File removed
        if len(old) > len(new):
            for file in self.existing_tracks:
                file = pathlib.Path(file).as_posix().replace("/", "\\")
                if file not in files:
                    for key, value in self.playlist.copy().items():
                        if file == value["path"]:
                            self.existing_tracks.remove(file)
                            self.playlist.pop(key)
                            update_tracks = True

        # File added
        elif len(old) < len(new):
            for file in files:
                if file not in self.existing_tracks:
                    self.populate_track_info(pathlib.Path(file))
                    update_tracks = True
    
        if update_tracks:
            self.reorder_now_playing()

        self.file_watcher = self.after(1000, self.watchdog)
    
    def toggle_mode(self) -> None:
        """Toggles the application's theme between light and dark modes.
        """
        if self.mode == "light_mode":
            self.mode = "dark_mode"
        
        elif self.mode == "dark_mode":
            self.mode = "light_mode"

    def update_theme(self) -> None:
        """Updates the theme of the application based on the current mode.
        """
        self.configure(background="white" if self.mode == "light_mode" else "#2F3136")
        for widget in self.winfo_children():
            if isinstance(widget, tkinter.Canvas) or isinstance(widget, tkinter.Toplevel):
                widget.configure(background="white" if self.mode == "light_mode" else "#2F3136", borderwidth=0, highlightthickness=0)
                for child in widget.winfo_children():
                    if isinstance(child, tkinter.Listbox):
                        child.configure(background="white" if self.mode == "light_mode" else "#2F3136", foreground="black" if self.mode == "light_mode" else "white", highlightcolor="grey" if self.mode == "light_mode" else "white", selectforeground='black' if self.mode == "light_mode" else "white", selectbackground='white' if self.mode == "light_mode" else "#2F3136")
                    
                    elif isinstance(child, tkinter.Button):
                        child_name = child.winfo_name()
                        if child_name in ["add", "remove"]:
                            child.configure(foreground="black" if self.mode == "light_mode" else "white", background="white" if self.mode == "light_mode" else "#2F3136", activebackground="white" if self.mode == "light_mode" else "#2F3136", activeforeground="black" if self.mode == "light_mode" else "white")
                            continue

                        child.configure(background="white" if self.mode == "light_mode" else "#2F3136", borderwidth=0, highlightthickness=0, highlightcolor="black" if self.mode == "light_mode" else "white", activebackground="white" if self.mode == "light_mode" else "#2F3136")

                        if child_name == "dark_light":
                            child.configure(image=self.LIGHT_MODE_LIGHT if self.mode == "light_mode" else self.DARK_MODE_DARK, background="white" if self.mode == "light_mode" else "#2F3136")
                        
                        elif child_name in ["play_pause", "muted_unmuted"]:
                            if child_name == "play_pause":
                                if not self.is_playing:
                                    self.play_pause_button.configure(image=self.LIGHT_MODE_PLAY if self.mode == "light_mode" else self.DARK_MODE_PLAY, background="white" if self.mode == "light_mode" else "#2F3136")
                                
                                else:
                                    self.play_pause_button.configure(image=self.LIGHT_MODE_PAUSE if self.mode == "light_mode" else self.DARK_MODE_PAUSE, background="white" if self.mode == "light_mode" else "#2F3136")
                            
                            else:
                                if self.is_muted:
                                    self.muted_unmuted.config(image=self.LIGHT_MODE_MUTED if self.mode == "light_mode" else self.DARK_MODE_MUTED)

                                else:
                                    self.muted_unmuted.config(image=self.LIGHT_MODE_UNMUTED if self.mode == "light_mode" else self.DARK_MODE_UNMUTED)

                        elif child_name == "artwork":
                            if not self.show_artwork:
                                child.configure(image=self.LIGHT_MODE_ALT_ARTWORK if self.mode == "light_mode" else self.DARK_MODE_ALT_ARTWORK, background="white" if self.mode == "light_mode" else "#2F3136")

                        else:
                            child.configure(image=getattr(self, f"{self.mode}_{child_name}".upper()))

                    elif isinstance(child, tkinter.Label):
                        child.configure(background="white" if self.mode == "light_mode" else "#2F3136", foreground="black" if self.mode == "light_mode" else "white")
                    
                    elif isinstance(child, tkinter.Scale):
                        child.configure(background="white" if self.mode == "light_mode" else "#2F3136", troughcolor="lightgrey", activebackground="white" if self.mode == "light_mode" else "#2F3136", borderwidth=0, highlightthickness=0, foreground="black" if self.mode == "light_mode" else "white")

    def close_settings(self):
        """Closes the settings window and cleans up the reference."""
        self.settings_window.destroy()
        del self.settings_window
    
    def update_default_theme(self) -> None:
        """Updates the default theme of the application based on the current mode.
        """
        selection = self.startup_theme.get()
        if selection == SETTINGS["theme"]:
            return
        
        try:
            with open("settings.json", "w") as file:
                SETTINGS["theme"] = selection
                json.dump(SETTINGS, file, indent=4)
        except KeyError:
            self.load_backup()
            self.update_default_theme()
    
    def update_tracks_directory(self) -> None:
        """Updates the tracks directory of the application based on the selected directory.
        """
        directory = filedialog.askdirectory(initialdir=SETTINGS["directory"], title="Select tracks directory")
        if not directory:
            return
        
        self.now_playing.clear()
        self.playlist.clear()
        self.existing_tracks.clear()

        self.set_to_default()
        self.mixer.unload()
        self.mixer.stop()

        self.reorder_now_playing()
        try:
            with open("settings.json", "w") as file:
                SETTINGS["directory"] = directory
                json.dump(SETTINGS, file, indent=4)
        except KeyError:
            self.load_backup()
            self.update_tracks_directory()
        

    def open_settings(self) -> None:
        """Opens the settings window for the application.
        """
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            self.settings_window.lift()

        else:
            self.settings_window = tkinter.Toplevel(self,takefocus=1, background="darkgrey")
            self.settings_window.iconbitmap("assets\\icon.ico")
            self.settings_window.grab_set()
            self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings)
            self.settings_window.bind("<Escape>", lambda event: self.close_settings())
            for key, value in DEFAULT.items():
                if key == "geometry":
                    value = "320x320" # Smaller than parent, big enough to fit settings

                func = getattr(self.settings_window, f"wm_{key}")
                func(**value) if isinstance(value, dict) else func(value)

            settings_canvas = tkinter.Canvas(self.settings_window)
            settings_canvas.grid()

            # .grid would not work for some reason
            # hidden text to allow rest of canvas to be adjustable
            hidden_text = tkinter.Label(settings_canvas, text="", background="darkgrey")
            hidden_text.grid()

            default_theme_canvas = tkinter.Canvas(self.settings_window, background="darkgrey", borderwidth=0, highlightthickness=0)
            default_theme_canvas.grid(row=1, column=1, padx=(48, 0))

            default_theme_label = tkinter.Label(default_theme_canvas, text="Set Default Theme:", font=("Times New Roman", 18, "bold"), background="darkgrey", borderwidth=0, highlightthickness=0)
            default_theme_label.grid(row=2, column=1)

            light_mode_button = tkinter.Radiobutton(default_theme_canvas, justify="center", text="Light Theme", variable=self.startup_theme, value=1, command=self.update_default_theme, font=("Times New Roman", 12, "bold"), background="darkgrey", borderwidth=0, highlightthickness=0, activebackground="darkgrey")
            light_mode_button.grid(row=3, column=1)

            dark_mode_button = tkinter.Radiobutton(default_theme_canvas, justify="center", text="Dark Theme", variable=self.startup_theme, value=2, command=self.update_default_theme, font=("Times New Roman", 12, "bold"), background="darkgrey", borderwidth=0, highlightthickness=0, activebackground="darkgrey")
            dark_mode_button.grid(row=4, column=1)

            default_directory_label = tkinter.Label(default_theme_canvas, text=pathlib.Path(SETTINGS["directory"]).absolute(), background="darkgrey", font=("Times New Roman", 12, "bold"), wraplength=200)
            default_directory_label.grid(row=7, column=1)

            default_directory_button = tkinter.Button(default_theme_canvas, text="Set Default Directory", command=self.update_tracks_directory)
            default_directory_button.grid(pady=(48, 0), sticky="nswe", column=1, row=6)

    def canvas(self) -> None:
        """
        Initializes and arranges the main UI components of the application.
        """
        # ------------------------------------------ #
        #                    Tracks                  #
        # ------------------------------------------ #

        tracks_canvas = tkinter.Canvas(self)
        tracks_canvas.grid(row=0, column=0, rowspan=16, sticky="wns")

        add_tracks_button = tkinter.Button(tracks_canvas, name="add", text="Add Track", font=("Times New Roman", 12, "bold"), command=self.add_tracks)
        add_tracks_button.grid(pady=(10, 5), padx=(10, 0), sticky="nswe", column=0)

        remove_tracks_button = tkinter.Button(tracks_canvas, name="remove", text="Remove Track", font=("Times New Roman", 12, "bold"), command=self.remove_tracks)
        remove_tracks_button.grid(pady=(5, 0), padx=(10, 0), sticky="nswe", column=0, row=16)

        self.tracks = tkinter.Listbox(tracks_canvas, font=("Times New Roman", 12), width=24, height=22, selectmode="single", background="white" if self.mode == "light_mode" else "black", foreground="black" if self.mode == "light_mode" else "white", highlightcolor="grey" if self.mode == "light_mode" else "white", selectforeground='black' if self.mode == "light_mode" else "white", selectbackground='white' if self.mode == "light_mode" else "black")
        self.tracks.grid(row=1, rowspan=13, padx=(8, 0), sticky="nsw")
        self.tracks.bind("<Double-Button-1>", self.play_selected_track)
        self.tracks.bind('<Button-1>', self.select_track)
        self.tracks.bind('<B1-Motion>', self.swap_track_index)

        self.add_existing_tracks()

        horizontal_scrollbar = tkinter.Scrollbar(tracks_canvas, command=self.tracks.xview, orient="horizontal")
        horizontal_scrollbar.grid(sticky="swe", padx=(8, 0), column=0, row=14)

        self.tracks.config(xscrollcommand=horizontal_scrollbar.set)

        # ------------------------------------------ #
        #                    Artwork                 #
        # ------------------------------------------ #

        artwork_canvas = tkinter.Canvas(self)
        artwork_canvas.grid(row=0, column=1, rowspan=7, columnspan=7, sticky="nswe", padx=(24, 0), pady=(32, 0))
        
        self.artwork = tkinter.Button(artwork_canvas, name="artwork", image=self.LIGHT_MODE_ALT_ARTWORK if self.mode == "light_mode" else self.DARK_MODE_ALT_ARTWORK, command=self.toggle_artwork, anchor="center", relief="flat")
        self.artwork.pack(expand=True)

        # ------------------------------------------ #
        #                  Track Info                #
        # ------------------------------------------ #

        track_info_canvas = tkinter.Canvas(self)
        track_info_canvas.grid(row=8, column=1, columnspan=7, sticky="wnse", pady=(8, 8), padx=(32, 0))

        self.track_title = tkinter.Label(track_info_canvas, text="Title", font=("Times New Roman", 12, "bold"), wraplength=512)
        self.track_title.grid(row=0)

        self.track_artist = tkinter.Label(track_info_canvas, text="Artist", font=("Times New Roman", 12))
        self.track_artist.grid(row=1)

        self.track_position = ttk.Progressbar(track_info_canvas, orient="horizontal", mode="determinate", length=396, variable=self.track_progress)
        self.track_position.grid(row=2, sticky="nsew", padx=(16, 0))

        self.track_position.bind('<Button-1>', self.set_track_position)

        self.track_duration_text = tkinter.Label(track_info_canvas, text="00:00:00", font=("Times New Roman", 12, "bold"))
        self.track_duration_text.grid(row=3)

        # ------------------------------------------ #
        #             Track/Audio Buttons            #
        # ------------------------------------------ #

        track_buttons_canvas = tkinter.Canvas(self)
        track_buttons_canvas.grid(row=9, column=4, sticky="nsew", padx=(32, 32))

        self.shuffle_button = tkinter.Button(track_buttons_canvas, name="shuffle", command=self.shuffle_tracks, image=self.LIGHT_MODE_SHUFFLE if self.mode == "light_mode" else self.DARK_MODE_SHUFFLE)
        self.shuffle_button.grid(column=0, row=1, padx=(24, 8))

        decrease = tkinter.Button(track_buttons_canvas, name="decrease", command=self.decrease_volume, image=self.LIGHT_MODE_DECREASE if self.mode == "light_mode" else self.DARK_MODE_DECREASE)
        decrease.grid(column=1, row=1, padx=(16, 8))

        self.previous_button = tkinter.Button(track_buttons_canvas, name="previous",  command=self.previous, image=self.LIGHT_MODE_PREVIOUS if self.mode == "light_mode" else self.DARK_MODE_PREVIOUS)
        self.previous_button.grid(column=2, row=1, padx=(16, 8))

        self.play_pause_button = tkinter.Button(track_buttons_canvas, name="play_pause",  command=self.toggle_playback, image=self.LIGHT_MODE_PLAY if self.mode == "light_mode" else self.DARK_MODE_PLAY)
        self.play_pause_button.grid(column=3, row=1, padx=(16, 8))

        self.next_button = tkinter.Button(track_buttons_canvas, name="next",  command=self.next,  image=self.LIGHT_MODE_NEXT if self.mode == "light_mode" else self.DARK_MODE_NEXT)
        self.next_button.grid(column=4, row=1, padx=(16, 8))

        increase = tkinter.Button(track_buttons_canvas, name="increase",  command=self.increase_volume, image=self.LIGHT_MODE_INCREASE if self.mode == "light_mode" else self.DARK_MODE_INCREASE)
        increase.grid(column=5, row=1, padx=(16, 8))

        self.repeat_button = tkinter.Button(track_buttons_canvas, name="repeat",  command=self.update_repeat,  image=self.LIGHT_MODE_REPEAT if self.mode == "light_mode" else self.DARK_MODE_REPEAT)
        self.repeat_button.grid(column=6, row=1, padx=(16, 8))

        # ------------------------------------------ #
        #             Volume Toggle/Slider           #
        # ------------------------------------------ #

        audio_buttons_canvas = tkinter.Canvas(self)
        audio_buttons_canvas.grid(row=10, column=3, columnspan=4)

        self.muted_unmuted = tkinter.Button(audio_buttons_canvas, name="muted_unmuted",  command=self.toggle_mute, image=self.LIGHT_MODE_UNMUTED if self.mode == "light_mode" else self.DARK_MODE_UNMUTED)
        self.muted_unmuted.grid(column=0, row=0, padx=(8, 48), pady=(16, 0))

        self.volume_slider = tkinter.Scale(audio_buttons_canvas, from_=0, to=100, command=self.adjust_volume, orient="horizontal", length=264)
        self.volume_slider.grid(row=0, column=4)
        self.volume_slider.set(self.volume)

        # ------------------------------------------ #
        #                   Themes                   #
        # ------------------------------------------ #

        dark_light_button_canvas = tkinter.Canvas(self)
        dark_light_button_canvas.grid(row=15, rowspan=16, column=12, sticky="se")

        self.dark_light_button = tkinter.Button(dark_light_button_canvas, name="dark_light", command=self.toggle_mode, image=self.LIGHT_MODE_LIGHT if self.mode == "light_mode" else self.DARK_MODE_DARK, relief="flat")
        self.dark_light_button.grid(column=0, row=0, padx=(56, 0), pady=(0, 8))

        # ------------------------------------------ #
        #                  Settings                  #
        # ------------------------------------------ #

        settings_button_canvas = tkinter.Canvas(self)
        settings_button_canvas.grid(row=0, rowspan=1, column=11, columnspan=12, sticky="se")

        self.settings_button = tkinter.Button(settings_button_canvas, name="settings", command=self.open_settings, image=self.LIGHT_MODE_SETTINGS if self.mode == "light_mode" else self.DARK_MODE_SETTINGS, relief="flat")
        self.settings_button.grid(row=0, column=1, padx=(0, 8), pady=(0, 192))

        self.website_button = tkinter.Button(settings_button_canvas, name="browser", image=self.LIGHT_MODE_BROWSER if self.mode == "light_mode" else self.DARK_MODE_BROWSER, command=lambda: webbrowser.open_new(r"https://tendo.cc/"))
        self.website_button.grid(row=0, column=0, padx=(0, 24), pady=(0, 192))

        # ------------------------------------------ #
        #               Startup Task                 #
        # ------------------------------------------ #

        self.update_theme()
        self.backup_settings()

    def run(self):
        """Starts the application's main event loop.
        """
        self.mainloop()

if __name__ == "__main__":
    app = Player()
    app.run()