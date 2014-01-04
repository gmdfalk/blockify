blockify
========

Mute songs on spotify (wine version only), requires wmctrl.

Optionally, there is a ui you can use, credit goes to  
Rod Persky (https://github.com/Rod-Persky/blockify)  

Installation:  
Keep blockify and its symlink to blockify.py as well as blockify-ui in the  
same directory, ideally in your users $PATH.  
Copy list_example.txt to ~/.blockify_list  

Usage:  
When you find a song you want to mute, you need to add it to  
~/.blockify_list either manually (find out the name with wmctrl -l) or via:  
`pkill -USR1 -f python2.*blockify`  
After adding a new entry you need to restart blockify manually or with:  
`pkill -USR2 -f python2.*blockify`  
Aliasing/Binding these commands in your shell/WM/DE is probably the most  
comfortable.

The UI is pretty self-explanatory. Closing the UI will currently end all  
running instances of blockify. Might get changed.  
  
Cheers,  
mikar  
  
To use media keys with Wine Spotify use [spotify_cmd](https://code.google.com/p/spotifycmd/).
