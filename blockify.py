#!/usr/bin/env python2

"""blockify:

    Mute songs on spotify (wine version only), requires wmctrl.

    Optionally, there is a ui you can use, this is called though
    ./blockify-ui

    Installation:
    Keep blockify and its symlink to blockify.py as well as blockify-ui in the
    same directory, ideally in your users $PATH.
    Copy list_example.txt to ~/.blockify_list

    Usage:
    When you find a song you want to mute, you need to add it to
    ~/.blockify_list either manually (find out the name with wmctrl -l) or via:
    pkill -USR1 -f python2.*blockify
    After adding a new entry you need to restart blockify manually or with:
    pkill -USR2 -f python2.*blockify
    Aliasing/Binding these commands works well for me.

    The UI is pretty self-explanatory. Closing the UI will currently end all
    running instances of blockify. Might get changed.

    Cheers,
    mikar

"""

import subprocess
import time
import sys
import os
import signal
from os.path import expanduser

home = expanduser("~")
SONGFILE = os.path.join(home, ".blockify_list")

# Initial global mute state, lets assume we start muted
is_muted = True

# Spotify names it's window based on the song playing with the prefix
spotify = "Spotify - "

#########################################
# Functions that work with the SONGFILE #
#########################################

def load_song_list():
    # Read song list
    global song_list

    try:
        song_file = open(SONGFILE, "r")

    except IOError:
        # If SONGFILE didn't exist SONGFILE
        song_file = open(SONGFILE, "w")
        song_file.write("")
        song_file.close()
        return []
    
    song_list = song_file.read()
    song_file.close()

    # Split into lines
    song_list = song_list.split("\n")
    
    # Remove empty lines
    clean_list = []
    for item in song_list:
        if len(item.strip()):
            clean_list.append(item)

    song_list = clean_list

    # Return song list for any function that may need it
    return song_list

def add_to_list(new_song):
    print 'Adding', new_song, 'to', SONGFILE

    # Read in the old .blockify_list
    song_list_file = open(SONGFILE, "r")
    current_song_list = song_list_file.read()
    song_list_file.close()
    
    # Add item to song list
    new_list = current_song_list + "\n" + new_song
    song_list_file = open(SONGFILE, "w")
    song_list_file.write(new_list)
    song_list_file.close()
    
    # Reload song list, and return new song list
    return load_song_list()

##############################################
# Functions that retrieve the song from wine #
##############################################

def get_windows():   
    try:
        pipe = subprocess.Popen(['wmctrl', '-l'], stdout=subprocess.PIPE).stdout
        return pipe.read().split("\n")
 
    # If Wine isn't installed OSError tends to happen, also the function
    # needs to return data in the expected format (a list)
    except OSError:
        print "wmctrl needs to be installed"
        sys.exit(1)
        #return [spotify + "wmctrl is not installed"]

 
######################################
# Functions that get the actual song #
######################################

def get_current_song():
    current_song = ""

    # Search through list of windows from get_windows()
    # if spotify is contained, remove spotify from window
    # title and any extra space

    for window_title in get_windows():
        if 0 <= window_title.find(spotify):
            current_song = window_title[len(spotify):].strip()
            break

    # Return the currently playing song or ""
    return current_song


def check_songlist(current_song = ""):
    # Can check songlist without having to get_current_song()
    if current_song == "":
        current_song = get_current_song()

    # If there was a spotify song found, and
    # If the current_song *starts* with an item in the song list
    if current_song is not "":
        for song in song_list:    
            if current_song.find(song) == 0:
                toggle_mute(True) # Song was found, set mute to True
                return True

    # Control reaches here when not found, not running
    # or no song provided
    toggle_mute(False) # No song, set mute to False


def block_current():
    current_song = get_current_song()

    # If the length is 0 then skip    
    if current_song is not "":
        add_to_list(window_title)

#####################################################
# Functions that work with amixer (from alsa-utils) #
#####################################################

def toggle_mute(mute = False):
    global state
    global is_muted

    # Only send the un/mute command on state change
    if is_muted != mute:
        if mute:
            state = 'mute' 
            print "Muting"
        else:
            state = 'unmute'
            print "Unmuting"

        # It was found that some computers mute the 'Speaker' 
        # channel when muting the master channel, but they
        # don't unmute automatically. Thus, we work with that
        # channel too.
    for channel in ['Master', 'Speaker']:
            subprocess.Popen(['amixer', '-q', 'set', channel, state])
        
    is_muted = mute

def check_mute():
    global is_muted
    # Read the actual mute status from amixer
    result = os.popen("amixer get Master | grep -o off").read()
    if "off" in result:
        actual_mute=True
    else:
        actual_mute=False
    
    # Return what we have the state as, and the actual state
    return (actual_mute, is_muted)

############################################
# Functions that work with the app running #
############################################

def restart():
    print 'Restarting Blockify'
    python = sys.executable
    os.execl(python, python, * sys.argv)

def trap_exit():
    print '\nStopping Blockify'
    toggle_mute()
    sys.exit()

signal.signal(signal.SIGUSR1, lambda sig, hdl: block_current())
signal.signal(signal.SIGUSR2, lambda sig, hdl: restart())
signal.signal(signal.SIGTERM, lambda sig, hdl: trap_exit())
signal.signal(signal.SIGINT,  lambda sig, hdl: trap_exit())

##################################################
# Main loop and initialisation for CLI interface #
##################################################

def main():
    # Initially unmute the sound
    print "Starting Blockify"
    toggle_mute()

    # Load the song list
    global song_list
    song_list = load_song_list()

    # Start the main loop
    while(True):
        check_songlist()
        time.sleep(1)


if __name__ == "__main__":
    print "please use ./blockify to run blockify"
    main()
