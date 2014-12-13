# blockify
Blockify is a linux only application that allows you to automatically mute songs and advertisements in Spotify.

### Installation
#### AUR
Arch-Linux users can find blockify in the [AUR](https://aur.archlinux.org/packages/blockify/).

#### Manually
Before installing blockify, please make sure you have the appropriate dependencies installed.

Hard dependencies (on ArchLinux):
- pygtk python2-wnck python2-dbus alsa-utils python2-docopt
Soft dependencies:
- pulseaudio
Installation tools:
- python2-pip (preferred) OR python2-setuptools 

Actual installation procedure is as follows:
``` bash
git clone https://github.com/mikar/blockify
cd blockify
sudo pip2 install . OR python2 setup.py install
```

### Usage
Blockify will automatically detect and block ads but it also comes with the option to complement or replace that functionality with a block list which will be saved as ~/.config/blockify/blocklist.  

Blockify has a CLI/daemon that you can start with `blockify`.
`blockify -h` will print out a help text with available options.
To block or unblock a song with the cli running, use `pkill -USR1 -f "python2.*blockify"` and `pkill -USR2 -f "python2.*blockify"` respectively.  

Alternatively, you can use the GUI with `blockify-ui` which spawns this window.
![ScreenShot](http://a.pomf.se/vxnnwo.jpg)  

### Changelog
v1.4 (coming soon): Interlude music of your choice during commercials  
v1.3 (2014-12-13): GUI-Update and Refactoring  
v1.2 (2014-12-11): Cover-Art and config/cache folder in ~/.config/blockify  
v1.1 (2014-06-17): Autodetection of commercials  
v1.0 (2014-05-02): First moderately stable version  
v0.9 (2014-04-29): Pulseaudio (sink) support  

### Known Issues
- If Spotify is minimized to the system tray, ad detection will not work. 
