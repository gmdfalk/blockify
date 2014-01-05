#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
blockify-tk:
This is a TKinter interface which looks like the windows version
of Blockify.
"""

import sys
import inspect
sys.dont_write_bytecode = True
from Tkinter import *
import tkMessageBox
from subprocess import Popen
from subprocess import check_output
import re
#FIXME use imp to import without .py extension
import blockify
blockify.unmute()

# Create TK App
app = Tk()
app.title("Blockify")

# Song Title Label
string_artist_album = StringVar()
string_artist_album.set("Hey!? How are you doing?")
label_artist_album = Label(app, textvariable=string_artist_album, font=("sans", 11))
label_artist_album.grid(row=1, column=1, columnspan=2)

def restart():
    blockify.restart()

def check_blockify():
    #FIXME check on startup to correct button
    global result
    s = check_output(['ps', 'aux'])
    result = re.search(r'python2.*blockify$', s, re.MULTILINE)
    if result:
        button_toggle_blockify.config(text="Stopped")
    else:
        button_toggle_blockify.config(text="Running")
              
def toggle_blockify():
    check_blockify()
    if result:
        Popen(["pkill", "-f", "python2.*blockify$"])
    else:
        Popen(["blockify"])

def exit_ui():
    blockify.unmute()
    Popen(['pkill', '-f', 'python2.*blockify$'])
    sys.exit()

button_toggle_blockify = Button(app, text="Start/Stop")
button_toggle_blockify.grid(row=2, column=1)
button_toggle_blockify.config(command=check_blockify)

button_add_song = Button(app, text="Block This Song")
button_add_song.grid(row=2, column=2)

button_restart = Button(app, text="Exit", command=exit_ui)
button_restart.grid(row=3, column=1)

button_restart = Button(app, text="Restart", command=restart)
button_restart.grid(row=3, column=2)

def toggle_block_current():
    window_list = blockify.get_windows()
    artist_album = blockify.get_playing(window_list)
        
    action = tkMessageBox.askquestion("Confirm",
            "Add {} to your block file?".format(artist_album))
    
    if action == "yes":
        blockify.block_current()
        
# All functions
def update_gui():
    window_list = blockify.get_windows()
    artist_album = blockify.get_playing(window_list)
    
    string_artist_album.set(artist_album)

    if artist_album is not "":
        if blockify.check_songlist(window_list):
                button_add_song.config(text=" Blocked ")
        else:
                button_add_song.config(text="Block This Song")
    else:
        string_artist_album.set("not playing")
        blockify.mute()
    
    app.after(1000, update_gui) #Get title every 2 seconds

# Callbacks
button_add_song.config(command=toggle_block_current)
button_toggle_blockify.config(command=toggle_blockify)
app.after(10, update_gui)

# Start App
app.mainloop()

# Unmute on exit
#~ blockify.unmute()
