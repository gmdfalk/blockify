#!/usr/bin/env python3

import re
import time
import subprocess
from spotify import Spotify

def toggle_mute(force=False):
    '''Finds spotify's audio sink and toggles it between muted and not muted'''

    pacmd_out = subprocess.check_output(["pacmd", "list-sink-inputs"])
    pidof_out = subprocess.check_output(["pidof", "spotify"])

    pattern = re.compile(r'(?: index|muted|application\.process\.id).*?(\w+)')
    pids = pidof_out.decode('utf-8').strip().split(' ')
    output = pacmd_out.decode('utf-8')

    # Every third element is a key, the value is the preceding two
    # elements in the form of a tuple - {pid : (index, muted)}
    info = pattern.findall(output)
    idxd = {info[3*n+2] : (info[3*n], info[3*n+1])
            for n in range(0, len(info) // 3)}

    pid = [k for k in idxd.keys() if k in pids][0]
    index, muted = idxd[pid]

    if muted == 'no' or force:
        subprocess.call(["pacmd", "set-sink-input-mute", index, '1'])
    else:
        subprocess.call(["pacmd", "set-sink-input-mute", index, '0'])


def blockify(spotify):
    '''Checks if an ad is playing. If so mutes spotify until a new song
    comes on.'''
    spotify.prev()

    now = int(time.time())
    title = spotify.get_song_title()
    length = spotify.get_song_length()
    end_time = now + length

    while spotify.is_running():
        now = int(time.time())
        cur_title = spotify.get_song_title()

        if cur_title != title:
            print("CHANGED: Song ends in", spotify.get_song_length(), "seconds")
            length = spotify.get_song_length()
            end_time = now + length
            title = cur_title

        status = str(spotify.get_property('PlaybackStatus'))

        if status == 'Paused':
            print("PAUSED: Song ends in", end_time - now, "seconds")
            while status == 'Paused':
                time.sleep(1)
                end_time += 1
                status = str(spotify.get_property('PlaybackStatus'))
            print("PLAYING")

        if now > end_time and cur_title == title:
            print("MUTING")
            toggle_mute()
            while cur_title == title:
                cur_title = spotify.get_song_title()
                time.sleep(0.5)
            print("UNUTING")
            toggle_mute()

        time.sleep(1)


def main():
    '''Blockifies a Spotify!'''
    spotify = Spotify()
    blockify(spotify)

if __name__ == "__main__":
    main()
