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
        self.block = gtk.ToggleButton("Block")
        self.block.set_size_request(80, 35)
        self.block.connect("clicked", self.on_block)

        # Open/Close Blocklist button.
        openlist = gtk.ToggleButton("Open List")
        openlist.set_size_request(10, 10)
        openlist.connect("clicked", self.on_openlist)

        # Disable/Enable mute checkbutton.
        checkmute = gtk.CheckButton("Disable mute.")
#         checkmute.set_active(True)
        checkmute.unset_flags(gtk.CAN_FOCUS)
        checkmute.connect("clicked", self.on_checkmute)

        # Layout.
        vbox = gtk.VBox(False, 2)
        vbox.add(self.block)
        vbox.add(openlist)
        vbox.add(checkmute)

        self.add(vbox)

        # Trap the exit.
        self.connect("destroy", self.shutdown)


    def update(self):
        found = self.b.update()
        self.songartist = self.spotify.get_song_artist()
        self.songtitle = self.spotify.get_song_title()
        if found and not self.block.get_active():
            self.block.set_active(True)
        elif not found and self.block.get_active():
            self.block.set_active(False)

        return True


    def start(self):
        "Start blockify."
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
        else:
           self.set_title("Blockify")


    def on_block(self, widget):
        if widget.get_active():
            widget.set_label("Unblock")
            self.b.block_current()
        else:
            widget.set_label("Block")
            self.b.unblock_current()


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
