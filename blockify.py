#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
blockify:
    Mute Spotify tracks (only works on the wine version)
    requires wmctrl to be installed.
    
    When you find a track you want to mute, you need to add it to
    track_list. Find out the name with wmctrl -l when the track is playing.
    you only need the part after "Spotify - " and you can shorten if you
    want, e.g. Spotify - Bloodhound Gang – Along Comes Mary becomes
    Bloodhound, which would mute all tracks that start with Bloodhound
    
    After adding a new entry you need to restart blockify manually or with:
    pkill -USR1 -f blockify
    
    cheers
"""

import subprocess, time, sys, os, signal
spotify = "Spotify -"
track_list_filename = "track_list.txt"

# Method for loading track_list from a file
def load_track_list():
    track_list_file = open(track_list_filename, "r")
    track_list = track_list_file.read()
    track_list_file.close()
    track_list = track_list.split("\n")
    
    clean_list = []
    for item in track_list:
        if len(item.strip()):
            clean_list.append(item)

    track_list = clean_list
    track_list = [spotify + " " + s for s in track_list]
    return track_list

# Method to add to the track_list file
def modify_track_list(artist_album):
    track_list_file = open(track_list_filename, "r")
    current_track_list = track_list_file.read()
    track_list_file.close()
    
    track_list = current_track_list + "\n" + artist_album
    track_list_file = open(track_list_filename, "w")
    track_list_file.write(track_list)
    track_list_file.close()
    
    return load_track_list()

# When the program starts, the track_list is read
track_list = load_track_list()


def mute():
    subprocess.Popen(['amixer', '-q', 'set', 'Master', 'mute'])
    global is_muted
    is_muted = True

def unmute():
    subprocess.Popen(['amixer', '-q', 'set', 'Master', 'unmute'])
    global is_muted
    is_muted = False
  
def restart():
    python = sys.executable
    os.execl(python, python, * sys.argv)

def signal_handler(signum, frame):
    if signum == 2:
        print 'Exiting'
        unmute()
        sys.exit(0)
    else:
        print signum, 'Restarting'
        restart()

signal.signal(signal.SIGUSR1, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def get_windows():
    pipe = get_windows_pipe()
    separator = ""
    return separator.join(pipe_readlines(pipe))
  
def get_windows_pipe():
    pipe = subprocess.Popen(['wmctrl', '-l'], stdout=subprocess.PIPE).stdout
    return pipe

def pipe_readlines(pipe):
    try:
        return pipe.readlines()
    except:
        return ""
    
def check_tracklist(windows):
    found = False
    
    for track in track_list:
        if (windows.find(track.strip('\n')) >= 0):
            found = True
            break
      
    if found:
        if (not is_muted):
            mute()
            print 'Muting'
    elif is_muted:
        unmute()
        
    return found

def get_playing(windows, artist_album=""):
    window_list = windows.split("\n")
    
    try:       
        for item in window_list:
            if spotify in item:
                window_title = item[item.find(spotify):].split("-")
                artist_album = window_title[1].strip()
    except:
        pass
    
    return artist_album

def main():
    global is_muted    
    is_muted = False
    unmute()
  
    while(True):
        windows = get_windows()
        check_tracklist(windows)
        time.sleep(1)


if __name__ == "__main__":
    print "Starting Blockify"
    main()
