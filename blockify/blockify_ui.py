#!/usr/bin/env python2
# coding: utf-8
# TODO: minimize to system-try
# TODO: different modes: minimal, full
import logging
import os

import glib
import gtk

import blockify
import spotifydbus


log = logging.getLogger("gui")


class BlockifyUI(gtk.Window):

    def __init__(self):
        super(BlockifyUI, self).__init__()
        basedir = os.path.dirname(os.path.realpath(__file__))
        self.muteofficon = os.path.join(basedir, "data/not_muted.png")
        self.muteonicon = os.path.join(basedir, "data/muted.png")

        # Window setup.
        self.set_title("Blockify")
        self.set_wmclass("blockify", "Blockify")
        self.set_default_size(220, 240)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_icon_from_file(self.muteofficon)

        self.artistlabel = gtk.Label()
        self.titlelabel = gtk.Label()
        self.statuslabel = gtk.Label()
        # Block/Unblock button.
        self.toggleblock = gtk.ToggleButton("Block")
        self.toggleblock.connect("clicked", self.on_toggleblock)

        # Mute/Unmute button.
        self.togglemute = gtk.ToggleButton("Manual Mute")
        self.togglemute.connect("clicked", self.on_togglemute)

        # Play/Pause button.
        self.toggleplay = gtk.ToggleButton("Pause")
        self.toggleplay.connect("clicked", self.on_toggleplay)

        # Open/Close Blocklist button.
        self.openlist = gtk.ToggleButton("Open List")
        self.openlist.connect("clicked", self.on_openlist)

        self.nextsong = gtk.Button("Next")
        self.nextsong.connect("clicked", self.on_nextsong)

        self.prevsong = gtk.Button("Previous")
        self.prevsong.connect("clicked", self.on_prevsong)

        # Disable/Enable mute checkbutton.
        self.toggleautomute = gtk.ToggleButton("Disable AutoMute")
        self.toggleautomute.unset_flags(gtk.CAN_FOCUS)
        self.toggleautomute.connect("clicked", self.on_toggleautomute)

        # Layout.
        vbox = gtk.VBox()
        vbox.add(self.artistlabel)
        vbox.add(self.titlelabel)
        vbox.add(self.statuslabel)
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        vbox.add(self.toggleplay)
        hbox.add(self.prevsong)
        hbox.add(self.nextsong)
        vbox.add(self.togglemute)
        vbox.add(self.toggleblock)
        vbox.add(self.toggleautomute)
        vbox.add(self.openlist)
#         alignment = gtk.Alignment()
#         alignment.set(0.5, 0, 0, 0)
        self.add(vbox)

        # Trap the exit.
        self.connect("destroy", self.shutdown)


    def format_current_song(self):
        song = self.b.current_song

        try:
            artist, title = song.split("–")
        except (ValueError, IndexError):
            artist, title = song, ""

        return artist, title

    def update(self):
        # Call the main update function of blockify.
        found = self.b.update()

        # Grab some useful information from DBus.
        self.songstatus = self.spotify.get_song_status()

        artist, title = self.format_current_song()

        self.artistlabel.set_text(artist)
        self.titlelabel.set_text(title)
        # Set state label:
        self.statuslabel.set_text(self.get_status_text())

        # Correct the state of the Block/Unblock toggle button.
        if found and not self.toggleblock.get_active():
            self.toggleblock.set_active(False)
        elif not found and self.toggleblock.get_active():
            self.toggleblock.set_active(True)

        # Correct the state of the Play/Pause toggle button.
#         if self.songstatus == "Playing" and not self.toggleplay.get_active():
#             self.toggleplay.set_active(True)
#         elif self.songstatus != "Playing" and self.toggleplay.get_active():
#             self.toggleplay.set_active(False)

#         if self.b.muted and not self.togglemute.get_active():
#             self.togglemute.set_active(True)
#         elif not self.b.muted and self.togglemute.get_active():
#             self.togglemute.set_active(False)


        # The glib.timeout loop will only break if we return False here.
        return True

    def get_status_text(self):
        length = self.spotify.get_song_length()
        m, s = divmod(self.spotify.get_song_length(), 60)
        rating = self.spotify.get_property("Metadata")["xesam:autoRating"]
        return "{}m{}s, {} ({})".format(m, s, rating, self.songstatus)


    def start(self):
        "Start blockify and the main update routine."
        blocklist = blockify.Blocklist()
        self.spotify = spotifydbus.SpotifyDBus()
        self.b = blockify.Blockify(blocklist)
        self.b.bind_signals()
        self.b.toggle_mute()
        glib.timeout_add_seconds(1, self.update)


    def shutdown(self, arg):
        "Cleanly shut down, unmuting sound and saving the blocklist."
        self.b.shutdown()
        gtk.main_quit()


    def on_toggleautomute(self, widget):
        if widget.get_active():
            self.set_title("Blockify (inactive)")
            self.b.automute = False
            widget.set_label("Enable AutoMute")
            self.b.toggle_mute()
        else:
            self.set_title("Blockify")
            self.b.automute = True
            widget.set_label("Disable AutoMute")


    def on_toggleblock(self, widget):
        if self.b.automute:
            if widget.get_active():
                widget.set_label("Unblock")
                self.b.block_current()
            else:
                widget.set_label("Block")
                self.b.unblock_current()


    def on_togglemute(self, widget):
        if widget.get_active():
            widget.set_label("Unmute")
            self.b.automute = False
            self.b.toggle_mute(True)
        else:
            widget.set_label("Mute")
            self.b.automute = True
            self.b.toggle_mute(False)


    def on_toggleplay(self, widget):
        if self.songstatus == "Playing":
            widget.set_label("Play")
        else:
            widget.set_label("Pause")
        self.spotify.playpause()


    def on_nextsong(self, widget):
        self.spotify.next()


    def on_prevsong(self, widget):
        self.spotify.prev()


    def on_openlist(self, widget):
        if widget.get_active():
            widget.set_label("Close List")
#             self.n = BasicTreeViewExample()
        else:
            widget.set_label("Open List")
#             self.n.destroy()


def main():
    blockify.init_logger(loglevel=2)
    ui = BlockifyUI()
    ui.show_all()
    ui.start()
    gtk.main()


if __name__ == "__main__":
    main()
