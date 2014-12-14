# blockify
Blockify is a linux only application that allows you to automatically mute songs and advertisements in Spotify.  

## Installation
##### AUR
Arch-Linux users can find blockify in the [AUR](https://aur.archlinux.org/packages/blockify/).  

##### Manually
Before installing blockify, please make sure you have the appropriate dependencies installed.  
- Hard dependencies: pygtk python2-wnck python2-dbus alsa-utils python2-docopt  
- Soft dependencies: pulseaudio  
- Installation tools: python2-pip (preferred) OR python2-setuptools  

Actual installation procedure is as follows:  
``` bash
git clone https://github.com/mikar/blockify
cd blockify
sudo pip2 install . OR python2 setup.py install
```

## Usage
Blockify will automatically detect and block ads but it also comes with the option to complement or replace that functionality with a block list which will be saved as ~/.config/blockify/blocklist.  

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
This feature only works if you use pulseaudio (i.e. spotify needs to run in its own sink).  
To make use of interlude music you have to configure a playlist file in `~/.config/blockify/playlist`.

An example playlist:
```
file:///media/shared/media/music/2014-ed_sheeran-x/01 One.mp3
file:///media/shared/media/music/2014-ed_sheeran-x/02 I'm a Mess.mp3
file:///media/shared/media/music/2014-foo_fighters-sonic_highways/01. Something From Nothing.mp3
file:///media/shared/media/music/2014-foo_fighters-sonic_highways/02. The Feast and the Famine.mp3
```
Once you have created the playlist, blockify will do the rest for you. Right now, there is no error correction, so make sure the paths are correct.  
You'll notice that you have to use complete URIs. The upside is that you can use basically any audio source this way, e.g. another radio station.  
This feature is currently rather dumb and will stop playing the interlude music as soon as the commercial is over aside from not being integrated with the GUI yet.  
Updates coming soon.  

## Changelog
- v1.5 (ETA 2014-12-21): Mini-audio player for interlude music (media buttons, interactive progress bar, interactive playlist, ...)
- v1.4 (2014-12-14): Interlude music of your choice during commercials  
- v1.3 (2014-12-14): GUI-Update (Buttons, Icons, Systray) and Refactoring  
- v1.2 (2014-12-11): Cover-Art and config/cache folder in ~/.config/blockify  
- v1.1 (2014-06-17): Autodetection of commercials  
- v1.0 (2014-05-02): First moderately stable version  
- v0.9 (2014-04-29): Pulseaudio (sink) support  

## Known Issues
- If Spotify is minimized to the system tray, ad detection will not work. 
