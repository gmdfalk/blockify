blockify
========

Mute songs on spotify (wine version only), requires wmctrl.

Optionally, there is a ui you can use, by calling ./blockify-ui

Installation
-------------

Blockify can be installed anywhere, and is super easy to get started!
Simply clone or download this repository into any folder and run
`./blockify`. Initially no block list that is 'shipped' will install
by default, however we do have an example in blockify_list. This example
Blockify list can be installed by calling (from the Blockify folder)

``` bash
cp blockify_list ~/.blockify_list
```


Usage
------ 

When you find a song you want to mute, you need to add it to
~/.blockify_list either manually or via: 
 
``` bash
pkill -USR1 -f python2.*blockify
```

Aliasing/Binding this to your shell/WM/DE is probably the most
comfortable and safe way to deal with it. For example, you can do:

``` bash
echo "alias blockify_add pkill -USR1 -f python2.*blockify >> ~/.bash_rc
```

Which will append this alias to your bash profile. You will have to
manually remove it if you no longer want it by finding the line in
your `~/.bash_rc` file and deleting it.


GUI Interface
-------------

The UI is pretty self-explanatory. Closing the UI will currently end all  
running instances of blockify, operating in much the same way that the
windows version of blockify does. You can enable the auto add function
which will then enable you to add tracks by pressing mute when anything
comes up which you don't like - Once it is added you'll need to enable
the auto add function; also the auto add function turns off when you
hit no as you might actually be muting audio for another reason.
  
Cheers,  
mikar  
  
To use media keys with Wine Spotify use [spotify_cmd](https://code.google.com/p/spotifycmd/).
