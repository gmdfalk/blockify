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
blockify.set_mute()

# Create TK App
app = Tk()
app.title("Blockify")

# Song Title Label
string_artist_album = StringVar()
string_artist_album.set("Hey!? How are you doing?")
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
    window_list = blockify.get_windows()
    artist_album = blockify.get_playing(window_list)
        
    action = tkMessageBox.askquestion("Confirm",
            "Add {} to your block file?".format(artist_album))
    
    if action == "yes":
        blockify.track_list = blockify.modify_track_list(artist_album)
        return True
    return False

def auto_block(artist_album):
    if not bool_auto_add_tracks.get():
        return
    
    mute_states = blockify.check_mute()
    if not mute_states[0] == mute_states[1]:
        if not toggle_block_current():
            bool_auto_add_tracks.set(0)

# All functions
def update_gui():   
    window_list = blockify.get_windows()
    artist_album = blockify.get_playing(window_list)
    
    string_artist_album.set(artist_album)

    if artist_album is not "":
        if bool_mute_tracks.get():
            if blockify.check_tracklist(window_list):
                button_add_track.config(text="    Blocked     ")
            else:
                button_add_track.config(text="Block This Track")
                auto_block(artist_album);
        else:
            blockify.set_mute()
    else:
        blockify.set_mute()
    
    app.after(1000, update_gui) #Get title every 2 seconds

# Callbacks
button_add_track.config(command=toggle_block_current)
app.after(10, update_gui)

# Start App
app.mainloop()


# Unmute on exit
blockify.set_mute()