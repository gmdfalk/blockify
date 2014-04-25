#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""blockify-ui:

    This is a TKinter interface which looks like the windows version
    of Blockify.
"""

import os
import tkMessageBox
import blockify
from Tkinter import *

# Duplicated from blockify.py. For some reason not working if imported.
home = os.path.expanduser("~")
SONGFILE = os.path.join(home, ".blockify_list")
initial_timestamp = os.path.getmtime(SONGFILE)

blockify.toggle_mute()
blockify.load_blocklist()

# Create TK App.
app = Tk()
app.title("Blockify")

# Song Title Label
artist_album = StringVar()
artist_album.set("")
label_artist_album = Label(app, textvariable=artist_album, font=("sans", 14))
label_artist_album.grid(row=1, column=1, columnspan=2)

# Mute track_list check box
bool_mute_tracks = IntVar()
bool_mute_tracks.set(1)
check_mute_tracks = Checkbutton(app, text="Mute Tracks", onvalue=1,
                                variable=bool_mute_tracks, offvalue=0)
check_mute_tracks.grid(row=2, column=2)

# Auto Mute track_list check box.
bool_auto_add_tracks = IntVar()
bool_auto_add_tracks.set(0)
check_auto_add_tracks = Checkbutton(app, text="Auto Add Tracks", onvalue=1,
                                    variable=bool_auto_add_tracks, offvalue=0)
check_auto_add_tracks.grid(row=3, column=2)

# Block currently playing song.
button_add_track = Button(app, text="Block This Track")
button_add_track.grid(row=2, column=1, rowspan=2)


def toggle_block_current():
    current_song = blockify.get_current_song()

    action = tkMessageBox.askquestion("Confirm", "Add %s to your block file?" %
                                      (current_song))

    if action == "yes":
        blockify.track_list = blockify.add_to_list(current_song)
        return True
    return False


def auto_block(current_song):
    if not bool_auto_add_tracks.get():
        return

    actual_mute, is_muted = blockify.sound_muted()
    if actual_mute != is_muted:
        if not toggle_block_current():
            bool_auto_add_tracks.set(0)


# Main callback
def update_gui():
    # Set current song label to current song.
    current_song = blockify.get_current_song()
    artist_album.set(current_song)

    # If there is a song running.
    if current_song is not "":
        # And mute is enabled.
        if bool_mute_tracks.get():
            # And a song on the blocklist was found.
            if blockify.check_songlist():
                # Set mute button to show blocked.
                button_add_track.config(text="    Blocked     ")
            # Otherwise offer to block track or autoblock.
            else:
                button_add_track.config(text="Block This Track")
                auto_block(current_song)
        else:
            blockify.toggle_mute()  # unmute
    else:
        blockify.toggle_mute()  # unmute

    # Duplicate from blockify.py, for some reason not working if imported.
    global initial_timestamp
    current_timestamp = os.path.getmtime(SONGFILE)
    if initial_timestamp != current_timestamp:
        blockify.load_blocklist()
        initial_timestamp = current_timestamp

    # Get title every second.
    app.after(1000, update_gui)

# Callbacks.
button_add_track.config(command=toggle_block_current)
app.after(10, update_gui)

# Start App.
app.mainloop()

# Unmute on exit.
blockify.toggle_mute()
