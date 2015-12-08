# blockify
Blockify is a linux only application that allows you to automatically mute songs and advertisements in Spotify.

**Important**: If you are using the 'old' Spotify client (version < 1.0), please use the legacy-branch (== blockify version < 2.0).


## Installation
##### Basic Requirements:
- Python3
- Pulseaudio
- Wmctrl
- Gstreamer1.0 (including the plugins you need for the audio formats you want to be able to play as interlude music)
- Spotify > 1.0.12 (to get the latest version follow the instructions given here [Spotify-Client-1-x-beta-] (https://community.spotify.com/t5/Spotify-Community-Blog/Spotify-Client-1-x-beta-for-Linux-has-been-released/ba-p/1147084))

##### Dependencies
Before installing blockify, please make sure you have the appropriate dependencies installed:  
`pacman -S python pulseaudio wmctrl gst-python alsa-utils libwnck3 pygtk python-dbus python-setuptools python-gobject python-docopt`

Package names are for ArchLinux and will probably differ slightly between distributions. 

##### Automatic
Arch-Linux users can find blockify in the [AUR](https://aur.archlinux.org/packages/?O=0&K=blockify). You can choose between a stable version ([blockify](https://aur.archlinux.org/packages/blockify/)) or the development version ([blockify-git](https://aur.archlinux.org/packages/blockify-git/)).  

Example ArchLinux installation routine:  
``` bash
curl -L -O https://aur4.archlinux.org/cgit/aur.git/snapshot/blockify.tar.gz
tar -xvf blockify.tar.gz
cd blockify
makepkg -sri
```

##### Direct (pip/setup.py)
If there is no blockify package available on your distribution, you'll have to install it directly via one of pythons many installation tools.  

First, the dependencies:  
``` bash
# Dependencies on Ubuntu 14.04 LTS
sudo apt-get install python3-pip libwnck-3-0 python3-gst-1.0 wmctrl
# Dependencies on Fedora
sudo dnf install python-dbus gstreamer-python libwnck3
```
Then blockify itself:  
``` bash
git clone https://github.com/mikar/blockify
cd blockify
sudo pip install .
# Create optional desktop icon
echo -e '[Desktop Entry]\nName=Blockify\nComment=Blocks Spotify commercials\nExec=blockify-ui\nIcon='$(python -c 'import pkg_resources; print pkg_resources.resource_filename("blockify", "data/icon-red-512.png")')'\nType=Application\nCategories=AudioVideo' | sudo tee /usr/share/applications/blockify.desktop
```

## Usage
#### Requirements
It is important to know that blockify relies on dbus (and, for some features, on pulseaudio) for ad detection.  
If any of these statements are true for your configuration, ad detection will _not_ work:  
* DBus is disabled
* Spotify is minimized to the system tray (task bar is fine)
* Notifications are disabled in Spotify  

Additionally, blockify makes use of pulseaudio sinks, allowing processes to be muted individually.    
If you do not have/want pulseaudio, blockify will mute the system sound during commercials instead of just Spotify. The interlude music feature will not work as a consequence.

#### Detection
Blockify will automatically detect and block ads for you so besides starting it after running spotify, there's not a lot to do.  
However, it also comes with the option to complement or replace that autoblock functionality with a blocklist (saved as ~/.config/blockify/blocklist.txt).  
Blocklist entries are case-sensitive and greedy, e.g. the entry `Blood` would match any artist starting with those exact five letters.    

#### Controls/Actions
Blockify accepts several signals:
* SIGINT(9)/SIGTERM(15): Exit cleanly.
* SIGUSR1(10): Block current song.
* SIGUSR2(12): Unblock current song.
* SIGRTMIN(34): Play previous spotify song.
* SIGRTMIN+1(35): Play next spotify song.
* SIGRTMIN+2(36): Toggle play/pause the current spotify song.
* SIGRTMIN+3(37): Toggle block state of current song.
* SIGRTMIN+10(44): Play previous interlude song.
* SIGRTMIN+11(45): Play next interlude song.
* SIGRTMIN+12(46): Toggle play/pause the current interlude song.
* SIGRTMIN+13(47): Toggle interlude autoresume.

Example usages:
```bash
pkill -USR1 -f "python2.*blockify"
pkill -RTMIN+1 -f "python2.*blockify"
alias btoggle='pkill -RTMIN+2 -f "python2.*blockify"'
```
Bind to keys for fun and profit.

##### CLI
Blockify has a CLI/daemon that you can start with `blockify`.  
`blockify -h` will print out a help text with available options.  

##### GUI
Alternatively, you can use the GUI with `blockify-ui` which spawns this window.  
![ScreenShot](http://i.imgur.com/c4oIZMX.jpg)
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


## Troubleshooting
## Known issues
- If Spotify is minimized to the system tray, ad detection will not work.
- If DBus/Notifications are disabled, ad detection will not work.

### Common issues 
* `ImportError: No module named gst`: You need to install gst-python.  
* Interlude music not playing: You might need to install gstreamer codecs (-bad, -ugly, ...).  
* Configuration is not loaded properly: Syntax might have changed between blockify versions. If in doubt, delete your configuration file. It will be rewritten with current defaults.  

### Debugging
If you can't find or fix the issue you are having by yourself, you are welcome to open an issue on this site. When you do, **please** provide the following information:
- A debug log, acquired by starting blockify(-ui) via `blockify(-ui) -vvv -l logfile`. Then upload it with `curl -F "c=logfile" https://ptpbw.pw` or paste it to a gist or bpaste.net or directly into the git issue (preferably with code tags -> three backticks before and after the snippet).
- The blockify version: `blockify --version`.
- If you suspect pulseaudio as culprit, the list of sinks: `pacmd list-sink-inputs | curl -F c=@- https://ptpb.pw`.


## Similar open-source projects
### On Linux:
- [Spotify-AdKiller](https://github.com/SecUpwN/Spotify-AdKiller) - automatic ad-blocker written in Bash

### On Windows:
- [Spotify-Ad-Blocker](https://github.com/Xeroday/Spotify-Ad-Blocker)

### On OS X:
- [SpotiFree](https://github.com/ArtemGordinsky/SpotiFree)


## Changelog
- v3.0.0 (2015-10-16): Remove beta status and port to python3 and gstreamer1.0 (see [issue #59](https://github.com/mikar/blockify/issues/59)).
- v2.0.1 (2015-10-05): (prerelease) Fix [issue #58](https://github.com/mikar/blockify/issues/58) and [issue #38](https://github.com/mikar/blockify/issues/38).  
- v2.0.0 (2015-09-05): (prerelease) Added rudimentary support for Spotify v1.0 and higher. Fixed autoplay option.  
- v1.9.0 (2015-08-15): Fix [issue #52](https://github.com/mikar/blockify/issues/52), introduce autoplay option and change start_spotify option to boolean type  
- v1.8.8 (2015-07-11): Fix [issue #46](https://github.com/mikar/blockify/issues/46) and [issue #47](https://github.com/mikar/blockify/issues/47)  
- v1.8.7 (2015-06-11): Pressing play will now properly pause interlude music before resuming spotify playback.
- v1.8.6 (2015-05-10): Minor refactoring and removed incomplete "fix" for [issue #44](https://github.com/mikar/blockify/issues/44).
- v1.8.5 (2015-05-09): Signal cleanups and [issue #44](https://github.com/mikar/blockify/issues/44) again.
- v1.8.4 (2015-05-08): Add additional signals for both spotify and interlude controls (prev/next/playpause, ...), see Controls/Actions section in this README
- v1.8.3 (2015-05-06): Fix [issue #44](https://github.com/mikar/blockify/issues/44): Cancel current interlude song and resume spotify playback if next spotify song button is clicked when no ad is playing
- v1.8.2 (2015-03-18): Reintroduced pacmd_muted_value option in general section ([issue #38](https://github.com/mikar/blockify/issues/38)). Added `gobject.threads_init()` to address ([issue #42](https://github.com/mikar/blockify/issues/42)). 
- v1.8.1 (2015-03-17): Added start_shuffled option in interlude-section ([issue #41](https://github.com/mikar/blockify/issues/41))
- v1.8.0 (2015-03-15): Added substring_search option ([issue #36](https://github.com/mikar/blockify/issues/36)). Added pacmd_muted_value option ([issue #38](https://github.com/mikar/blockify/issues/38)). Removed gtk.threads_init() ([issue #39](https://github.com/mikar/blockify/issues/39)).
- v1.7.2 (2015-01-10): Added unmute_delay option for the GUI, too. Removed forced unmute when Spotify is not playing a song or blockify can't find an ad. 
- v1.7.1 (2014-12-26): Fix for [issue #32](https://github.com/mikar/blockify/issues/32) (introduced playback_delay option), better load_config and update_slider error catching
- v1.7 (2014-12-24): Unmute delay (avoid last second of commercial), segfault bug fix, Timeout for radio stations, logging improvements, threading improvements (complete switch to gtk), refactorings.
- v1.6 (2014-12-23): Configuration file, playlist and notepad improvements, bug fixes.
- v1.5 (2014-12-21): Mini-audio player for interlude music (media buttons, interactive progress bar, interactive playlist, ...)
- v1.4 (2014-12-14): Interlude music of your choice during commercials  
- v1.3 (2014-12-14): GUI-Update (Buttons, Icons, Systray) and Refactoring  
- v1.2 (2014-12-11): Cover-Art and config/cache folder in ~/.config/blockify  
- v1.1 (2014-06-17): Autodetection of commercials  
- v1.0 (2014-05-02): First moderately stable version  
- v0.9 (2014-04-29): Pulseaudio (sink) support  
