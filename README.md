blockify
========

Mute Spotify advertisements.
Works with both the Linux and Wine version of Spotify but depends on the wnck library.  

Installation
-------------

Simply clone or download this repository into any folder and run
`./blockify`.  
No blocklist will be installed by default but you can find a basic  
example in the installation/clone directory. To use it, copy it to your $HOME:  

``` bash
cp blockify_list ~/.blockify_list
```
  
Optionally, there is a GUI you can use, by calling ./blockify-ui  

Usage
------ 

When you find a song you want to mute, you need to add it to
~/.blockify_list either manually or via: 
 
``` bash
pkill -USR1 -f python2.*blockify
```

Aliasing/Binding this to your shell/WM/DE is probably the most
comfortable and safe way to deal with it.

GUI Interface
-------------

The UI is pretty self-explanatory. Closing the UI will currently end all  
running instances of blockify, operating in much the same way that the
windows version of blockify does. You can enable the auto add function
which will then enable you to add tracks by pressing mute when anything
comes up which you don't like - Once it is added you'll need to enable
the auto add function; also the auto add function turns off when you
hit no as you might actually be muting audio for another reason.
  
To use media keys with Wine Spotify use [spotify_cmd](https://code.google.com/p/spotifycmd/).
