import os

import gtk

# import blockify


class Notepad(gtk.Window):

    def __init__(self):
        super(Notepad, self).__init__()
        self.set_default_size(300, 200)
        self.set_title("Blocklist")
        self.set_wmclass("blocklist", "Blocklist")
        self.show()


class BlockifyUI(gtk.Window):

    def __init__(self):
        super(BlockifyUI, self).__init__()

        self.set_title("Blockify")
        self.set_wmclass("blockify", "Blockify")
        self.set_default_size(300, 200)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_icon_from_file("data/sound.png")

        block = gtk.ToggleButton("Block")
        block.set_size_request(80, 35)
        block.connect("clicked", self.on_block)

        openlist = gtk.ToggleButton("Open List")
        openlist.set_size_request(10, 10)
        openlist.connect("clicked", self.on_openlist)

        checkmute = gtk.CheckButton("Disable mute.")
#         checkmute.set_active(True)
        checkmute.unset_flags(gtk.CAN_FOCUS)
        checkmute.connect("clicked", self.on_checkmute)

        vbox = gtk.VBox(False, 2)
        vbox.add(block)
        vbox.add(openlist)
        vbox.add(checkmute)

        self.add(vbox)
        self.show_all()

        self.connect("destroy", gtk.main_quit)

        self.show_all()
#         while gtk.events_pending():
#             gtk.main_iteration()
#             blockify.update()

    def on_checkmute(self, widget):
        if widget.get_active():
            self.set_title("Blockify (inactive)")
        else:
           self.set_title("Blockify")

    def on_block(self, widget):
        if widget.get_active():
            widget.set_label("Unblock")
        else:
            widget.set_label("Block")

    def on_openlist(self, widget):
        if widget.get_active():
            widget.set_label("Close Blocklist")
            self.n = Notepad()
        else:
            widget.set_label("Open Blocklist")
            self.n.destroy()

BlockifyUI()
gtk.main()
