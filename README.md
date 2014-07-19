# blockify

Blockify is a linux only application that allows you to automatically mute songs and advertisements in both the wine and native versions of Spotify.  
It depends on gtk and wnck and will currently only work if Spotify is not minimized to the system tray (minimized to task bar is fine). 

### Installation
Clone the repository with `git clone https://github.com/mikar/blockify`.  
You can then either run the cli/gui directly or install it with `pip install .`  
Arch-Linux users can find blockify in the [AUR](https://aur.archlinux.org/packages/blockify/).
For the linux version of Spotify, blockify will automatically detect and block ads but it also comes with the option to complement or replace that functionality with a block list which will be saved as ~/.blockify_list.
For the windows (wine) version of Spotify, you will have to use the block list as automatic detection is not supported.
Keep in mind that you can edit the block list entries to broaden the matching pattern.  
For instance, `Bloodhound Gang – The Bad Touch` will only block that song while `Blood` will block not only all Bloodhound Gang Songs but any artist whose name starts with "Blood".  

### GUI Usage
![ScreenShot](http://a.pomf.se/dzngqg.png)  
Blockify comes with a GUI which is tailored for the native linux version of Spotify.  
It does work with the Wine version but Play/Pause and Previous/Next will not be available.  

### CLI Usage

New with v1.1: Automatic ad detection (won't work for the wine version)

`blockify -h` will print out a help text with available options.

When you find a song you want to mute, add it to ~/.blockify_list either manually or with:
``` bash
pkill -USR1 -f "python2.*blockify"
```

Similarly, to unblock a song, you can either remove it manually from the textfile or send SIGUSR2:
``` bash
pkill -USR2 -f "python2.*blockify"
```
Note that this will only work for unedited block entries.  

Alternatively, this command will remove the last added entry from the blocklist:
``` bash
sed -ie '$d' ~/.blockify_list
```

Aliasing/Binding this to your shell/WM/DE is probably the most comfortable and safe way to deal with it.

### DBus Interface

Thanks to [kerbertx](https://github.com/kebertx/blockify), a dbus interface for the native Spotify client is now included, too.  
The docstring inside spotifydbus.py explains how it's used.  
If you're using the wine version of Spotify you might want to take a look at [spotify_cmd](https://code.google.com/p/spotifycmd/) for similar functionality.
