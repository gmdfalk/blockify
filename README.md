blockify
========

mute spotify commercials (only works on the wine version)

requires wmctrl to be installed.

when you find a commercial that is not yet recognized, you need to add it to ad_list.
find out the name with wmctrl -l when the ad is playing.
you only need the part after "Spotify - "

after adding a new entry you need to restart blockify manually or with:
pkill -USR1 -f blockify
cheers

To use media keys with Wine Spotify use [spotify_cmd](https://code.google.com/p/spotifycmd/)
