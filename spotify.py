#!/usr/bin/env python3

import dbus

class Spotify(object):
    '''Wrapper for Spotify's DBus interface'''
    prop_path = 'org.freedesktop.DBus.Properties'
    player_path = 'org.mpris.MediaPlayer2.Player'
    spotify_path = 'org.mpris.MediaPlayer2.spotify'
    running = False

    session_bus = None
    proxy = None
    properties = None
    player = None

    def __init__(self):
        self.session_bus = dbus.SessionBus()
        try:
            self.proxy = self.session_bus.get_object(self.spotify_path,
                                                     '/org/mpris/MediaPlayer2')
        except:
            self.proxy = None
            print("Is Spotify not runnung?")

        if self.proxy:
            self.running = True
            self.properties = dbus.Interface(self.proxy, self.prop_path)
            self.player = dbus.Interface(self.proxy, self.player_path)


    def is_running(self):
        '''TODO: Make this not redundant'''
        return self.running


    def get_property(self, key):
        '''Gets the value from any available property'''
        if self.properties:
            return self.properties.Get(self.player_path, key)


    def toggle_pause(self):
        '''Calls PlayPause method'''
        if self.player:
            can_pause = self.get_property('CanPause')
            can_play = self.get_property('CanPlay')
            if can_pause and can_play:
                self.player.PlayPause()
            else:
                print("Cannot Play/Pause")


    def next(self):
        '''Tries to skip to next song'''
        if self.player:
            can_next = self.get_property('CanGoNext')
            if can_next:
                self.player.Next()
            else:
                print("Cannot Go Next")


    def prev(self):
        '''Tries to go back to last song'''
        if self.player:
            can_prev = self.get_property('CanGoPrevious')
            if can_prev:
                self.player.Previous()
            else:
                print("Cannot Go Previous")


    def seek(self, seconds):
        '''Calls (nonworking?) Seek method'''
        if self.player:
            can_seek = self.get_property('CanSeek')
            if can_seek:
                self.player.Seek(seconds)
            else:
                print("Cannot Seek")


    def get_song_length(self):
        '''Gets the length of current song from metadata (in seconds)'''
        metadata = self.get_property('Metadata')
        if metadata:
            return int(metadata['mpris:length'] / 1000000)


    def get_song_title(self):
        '''Gets title of current song from metadata'''
        metadata = self.get_property('Metadata')
        if metadata:
            return str(metadata['xesam:title'])


    def get_song_artist(self):
        '''Gets the artist of current song from metadata'''
        metadata = self.get_property('Metadata')
        if metadata:
            return str(metadata['xesam:artist'][0])


    def print_info(self):
        '''Prints all the information I can get from the dbus interface. Some
        of it is incorrect, but it's what I've got!'''
        if self.properties:
            interfaces = self.properties.GetAll(self.player_path)
            metadata = self.get_property('Metadata')

            i_keys = list(map(str, interfaces.keys()))
            i_keys.remove('Metadata')
            i_keys.sort()

            for i in i_keys:
                if len(i) < 7:
                    print(i, "\t\t= ", self.get_property(i))
                else:
                    print(i, "\t= ", self.get_property(i))

            print("")

            d_keys = list(metadata.keys())
            d_keys.sort()

            for k in d_keys:
                d = k.split(':')[1]

                if d == 'artist':
                    print(d, "\t\t= ", metadata[k][0])
                # elif d == 'length':
                elif len(d) < 7:
                    print(d, "\t\t= ", metadata[k])
                else:
                    print(d, "\t= ", metadata[k])
        else:
            print("Something is amiss")
