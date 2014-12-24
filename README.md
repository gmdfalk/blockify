# blockify
Blockify is a linux only application that allows you to automatically mute songs and advertisements in Spotify.  

## Installation
##### Dependencies
Before installing blockify, please make sure you have the appropriate dependencies installed. Package names are for ArchLinux and will probably differ slightly between distributions. 
- Mandatory: pygtk alsa-utils gstreamer0.10-python python2-wnck python2-dbus
- Optional (but highly recommended): pulseaudio python2-docopt  
- Installation tools: python2-pip (preferred) OR python2-setuptools  

##### Automatic (AUR)
Arch-Linux users can find blockify in the [AUR](https://aur.archlinux.org/packages/?O=0&K=blockify). You can choose between a stable version ([blockify](https://aur.archlinux.org/packages/blockify/)) or the hopefully stable development version ([blockify-git](https://aur.archlinux.org/packages/blockify-git/)). I try to publish new changes from the latter to the former version quickly so most of the time there is little difference between these two packages other than the source.  
Example installation routine:  
``` bash
mkdir blockify
cd blockify
wget https://aur.archlinux.org/packages/bl/blockify/PKGBUILD
makepkg
sudo pacman -U blockify-X.Y-Z-any.pkg.tar.xz
```

##### Direct (pip/setup.py)
If there is no blockify package available on your distribution, you'll have to install it directly via one of pythons many installation tools.  
Example installation routine:  
``` bash
git clone https://github.com/mikar/blockify
cd blockify
sudo pip2 install . (OR sudo python2 setup.py install)
```

## Usage
#### Requirements
It is important to know that blockify relies on dbus (and, for some features, on pulseaudio) for ad detection.  
If any of these criteria are true ad detection _will not work_:  
* DBus is disabled
* Spotify is minimized to the system tray (task bar is fine)
* Notifications are disabled in Spotify

#### Detection
Blockify will automatically detect and block ads for you so besides starting it, there's not a lot to do.  
However, it also comes with the option to complement or replace that autoblock functionality with a blocklist (saved as ~/.config/blockify/blocklist).  

##### CLI
Blockify has a CLI/daemon that you can start with `blockify`.  
`blockify -h` will print out a help text with available options.  
To block or unblock a song with the cli running, use `pkill -USR1 -f "python2.*blockify"` and `pkill -USR2 -f "python2.*blockify"` respectively.   

##### GUI
Alternatively, you can use the GUI with `blockify-ui` which spawns this window.  
![ScreenShot](http://a.pomf.se/vxnnwo.jpg)  
- Play, Previous, Next: These buttons use dbus to send audio control commands to spotify.
- Block/Unblock: Add/Remove the currently playing song to/from the blocklist.
- Mute/Unmute: Mute/Unmute the current song. Only works if "Manual" checkbox is activated.
- Manual: Disables automatic mute of ads and instead allows you to mute manually.
- Show/Hide Cover: Enable/Disable display of cover art image.
- Autohide: If this option is checked, the cover art will be automatically hidden whenever a commercial is playing.

##### Interlude Music
From version 1.4 onwards blockify can play music of your choice during commercial breaks.  
The default behaviour is for blockify to automatically play the first song in the playlist file (should you have one), when a commercial starts playing.  
Alternatively, you can disable autoresume which will cause blockify to always finish the current interlude song before resuming spotify playback.  

The interlude feature only works if you use pulseaudio (i.e. spotify needs to run in its own sink so it can be muted separately).    
To make use of interlude music you have to configure a playlist file in `~/.config/blockify/playlist.m3u`.  
The playlist system is (mostly) M3U-compliant.  

An example playlist:
```
# Lines starting with "#" will be ignored.
# Absolute path to a file.
/media/music/foo/bar.mp3
# Relative path to a file (as seen from playlist location).
foo/bar.flac
# This is a radio station. Note that radio streams don't usually end so you'll have to switch
# back to spotify manually or specify the max_timeout in the config file.
http://skyserver5.skydisc.net:8000
# It's also possible to give full URIs:
file:///media/music/foo/bar.mp4
http://www.example.com/foo/bar.aiff
mms://www.example.com/foo/bar.avi
```
You can use relative and absolute paths as well as basically any audio source/format, as long as you have the respective gstreamer codec installed. 

## Changelog
- v1.6 (2014-12-23): Configuration file, playlist and notepad improvements, bug fixes.
- v1.5 (2014-12-21): Mini-audio player for interlude music (media buttons, interactive progress bar, interactive playlist, ...)
- v1.4 (2014-12-14): Interlude music of your choice during commercials  
- v1.3 (2014-12-14): GUI-Update (Buttons, Icons, Systray) and Refactoring  
- v1.2 (2014-12-11): Cover-Art and config/cache folder in ~/.config/blockify  
- v1.1 (2014-06-17): Autodetection of commercials  
- v1.0 (2014-05-02): First moderately stable version  
- v0.9 (2014-04-29): Pulseaudio (sink) support  

## Known Issues
- If Spotify is minimized to the system tray, ad detection will not work.  
- If Notifications are disabled, ad detection will not work.
