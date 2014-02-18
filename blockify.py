#!/usr/bin/env python3

from spotify import Spotify

import time

def blockify(spotify):
    spotify.prev()

    now = int(time.time())
    title = spotify.get_song_title()
    length = spotify.get_song_length()
    end_time = now + length

    while spotify.is_running():
        cur_title = spotify.get_song_title()
        
        if cur_title != title:
            print("Song Changed")
            print("Song ends in ", spotify.get_song_length(), " seconds")
            length = spotify.get_song_length()
            end_time = now + length
            title = cur_title

        status = str(spotify.get_property('PlaybackStatus'))
        
        while status == 'Paused':
            now = int(time.time())
            status = str(spotify.get_property('PlaybackStatus'))
            print("PAUSED: Song ends in", end_time - now, "seconds")
            end_time += 1
            time.sleep(1)
        
        now = int(time.time())
        
        if now > end_time and cur_title == title:
            print("Muting")
            spotify.toggle_mute()
            while cur_title == title:
                cur_title = spotify.get_song_title()
                time.sleep(0.5)
            print("Unuting")
            spotify.toggle_mute()
                
        time.sleep(1)
            

def main():
    spotify = Spotify()
    blockify(spotify)

if __name__ == "__main__":
    main()
