# blockify

Blockify is a GNU/Linux application that allows you to automatically mute songs and advertisements in both the wine and native versions of Spotify.  
It depends on the wnck library and will currently __not__ work if Spotify is minimized.  

### Installation
Clone the repository with `git clone https://github.com/mikar/blockify`.  
You can then either the cli/gui directly or install it with `pip install .`.  
Arch-Linux users can find blockify in the [AUR](https://aur.archlinux.org/packages/blockify/).

### Usage

When you find a song you want to mute, add it to ~/.blockify_list either manually or with:
 
``` bash
pkill -USR1 -f python2.*blockify
```

This command will remove the last added entry:
``` bash
sed -ie '$d' ~/.blockify_list
```

Aliasing/Binding this to your shell/WM/DE is probably the most comfortable and safe way to deal with it.

### DBus Interface

Thanks to [kerbertx](https://github.com/kebertx/blockify), a dbus interface for the native Spotify client is now included, too.  
The docstring inside spotifydbus.py explains how it's used.  
If you're using the wine version of Spotify you might want to use [spotify_cmd](https://code.google.com/p/spotifycmd/) for similar functionality.