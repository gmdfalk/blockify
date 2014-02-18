Blockify
========
I took a shot at writing a blockify that actually works with the linux
client. When a new song starts, this will wait until the song is over,
and if after that a new song hasn't start, it uses pacmd to mute the
volume until it has.


The code is tiny, check it out yourself if you feel like it.


TODO:
-----
So, this gets all messed up if you try to seek forward or back in the
song you're listening to, and that song then leads into an ad. I'm not
sure there's much I can do about it, but I'm keeping an eye on it.

Also, it crashes when you quit Spotify or reach the end of your
playlist. I'm totally overhauling this later, it's totally rudimentary
right now.