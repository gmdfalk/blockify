#!/usr/bin/python3
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

class MyStatusIconApp:
    def __init__(self):
        self.status_icon = Gtk.StatusIcon()
        self.status_icon.set_from_stock(Gtk.STOCK_HOME)
        self.status_icon.connect("popup-menu", self.right_click_event)

    def right_click_event(self, icon, button, time):
        self.menu = Gtk.Menu()

        about = Gtk.MenuItem()
        about.set_label("About")
        about.connect("activate", self.show_about_dialog)
        self.menu.append(about)

        quit = Gtk.MenuItem()
        quit.set_label("Quit")
        quit.connect("activate", Gtk.main_quit)
        self.menu.append(quit)

        self.menu.show_all()

        self.menu.popup(None, None, None, self.status_icon, button, time)

    def show_about_dialog(self, widget):
        about_dialog = Gtk.AboutDialog()

        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name("StatusIcon Example")
        about_dialog.set_version("1.0")
        about_dialog.set_authors(["Andrew Steele"])

        about_dialog.run()
        about_dialog.destroy()

app = MyStatusIconApp()
Gtk.main()