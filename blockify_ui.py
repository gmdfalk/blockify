#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
blockify-tk:
    This is a TKinter interface which looks like the windows version
    of Blockify.
"""

import sys, os, inspect
from Tkinter import *
import tkMessageBox


import blockify as blockify

# Duplicated from blockify.py. For some reason not working if imported
home = os.path.expanduser("~")
SONGFILE = os.path.join(home, ".blockify_list")
initial_timestamp = os.path.getmtime(SONGFILE)

blockify.toggle_mute()
blockify.load_song_list()



# Create TK App
app = Tk()
app.title("Blockify")

# Song Title Labelhttp://pypix.com/python/create-simple-music-streaming-app-flask/
string_artist_album = StringVar()
string_artist_album.set("")
label_artist_album = Label(app, textvariable=string_artist_album, font=("sans", 14))
label_artist_album.grid(row=1, column=1, columnspan=2)

# Mute track_list check box
bool_mute_tracks = IntVar()
bool_mute_tracks.set(1)
check_mute_tracks = Checkbutton(app, text = "Mute Tracks",\
                     variable=bool_mute_tracks, onvalue=1, offvalue=0)
check_mute_tracks.grid(row=2, column=2)

# Auto Mute track_list check box
bool_auto_add_tracks = IntVar()
bool_auto_add_tracks.set(0)
check_auto_add_tracks = Checkbutton(app, text = "Auto Add Tracks",\
                        variable=bool_auto_add_tracks, onvalue=1, offvalue=0)
check_auto_add_tracks.grid(row=3, column=2)

# Block currently playing
button_add_track = Button(app, text="Block This Track")
button_add_track.grid(row=2, column=1, rowspan=2)


def toggle_block_current():
    current_song = blockify.get_current_song()
        
    action = tkMessageBox.askquestion("Confirm",
            "Add {} to your block file?".format(current_song))
    
    if action == "yes":
        blockify.track_list = blockify.add_to_list(current_song)
        return True
    return False

def auto_block(current_song):
    if not bool_auto_add_tracks.get():
        return
    
    mute_states = blockify.check_mute()
    if not mute_states[0] == mute_states[1]:
        if not toggle_block_current():
            bool_auto_add_tracks.set(0)

# Main callback
def update_gui():
    # Set current song label to current song
    current_song = blockify.get_current_song()
    string_artist_album.set(current_song)

    # If there is a song running
    if current_song is not "":

        # And mute is enabled
        if bool_mute_tracks.get():

            # And a song on the blocklist was found
            if blockify.check_songlist():
               
                # Set mute button to show blocked
                button_add_track.config(text="    Blocked     ")

            # Otherwise offer to block track or autoblock
            else:
                button_add_track.config(text="Block This Track")
                auto_block(current_song);
        else:
            blockify.toggle_mute() # unmute
    else:
        blockify.toggle_mute()     # unmute

    # Duplicate from blockify.py, for some reason not working if imported
    global initial_timestamp
    current_timestamp = os.path.getmtime(SONGFILE)
    if initial_timestamp != current_timestamp:
        song_list = blockify.load_song_list()
        initial_timestamp = current_timestamp
        
    app.after(1000, update_gui) # Get title every second

# Callbacks
button_add_track.config(command=toggle_block_current)
app.after(10, update_gui)

# Start App
app.mainloop()


# Unmute on exit
blockify.toggle_mute()
