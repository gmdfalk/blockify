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

Example AUR installation routine:  
``` bash
mkdir blockify
cd blockify
wget https://aur.archlinux.org/packages/bl/blockify/PKGBUILD
makepkg
sudo pacman -U blockify-X.Y-Z-any.pkg.tar.xz
```

##### Direct (pip/setup.py)
If there is no blockify package available on your distribution, you'll have to install it directly via one of pythons many installation tools.  

Example manual/direct installation routine:  
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
* 
Additionally, blockify makes use of pulseaudio sinks, allowing processes to be muted individually.    
If you do not have/want pulseaudio, blockify will mute the system sound during commercials instead of just Spotify. The interlude music feature will not work as a consequence.

#### Detection
Blockify will automatically detect and block ads for you so besides starting it, there's not a lot to do.  
However, it also comes with the option to complement or replace that autoblock functionality with a blocklist (saved as ~/.config/blockify/blocklist.txt).  
Blocklist-Entries are case-sensitive and greedy, e.g. the entry `Blood` would not only block all Bloodhound Gang songs but any song by any artist starting with `"Blood"`.  

##### CLI
Blockify has a CLI/daemon that you can start with `blockify`.  
`blockify -h` will print out a help text with available options.  
To block or unblock a song with the cli running, use `pkill -USR1 -f "python2.*blockify"` and `pkill -USR2 -f "python2.*blockify"` respectively.   

##### GUI
Alternatively, you can use the GUI with `blockify-ui` which spawns this window.  
![ScreenShot](http://a.pomf.se/bimbza.jpg)
- Play, Previous, Next: These buttons use dbus to send audio control commands to spotify.
- Block/Unblock: Add/Remove the currently playing song to/from the blocklist.
- Mute/Unmute: Mute/Unmute the current song. Only works if "Manual" checkbox is activated.
- Manual: Disables automatic mute of ads and instead allows you to mute manually.
- Show/Hide Cover: Enable/Disable display of cover art image.
- Autohide: If this option is checked, the cover art will be automatically hidden whenever a commercial is playing.
- Open/Close List: Opens a small popup text editor with the blocklist opened where you can edit and save it. Keybinds: Control-S (save), Control-W/Q (close), Control-D (delete current line).
- Exit: Stop blockify cleanly, i.e. unmute sinks, update blocklist and generally clean up.
- Enable/disable Player: Shows and enables resp. hides and disables the mini audio player (interlude player) below the button which will play music instead of commercials.
- Prev, Play/Pause, Next (bottom): Media buttons to control the interlude player.
- Browse: Allows you to open m3u-playlists and/or audio files on the fly. You can select multiple items and combine playlists with audio files. The player will automatically load those and discard the previous playlist.  
- Autoresume: If enabled, the interlude player will switch back to Spotify as soon as the commercials end. If disabled, the current interlude song will be finished before switching back to Spotify.  

##### Configuration
Please see the provided [example_blockify.ini](https://github.com/mikar/blockify/blob/master/blockify/data/example_blockify.ini) on what settings are available and their purpose.  
Blockify automatically creates a configuration file at `$HOME/.config/blockify/blockify.ini` if you don't have one already. It will also tell you via ERROR-logging messages, if you configuration file is faulty or incomplete, in which case the options that could be read will be merged with the default options you see in example_blockify.ini but you'll still want to fix your configuration file.  

##### Interlude Music
From version 1.4 onwards blockify can play music of your choice during commercial breaks.  
The default behaviour is for blockify to automatically play the first song in the playlist file (should you have one), when a commercial starts playing.  
Alternatively, you can set the autoresume option to False which will cause blockify to always finish the current interlude song before resuming spotify playback.   

The interlude feature only works if you use pulseaudio (i.e. spotify needs to run in its own sink so it can be muted separately).    
To make use of interlude music you have to configure a playlist file in `~/.config/blockify/playlist.m3u`.  
The playlist system is (mostly) M3U-compliant.  

An example playlist:
```
# Lines starting with "#" will be ignored.
# Absolute path to a file:
/media/music/foo/bar.mp3
# Relative path to a file (as seen from playlist location):
foo/bar.flac
# Relative path to another playlist. Just make sure the other playlist doesn't link back or else you'll get a very long playlist:
baz.m3u
# A whole directory:
/media/music/foo
# It's also possible to give full URIs:
file:///media/music/foo/bar.mp4
http://www.example.com/foo/bar.wav
# A radio station. Note that radio streams don't usually end so you'll have to switch
# back to spotify manually, enable autoresume or specify the radio_timeout in the config file.
http://skyserver5.skydisc.net:8000
```
You can use relative and absolute paths as well as basically any audio source/format, as long as you have the respective gstreamer codec installed. 

## Changelog
- v1.7.1 (2014-12-26): Fix for #32 (introduced playback_delay option), better load_config and update_slider error catching
- v1.7 (2014-12-24): Unmute delay (avoid last second of commercial), segfault bug fix, Timeout for radio stations, logging improvements, threading improvements (complete switch to gtk), refactorings.
- v1.6 (2014-12-23): Configuration file, playlist and notepad improvements, bug fixes.
- v1.5 (2014-12-21): Mini-audio player for interlude music (media buttons, interactive progress bar, interactive playlist, ...)
- v1.4 (2014-12-14): Interlude music of your choice during commercials  
- v1.3 (2014-12-14): GUI-Update (Buttons, Icons, Systray) and Refactoring  
- v1.2 (2014-12-11): Cover-Art and config/cache folder in ~/.config/blockify  
- v1.1 (2014-06-17): Autodetection of commercials  
- v1.0 (2014-05-02): First moderately stable version  
- v0.9 (2014-04-29): Pulseaudio (sink) support  

## Troubleshooting
If you experience errors or unexpected behaviour, please start blockify/blockify-ui with the -vvv parameter to enable debug logging and see if you get any helpful information this way.  
You're welcome to open an issue on this site and ask for help but when you do, please provide the following information:  
- A debug log, acquired by starting blockify(-ui) via `blockify(-ui) -vvv -l logfile`. Then upload it with `curl -F "c=logfile" https://ptpbw.pw` (or paste it to a git or bpaste.net or directly into the git issue, you get the idea).
- The blockify version: `blockify --version`.
- If you suspect pulseaudio as culprit, the list of sinks: `pacmd list-sink-inputs | curl -F c=@- https://ptpb.pw`.

## Known Issues
- If Spotify is minimized to the system tray, ad detection will not work.  
- If Notifications are disabled, ad detection will not work.
