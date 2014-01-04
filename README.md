blockify
========

Mute songs on spotify (wine version only), requires wmctrl.

When you find a song you want to mute, you need to add it to
~/.blockify_list either manually (find out the name with wmctrl -l) or via:
pkill -USR1 -f python2.*blockify
After adding a new entry you need to restart blockify manually or with:
pkill -USR2 -f python2.*blockify
Aliasing/Binding these commands works well for me.

Optionally, there is a ui you can use, credit goes to
Rod Persky (https://github.com/Rod-Persky/blockify)

Cheers,
mikar

To use media keys with Wine Spotify use [spotify_cmd](https://code.google.com/p/spotifycmd/).
