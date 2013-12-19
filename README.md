blockify
========

mute spotify tracks (only works on the wine version)
requires wmctrl to be installed.

when you find a track you want to mute, you need to add it to track_list.
find out the name with wmctrl -l when the track is playing.
you only need the part after "Spotify - " and you can shorten if you want,
e.g. Spotify - Bloodhound Gang – Along Comes Mary becomes Bloodhound,
which would mute all tracks that start with Bloodhound

after adding a new entry you need to restart blockify manually or with:
pkill -USR1 -f blockify

cheers

To use media keys with Wine Spotify use [spotify_cmd](https://code.google.com/p/spotifycmd/).
