#!/usr/bin/env python2

"""blockify:
    Mute adverts on spotify (wine version only)

    Usage:
    When you find an advert you want to mute, you need to add it to
    ~/.blockify_list either manually (find out the name with wmctrl -l) or via:
    pkill -USR1 -f python2.*blockify
"""

import subprocess
import time
import sys
import os
import signal

# Check if we can use the wnck library, otherwise resort to wmctrl.
use_wnck = False
try:
    import wnck
    import gtk
    import pygtk
    pygtk.require('2.0')
    use_wnck = True
except ImportError:
    try:
        devnull = open(os.devnull)
        subprocess.Popen(["wmctrl"], stdout=devnull, stderr=devnull).communicate()
    except OSError:
        print "Please install wnck or wmctrl first."
        sys.exit(1)

# Globals
VERSION=0.5
spotify = "Spotify - "
is_muted = True
home = os.path.expanduser("~")
SONGFILE = os.path.join(home, ".blockify_list")

#########################################
# Functions that work with the SONGFILE #
#########################################

def load_song_list():
    try:
        song_file = open(SONGFILE, "r")
    except IOError:
        # If SONGFILE didn't exist create it.
        song_file = open(SONGFILE, "w")
        song_file.write("")
        song_file.close()
        return []
    
    song_list = song_file.read()
    song_file.close()

    # Split the list into lines.
    song_list = song_list.split("\n")
    
    # Remove all empty lines.
    clean_list = [i for i in song_list if len(i.strip())]
    song_list = clean_list

    # Return song list for any function that may need it.
    return song_list

def add_to_list(new_song):
    print 'Adding', new_song, 'to', SONGFILE

    # Read in the old .blockify_list.
    song_list_file = open(SONGFILE, "r")
    current_song_list = song_list_file.read()
    song_list_file.close()
    
    # Add item to song list
    new_list = current_song_list + "\n" + new_song
    song_list_file = open(SONGFILE, "w")
    song_list_file.write(new_list)
    song_list_file.close()
    
    # Reload song list, and return new song list.
    return load_song_list()

##############################################
# Functions that retrieve the song from wine #
##############################################

def get_windows():
    if use_wnck:
        # Get the current screen.
        screen = wnck.screen_get_default()

        while gtk.events_pending():
            gtk.main_iteration(False)

        # Object list of windows in screen.
        windows = screen.get_windows()
        # Actual window list.
        return [win.get_icon_name() for win in windows if len(windows)]
    else:
        pipe = subprocess.Popen(['wmctrl', '-l'], stdout=subprocess.PIPE).stdout
        # Split the lines into a window list.
        return pipe.read().split("\n")
 
######################################
# Functions that get the actual song #
######################################

def get_current_song():
    current_song = ""

    # Check if a Spotify window exists and return the current songname.
    pipe = get_windows()
    for line in pipe:
        if (line.find(spotify) >= 0):
            # Remove "Spotify - " and assign the name.
            if use_wnck:
                current_song = " ".join(line.split()[2:])
            else:
                current_song = " ".join(line.split()[5:])
            break

    # Return the currently playing song or "".
    return current_song

def check_songlist(current_song = ""):    
    # Can check songlist without having to get_current_song().
    if current_song == "":
        current_song = get_current_song()

    # If there was a spotify song found, and if the current_song *starts*
    # with a string from the song list.
    global song
    song_list = load_song_list()
    if current_song is not "":
        for song in song_list:
            if current_song.find(song) == 0:
                toggle_mute(True) # Song was found, set mute to True.
                return True

    # Control reaches here when not found, not running
    # or no song provided.
    toggle_mute(False) # No song, set mute to False.

def block_current():
    current_song = get_current_song()

    # If the length is 0 then skip.
    if current_song is not "":
        add_to_list(current_song)

#####################################################
# Functions that work with amixer (from alsa-utils) #
#####################################################

def check_channels():
    speaker_channel=False
    # Check if we need to use the Speaker Channel in addition to Master.
    amixer_output = subprocess.Popen(['amixer'], stdout=subprocess.PIPE).communicate()[0]
    if "'Speaker',0" in amixer_output:
        speaker_channel=True
        return speaker_channel
    return speaker_channel

def toggle_mute(mute = False):
    global is_muted
    speaker_channel = check_channels()

    # Only send the un/mute command on state change.
    if is_muted != mute:
        if mute:
            state = 'mute' 
            print "Muting", song
        else:
            state = 'unmute'
            print "Unmuting"

        # It was found that some computers mute the 'Speaker' 
        # channel when muting the master channel, but they
        # don't unmute automatically. Thus, we work with that
        # channel too.
        if speaker_channel:
            for channel in ['Master', 'Speaker']:
                subprocess.Popen(['amixer', '-q', 'set', channel, state])
        else:
            for channel in ['Master']:
                subprocess.Popen(['amixer', '-q', 'set', channel, state])
        
        is_muted = mute
    
def check_mute():
    # Read the actual mute status from amixer.
    p1 = subprocess.Popen(["amixer", "get", "Master"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "-o", "off"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    muted_output = p2.communicate()[0]
    #muted_output = os.popen("amixer get Master | grep -o off").read()
    
    if "off" in muted_output:
        actual_mute=True
    else:
        actual_mute=False
    
    # Return what we have the state as, and the actual state.
    return (actual_mute, is_muted)

############################################
# Functions that work with the app running #
############################################

# Not necessary anymore but keeping it in for reference.
def restart():
    print 'Restarting Blockify'
    python = sys.executable
    os.execl(python, python, * sys.argv)

def trap_exit():
    print '\nStopping Blockify'
    # FIXME: this should not be necessary, fix toggle_mute().
    actual_mute, is_muted = check_mute()
    if actual_mute == True:
        speaker_channel = check_channels()
        if speaker_channel:
            for channel in ['Master', 'Speaker']:
                subprocess.Popen(['amixer', '-q', 'set', channel, 'unmute'])
        else:
            for channel in ['Master']:
                subprocess.Popen(['amixer', '-q', 'set', channel, 'unmute'])
        print 'Unmuted. Bye'
    sys.exit()

signal.signal(signal.SIGUSR1, lambda sig, hdl: block_current())
signal.signal(signal.SIGUSR2, lambda sig, hdl: restart())
signal.signal(signal.SIGTERM, lambda sig, hdl: trap_exit())
signal.signal(signal.SIGINT,  lambda sig, hdl: trap_exit())

#################################################
# Main loop and initialisation of CLI interface #
#################################################

def main():
    print "Starting Blockify"
    # Initially unmute the sound.
    toggle_mute()

    # Load the song list.
    song_list = load_song_list()
    # Initialize timestamp of SONGFILE to see when/if we need to reload it.
    old_timestamp = os.path.getmtime(SONGFILE)
    
    # Start the main loop.
    while(True):
        check_songlist()
        
        # Reload songlist if it changed.
        current_timestamp = os.path.getmtime(SONGFILE)
        if old_timestamp != current_timestamp:
            song_list = load_song_list()
            old_timestamp = current_timestamp
        
        time.sleep(1)


if __name__ == "__main__":
    print "please use ./blockify to run blockify.py"
    main()
