#!/usr/bin/env python2
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

        # Window setup.
        self.set_title("Blockify")
        self.set_wmclass("blockify", "Blockify")
        self.set_default_size(300, 200)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_icon_from_file("data/sound.png")

        # Block/Unblock button.
        self.toggleblock = gtk.ToggleButton("Block")
        self.toggleblock.connect("clicked", self.on_toggleblock)

        # Mute/Unmute button.
        self.togglemute = gtk.ToggleButton("Mute")
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
        self.checkmute = gtk.CheckButton("Disable mute.")
        self.checkmute.unset_flags(gtk.CAN_FOCUS)
        self.checkmute.connect("clicked", self.on_checkmute)

        # Layout.
        vbox = gtk.VBox(False, 2)
        vbox.add(self.openlist)
        vbox.add(self.toggleblock)
        vbox.add(self.toggleplay)
        vbox.add(self.togglemute)
        vbox.add(self.nextsong)
        vbox.add(self.prevsong)
        vbox.add(self.checkmute)

        self.add(vbox)

        # Trap the exit.
        self.connect("destroy", self.shutdown)


    def update(self):
        # Call the main update function of blockify.
        found = self.b.update()

        # Grab some useful information from DBus.
        self.songstatus = self.spotify.get_song_status()
        self.songartist = self.spotify.get_song_artist()
        self.songtitle = self.spotify.get_song_title()

        # Correct the state of the Block/Unblock toggle button.
        if found and not self.toggleblock.get_active():
            self.toggleblock.set_active(True)
        elif not found and self.toggleblock.get_active():
            self.toggleblock.set_active(False)

        # Correct the state of the Play/Pause toggle button.
        if self.songstatus == "Playing":
            pass

        # The glib.timeout loop will only break if we return False here.
        return True


    def start(self):
        "Start blockify and the main update routine."
        self.spotify = spotifydbus.SpotifyDBus()
        blocklist = blockify.Blocklist()
        self.b = blockify.Blockify(blocklist)
        self.b.bind_signals()
        self.b.toggle_mute()
        glib.timeout_add_seconds(1, self.update)


    def shutdown(self):
        "Cleanly shut down, unmuting sound and saving the blocklist."
        self.b.shutdown()
        gtk.main_quit()


    def on_checkmute(self, widget):
        if widget.get_active():
            self.set_title("Blockify (inactive)")
            self.b.automute = False
            self.b.toggle_mute()

        else:
           self.set_title("Blockify")
           self.b.automute = True


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
            widget.set_label("Close Blocklist")
#             self.n = BasicTreeViewExample()
        else:
            widget.set_label("Open Blocklist")
#             self.n.destroy()


def main():
    blockify.init_logger(loglevel=2)
    ui = BlockifyUI()
    ui.show_all()
    ui.start()
    gtk.main()


if __name__ == "__main__":
    main()
