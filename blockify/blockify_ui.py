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

class BasicTreeViewExample(object):

    # close the window and quit
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def __init__(self):
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        self.window.set_title("Basic TreeView Example")

        self.window.set_size_request(200, 200)

        self.window.connect("delete_event", self.delete_event)

        # create a TreeStore with one string column to use as the model
        self.treestore = gtk.TreeStore(str)

        # we'll add some data now - 4 rows with 3 child rows each
        for parent in range(4):
            piter = self.treestore.append(None, ['parent %i' % parent])
            for child in range(3):
                self.treestore.append(piter, ['child %i of parent %i' %
                                              (child, parent)])

        # create the TreeView using treestore
        self.treeview = gtk.TreeView(self.treestore)

        # create the TreeViewColumn to display the data
        self.tvcolumn = gtk.TreeViewColumn('Column 0')

        # add tvcolumn to treeview
        self.treeview.append_column(self.tvcolumn)

        # create a CellRendererText to render the data
        self.cell = gtk.CellRendererText()

        # add the cell to the tvcolumn and allow it to expand
        self.tvcolumn.pack_start(self.cell, True)

        # set the cell "text" attribute to column 0 - retrieve text
        # from that column in treestore
        self.tvcolumn.add_attribute(self.cell, 'text', 0)

        # make it searchable
        self.treeview.set_search_column(0)

        # Allow sorting on the column
        self.tvcolumn.set_sort_column_id(0)

        # Allow drag and drop reordering of rows
        self.treeview.set_reorderable(True)

        self.window.add(self.treeview)

        self.window.show_all()


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
            self.n = BasicTreeViewExample()
        else:
            widget.set_label("Open Blocklist")
            self.n.destroy()

BlockifyUI()
gtk.main()
