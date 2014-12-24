#!/usr/bin/env python2
"""blockify-ui

Usage:
    blockify-ui [-l <path>] [-v...] [-q] [-h]

Options:
    -l, --log=<path>  Enables logging to the logfile/-path specified.
    -q, --quiet       Don't print anything to stdout.
    -v                Verbosity of the logging module, up to -vvv.
    -h, --help        Show this help text.
    --version         Show current version of blockify.
"""
# TODO: Fix detection delay as outlined by JP-Ellis.
# TODO: Try experimental mode suggested by spam0cal to skip the last
#       second of each song to skip ads altogether (could not verify this).
# TODO: Continuous detect_ad of tray icon tooltip.
# TODO: Different GUI-modes (minimal, full)?
# TODO: Try xlib for minimized window detection. Probably won't help.
# TODO: Notepad: Use ListStore instead of TextView?
# TODO: Notepad: Undo/Redo Ctrl+Z, Ctrl+Y, Fix Ctrl+D to completely delete line.
# TODO: Add detect_ad interval option to docopt.
import codecs
import datetime
import logging
import os
import signal
import threading
import urllib

import blockify
import gtk

import util


log = logging.getLogger("gui")


class Notepad(gtk.Window):
    "A tiny text editor to modify the blocklist."
    def __init__(self):

        super(Notepad, self).__init__()

        self.location = util.BLOCKLIST_FILE

        self.set_title("Blocklist")
        self.set_wmclass("blocklist", "Blockify")
        self.set_default_size(300, 400)
        self.set_position(gtk.WIN_POS_CENTER)

        self.textview = gtk.TextView()
        self.statusbar = gtk.Statusbar()
        self.statusbar.push(0, "Ctrl+S (save), Ctrl+Q (close), Ctrl+D (del-line)")

        self.create_keybinds()
        self.create_layout()

        self.open_file()
        self.show_all()

    def create_layout(self):
        vbox = gtk.VBox()
        textbox = gtk.VBox()
        statusbox = gtk.VBox()
        vbox.pack_start(textbox, True, True, 0)
        vbox.pack_start(statusbox, False, False, 0)

        # Put the textview into a ScrolledWindow.
        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.add(self.textview)
        textbox.pack_start(self.sw)
        statusbox.pack_start(self.statusbar, True, False, 0)

        self.add(vbox)

    def split_accelerator(self, accelerator):
        key, mod = gtk.accelerator_parse(accelerator)
        return key, mod

    def create_keybinds(self):
        "Register Ctrl+Q/W to quit and Ctrl+S to save the blocklist."
        q_key, q_mod = self.split_accelerator("<Control>q")
        w_key, w_mod = self.split_accelerator("<Control>w")
        s_key, s_mod = self.split_accelerator("<Control>s")
        d_key, d_mod = self.split_accelerator("<Control>d")
        a_key, a_mod = self.split_accelerator("<Control>a")

        quit_group = gtk.AccelGroup()
        quit_group.connect_group(q_key, q_mod, gtk.ACCEL_LOCKED, self.destroy)
        quit_group.connect_group(w_key, w_mod, gtk.ACCEL_LOCKED, self.destroy)
        self.add_accel_group(quit_group)

        save_group = gtk.AccelGroup()
        save_group.connect_group(s_key, s_mod, gtk.ACCEL_LOCKED, self.save)
        self.add_accel_group(save_group)

        edit_group = gtk.AccelGroup()
        edit_group.connect_group(d_key, d_mod, gtk.ACCEL_LOCKED, self.delete_line)
        edit_group.connect_group(a_key, a_mod, gtk.ACCEL_LOCKED, self.select_all)
        self.add_accel_group(edit_group)

    def undo(self, *args):
        "Ctrl+Z, undo the last text change."
        pass

    def redo(self, *args):
        "Ctrl+Y, redo the last text change."
        pass

    def delete_line(self, *args):
        "Ctrl+D, delete the current line."
        textbuffer = self.textview.get_buffer()
        mark_at_cursor = textbuffer.get_insert()
        iter_at_cursor = textbuffer.get_iter_at_mark(mark_at_cursor)

        line_number = iter_at_cursor.get_line()
        line_start = textbuffer.get_iter_at_line_offset(line_number, 0)
        bytes_in_line = line_start.get_bytes_in_line()
        end_offset = bytes_in_line - 1 if bytes_in_line > 0 else bytes_in_line
        line_end = textbuffer.get_iter_at_line_index(line_number, end_offset)
        textbuffer.delete(line_start, line_end)

    def select_all(self, *args):
        "Ctrl+A, select all text in the buffer."
        textbuffer = self.textview.get_buffer()
        first, last = textbuffer.get_bounds()
        textbuffer.select_range(first, last)

    def destroy(self, *args):
        "Overloading destroy to untoggle the Open List button."
        super(Notepad, self).destroy()

    def open_file(self, *args):
        textbuffer = self.textview.get_buffer()
        try:
            with codecs.open(self.location, "r", encoding="utf-8") as f:
                textbuffer.set_text(f.read())
        except IOError as e:
            log.error("Notepad: Could not read blocklist. Creating new one. Msg: {}".format(e))
            with codecs.open(self.location, "w", encoding="utf-8"):
                textbuffer.set_text("")
        self.set_title(self.location)

    def save(self, *args):
        textbuffer = self.textview.get_buffer()
        start, end = textbuffer.get_start_iter(), textbuffer.get_end_iter()
        text = textbuffer.get_text(start, end)
        # Append a newline to the blocklist, if necessary.
        if not text.endswith("\n"):
            text += "\n"
        with codecs.open(self.location, "w", encoding="utf-8") as f:
            f.write(text)
        now = str(datetime.datetime.now())
        self.statusbar.push(0, "{}: Saved to {}.".format(now, self.location))


class BlockifyUI(gtk.Window):
    "PyQT4 interface for blockify."
    def __init__(self, blockify):
        super(BlockifyUI, self).__init__()

        # Initialize blockify.
        self.b = blockify

        # Images used for interlude media buttons.
        self.play_img = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
        self.pause_img = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
        self.next_img = gtk.image_new_from_stock(gtk.STOCK_MEDIA_NEXT, gtk.ICON_SIZE_BUTTON)
        self.prev_img = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PREVIOUS, gtk.ICON_SIZE_BUTTON)
        self.open_img = gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
        self.shuffle_img = gtk.image_new_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)

        self.thumbnail_dir = util.THUMBNAIL_DIR
        self.cover_server = "https://i.scdn.co/image/"
        self.use_cover_art = self.b.options["gui"]["use_cover_art"]
        self.autohide_cover = self.b.options["gui"]["autohide_cover"]
        self.previous_cover_file = ""

        self.editor = None
        self.statusicon_found = False

        # Set the GUI/Blockify detect_ad interval to 400ms. Increase this to
        # reduce CPU usage and decrease it to improve responsiveness.
        # If you need absolutely minimal CPU usage you could, in self.start(),
        # change the line to glib.timeout_add_seconds(2, self.update) or more.
        self.update_interval = self.b.options["gui"]["update_interval"]

        # Update interval for interlude music slider.
        self.slider_update_interval = 100

        # Window setup.
        self.set_title("Blockify")
        self.set_wmclass("blockify", "Blockify")
        self.set_default_size(195, 188)
        self.coverimage = gtk.Image()
        self.create_labels()
        self.create_buttons()
        self.create_interlude_player()
        self.create_layout()
        self.create_tray()

        # "Trap" the exit.
        self.connect("destroy", self.stop)

        self.show_all()
        self.set_states()
        log.info("Blockify-UI initialized.")
        self.start()

    def create_tray(self):
        basedir = os.path.dirname(os.path.realpath(__file__))

        self.blue_icon_file = os.path.join(basedir, "data/icon-blue-32.png")
        self.red_icon_file = os.path.join(basedir, "data/icon-red-32.png")
        pixbuf_blue = gtk.gdk.pixbuf_new_from_file(self.blue_icon_file)  # @UndefinedVariable
        pixbuf_red = gtk.gdk.pixbuf_new_from_file(self.red_icon_file)  # @UndefinedVariable
        self.blue_icon_buf = pixbuf_blue.scale_simple(16, 16, gtk.gdk.INTERP_BILINEAR)  # @UndefinedVariable
        self.red_icon_buf = pixbuf_red.scale_simple(16, 16, gtk.gdk.INTERP_BILINEAR)  # @UndefinedVariable

        self.set_icon_from_file(self.blue_icon_file)
        self.status_icon = gtk.StatusIcon()
        self.status_icon.set_from_pixbuf(self.blue_icon_buf)

        self.status_icon.connect("popup-menu", self.on_tray_right_click)
        self.status_icon.connect("activate", self.on_tray_left_click)
        self.status_icon.set_tooltip("blockify v{0}".format(blockify.VERSION))
        self.connect("delete-event", self.on_delete_event)

    def create_traymenu(self, event_button, event_time):
        menu = gtk.Menu()

        toggleblock = gtk.MenuItem("Toggle Block")
        toggleblock.show()
        menu.append(toggleblock)
        toggleblock.connect("activate", self.on_toggleblock)

        toggleplay = gtk.MenuItem("Toggle Play")
        toggleplay.show()
        toggleplay.connect("activate", self.on_toggleplay)
        menu.append(toggleplay)

        prevsong = gtk.MenuItem("Previous Song")
        prevsong.show()
        prevsong.connect("activate", self.on_prevsong)
        menu.append(prevsong)

        nextsong = gtk.MenuItem("Next Song")
        nextsong.show()
        nextsong.connect("activate", self.on_nextsong)
        menu.append(nextsong)

        about = gtk.MenuItem("About")
        about.show()
        menu.append(about)
        about.connect("activate", self.show_about_dialogue)

        exit = gtk.MenuItem("Exit")
        exit.show()
        menu.append(exit)
        exit.connect("activate", self.on_exit_btn)

        menu.popup(None, None, gtk.status_icon_position_menu,
                   event_button, event_time, self.status_icon)

    def create_labels(self):
        self.albumlabel = gtk.Label()
        self.artistlabel = gtk.Label()
        self.titlelabel = gtk.Label()
        self.statuslabel = gtk.Label()

        for label in [self.albumlabel, self.artistlabel, self.titlelabel]:
            # label.set_line_wrap(True)
            label.set_width_chars(26)

    def create_interlude_player(self):
        interludelabel = "Disable" if self.b.use_interlude_music else "Enable"
        self.toggle_interlude_btn = gtk.Button(interludelabel + " Player")
        self.toggle_interlude_btn.connect("clicked", self.on_toggleinterlude_btn)
        self.prev_btn = gtk.Button()
        self.prev_btn.set_image(self.prev_img)
        self.prev_btn.connect("clicked", self.on_prev_btn)
        self.play_btn = gtk.Button()
        self.play_btn.set_image(self.play_img)
        self.play_btn.connect("clicked", self.on_play_btn)
        self.next_btn = gtk.Button()
        self.next_btn.set_image(self.next_img)
        self.next_btn.connect("clicked", self.on_next_btn)
        self.open_btn = gtk.Button()
        self.open_btn.set_image(self.open_img)
        self.open_btn.set_tooltip_text("Load playlist")
        self.open_btn.connect("clicked", self.on_open_btn)
        self.shuffle_btn = gtk.Button()
        self.shuffle_btn.set_image(self.shuffle_img)
        self.shuffle_btn.set_tooltip_text("Shuffle")
        self.shuffle_btn.connect("clicked", self.on_shuffle_btn)

        self.interlude_label = gtk.Label()
        self.interlude_label.set_width_chars(26)

        self.autoresume_chk = gtk.CheckButton("Autoresume")
        self.autoresume_chk.connect("clicked", self.on_autoresume)

        self.slider = gtk.HScale()
        self.slider.set_sensitive(False)
        self.slider.set_range(0, 100)
        self.slider.set_increments(1, 10)
        self.slider.connect("value-changed", self.on_slider_change)

        self.b.player.bus.connect("message::tag", self.on_interlude_tag_changed)
        self.b.player.player.connect("audio-changed", self.on_interlude_audio_changed)

    def create_buttons(self):
        self.toggleplay_btn = gtk.Button("Play/Pause")
        self.toggleplay_btn.connect("clicked", self.on_toggleplay)
        self.prevsong_btn = gtk.Button("Previous")
        self.prevsong_btn.connect("clicked", self.on_prevsong)
        self.nextsong_btn = gtk.Button("Next")
        self.nextsong_btn.connect("clicked", self.on_nextsong)

        self.toggleblock_btn = gtk.Button("Block")
        self.toggleblock_btn.connect("clicked", self.on_toggleblock)
        self.autodetect_chk = gtk.CheckButton("Autodetect")
        self.autodetect_chk.connect("clicked", self.on_autodetect)

        self.togglemute_btn = gtk.ToggleButton("Mute")
        self.togglemute_btn.connect("clicked", self.on_togglemute)
        self.automute_chk = gtk.CheckButton("Automute")
        self.automute_chk.connect("clicked", self.on_automute)

        self.togglecover_btn = gtk.Button("Toggle Cover")
        self.togglecover_btn.connect("clicked", self.on_togglecover)
        self.autohidecover_chk = gtk.CheckButton("Autohide")
        self.autohidecover_chk.connect("clicked", self.on_autohidecover)

        self.togglelist_btn = gtk.ToggleButton("Open List")
        self.togglelist_btn.connect("clicked", self.on_togglelist)

        self.exit_btn = gtk.Button("Exit")
        self.exit_btn.connect("clicked", self.on_exit_btn)

        self.togglemute_btn.set_sensitive(False)

    def create_layout(self):
        main = gtk.VBox()

        main.add(self.coverimage)
        main.add(self.artistlabel)
        main.add(self.titlelabel)
        main.add(self.albumlabel)
        main.add(self.statuslabel)
        main.add(self.toggleplay_btn)

        controlbuttons = gtk.HBox(True)
        controlbuttons.add(self.prevsong_btn)
        controlbuttons.add(self.nextsong_btn)
        main.pack_start(controlbuttons)

        blockbuttons = gtk.HBox(True)
        blockbuttons.add(self.toggleblock_btn)
        blockbuttons.add(self.autodetect_chk)
        main.pack_start(blockbuttons)

        mutebuttons = gtk.HBox(True)
        mutebuttons.add(self.togglemute_btn)
        mutebuttons.add(self.automute_chk)
        main.pack_start(mutebuttons)

        coverbuttons = gtk.HBox(True)
        coverbuttons.add(self.togglecover_btn)
        coverbuttons.add(self.autohidecover_chk)
        main.pack_start(coverbuttons)

        main.add(self.togglelist_btn)
        main.add(self.exit_btn)
        main.add(self.toggle_interlude_btn)

        interludebuttons = gtk.HBox(False)
        interludebuttons.add(self.prev_btn)
        interludebuttons.add(self.play_btn)
        interludebuttons.add(self.next_btn)
        interludebuttons.add(self.open_btn)
        interludebuttons.add(self.shuffle_btn)
        interludebuttons.add(self.autoresume_chk)
        self.interlude_box = gtk.VBox()
        self.interlude_box.add(self.interlude_label)
        self.interlude_box.add(self.slider)
        self.interlude_box.add(interludebuttons)
        main.add(self.interlude_box)

        self.add(main)

    def set_states(self):
        # Simulate finding a commercial to keep autoresume_chk from bugging out.
        self.b.found = True

        checkboxes = [self.autodetect_chk, self.automute_chk, self.autoresume_chk, self.autohidecover_chk]
        values = [self.b.options["general"]["autodetect"], self.b.options["general"]["automute"],
               self.b.options["interlude"]["autoresume"], self.b.options["gui"]["autohide_cover"]]

        for i in range(len(checkboxes)):
            checkboxes[i].set_active(values[i])

        if not self.b.use_interlude_music:
            self.interlude_box.hide()

    def start(self):
        "Start the main detect_ad routine."
        self.b.toggle_mute()
        self.bind_signals()

        gtk.threads_init()
        # Start and loop the main detect_ad routine once every X ms.
        # To influence responsiveness or CPU usage, decrease/increase ms here.
        gtk.timeout_add(self.update_interval, self.update)
        log.info("Blockify-UI started.")
        gtk.main()

    def stop(self, *args):
        "Cleanly shut down, unmuting sound and saving the blocklist."
        self.b.stop()
        log.debug("Exiting GUI.")
        gtk.main_quit()

    def bind_signals(self):
        "Binds SIGTERM, SIGINT and SIGUSR1 to custom actions."
        signal.signal(signal.SIGUSR1, lambda sig, hdl: self.b.block_current())
        signal.signal(signal.SIGUSR2, lambda sig, hdl: self.b.unblock_current())
        signal.signal(signal.SIGTERM, lambda sig, hdl: self.stop())
        signal.signal(signal.SIGINT, lambda sig, hdl: self.stop())

    def show_about_dialogue(self, widget):
        about = gtk.AboutDialog()
        about.set_destroy_with_parent (True)
        about.set_icon_name ("blockify")
        about.set_name("blockify")
        about.set_version(blockify.VERSION)
        about.set_website("http://github.com/mikar/blockify")
        about.set_copyright("(c) 2014 Max Demian")
        about.set_license("The MIT License (MIT)")
        about.set_comments(("Blocks Spotify commercials"))
        about.set_authors(["Max Demian <mikar@gmx.de>", "Jesse Maes <kebertyx@gmail.com>"])
        about.run()
        about.destroy()

    def update(self):
        "Main GUI loop at specific time interval (see self.update_interval)."
        # Call the main detect_ad function of blockify and assign return value
        # (True/False) depending on whether a song to be blocked was found.
        self.b.found = self.b.detect_ad()
        if self.b.use_interlude_music:
            threading.Thread(target=self.b.player.toggle_interlude_music).start()

        # Our main GUI workers here, updating labels, buttons and the likes.
        self.update_cover()
        self.update_labels()
        self.update_buttons()
        self.update_icons()

        # The glib.timeout loop will only break if we return False here.
        return True

    def update_cover(self):
        if not self.use_cover_art:
            return
        if self.b.is_sink_muted or self.b.is_fully_muted:
            if self.autohide_cover and self.b.automute:
                self.disable_cover()
        else:
            try:
                cover_file = self.get_cover_art()
                if cover_file and self.previous_cover_file != cover_file:
                    pixbuf = gtk.gdk.pixbuf_new_from_file(cover_file)  # @UndefinedVariable
                    scaled_buf = pixbuf.scale_simple(195, 195, gtk.gdk.INTERP_BILINEAR)  # @UndefinedVariable
                    self.coverimage.set_from_pixbuf(scaled_buf)
                    self.previous_cover_file = cover_file
                if self.autohide_cover:
                    self.enable_cover()
            except Exception as e:
                log.error("Failed to load cover art: {}. Disabling.".format(e))
                self.use_cover_art = False
                self.autohidecover_chk.set_active(False)
                self.disable_cover()

    def update_labels(self):
        status = self.get_status_text()
        self.statuslabel.set_text(status)
        if not self.b.found:
            self.albumlabel.set_text(self.b.dbus.get_song_album())
        else:
            self.albumlabel.set_text("(blocked)")

        artist, title = self.format_current_song()
        self.artistlabel.set_text(artist)
        self.titlelabel.set_text(title)
        # self.status_icon.set_tooltip("{0} - {1}\n{2}\nblockify v{3}".format(artist, title, status, blockify.VERSION))

    def update_buttons(self):
        # Correct the state of the Block/Unblock toggle button.
        if self.b.found:
            self.toggleblock_btn.set_label("Unblock")
            self.set_title("Blockify (blocked)")
        else:
            self.toggleblock_btn.set_label("Block")
            self.set_title("Blockify")

        if self.b.song_status == "Playing" and self.b.current_song:
            self.toggleplay_btn.set_label("Pause")
        else:
            self.toggleplay_btn.set_label("Play")

        if self.coverimage.get_visible():
            self.togglecover_btn.set_label("Hide Cover")
        else:
            self.togglecover_btn.set_label("Show Cover")

        # Correct state of Open/Close List toggle button.
        if self.editor:
            if not self.editor.get_visible() and self.togglelist_btn.get_active():
                self.togglelist_btn.set_active(False)
        if self.togglelist_btn.get_active():
            self.togglelist_btn.set_label("Close List")
        else:
            self.togglelist_btn.set_label("Open List")

        if self.b.use_interlude_music:
            if self.b.player.is_playing():
                self.play_btn.set_image(self.pause_img)
            else:
                self.play_btn.set_image(self.play_img)

    def update_icons(self):
        if self.b.found and not self.statusicon_found:
            self.set_icon_from_file(self.red_icon_file)
            self.status_icon.set_from_pixbuf(self.red_icon_buf)
            self.statusicon_found = True
        elif not self.b.found and self.statusicon_found:
            self.set_icon_from_file(self.blue_icon_file)
            self.status_icon.set_from_pixbuf(self.blue_icon_buf)
            self.statusicon_found = False

    def update_slider(self):
        is_sensitive = self.slider.get_sensitive()
        is_playing = self.b.player.is_playing()
        if is_playing and not is_sensitive:
            self.slider.set_sensitive(True)
        elif not is_playing and is_sensitive:
            self.slider.set_sensitive(False)

        if self.b.player.is_radio():
            self.slider.set_sensitive(False)
            return False

        try:
            nanosecs, format = self.b.player.player.query_position(self.b.player.gst.FORMAT_TIME)
            duration_nanosecs, format = self.b.player.player.query_duration(self.b.player.gst.FORMAT_TIME)

            # Block seek handler so we don't seek when we set_value().
            self.slider.handler_block_by_func(self.on_slider_change)

            self.slider.set_range(0, float(duration_nanosecs) / self.b.player.gst.SECOND)
            self.slider.set_value(float(nanosecs) / self.b.player.gst.SECOND)

            self.slider.handler_unblock_by_func(self.on_slider_change)
        except Exception as e:
            log.error("Exception while updating slider: {}".format(e))

        # Continue calling every self.slider_update_interval milliseconds.
        return True

    def format_current_song(self):
        song = self.b.current_song
        # For whatever reason, Spotify doesn't use a normal hyphen but a
        # slightly longer one. This is its unicode code point.
        delimiter = u"\u2013"  # \xe2\x80\x93 is the bytestring.

        # We prefer the current_song variable as source for artist, title but
        # should that fail, try getting those from DBus.
        try:
            artist, title = song.split(" {} ".format(delimiter))
        except (ValueError, IndexError):
            artist = self.b.dbus.get_song_artist()
            title = self.b.dbus.get_song_title()

        # Sometimes song.split returns None, catch it here.
        if not artist or not title:
            artist, title = "No song playing?", song

        return artist, title

    def get_cover_art(self):
        cover_file = ""
        cover_hash = os.path.basename(self.b.dbus.get_art_url())

        if cover_hash:
            # The url spotify gets its cover images from. Filename is a hash, the last part of metadata["artUrl"]
            cover_url = self.cover_server + cover_hash
            cover_file = os.path.join(util.THUMBNAIL_DIR, cover_hash + ".png")

            if not os.path.exists(cover_file):
                log.info("Downloading cover art for {0} ({1}).".format(self.b.current_song, cover_hash))
                urllib.urlretrieve(cover_url, cover_file)

        return cover_file

    def get_status_text(self):
        status = ""
        songlength = self.b.dbus.get_song_length()

        if songlength:
            m, s = divmod(songlength, 60)
            r = self.b.dbus.get_property("Metadata")["xesam:autoRating"]
            status = "{}m{}s, {} ({})".format(m, s, r, self.b.song_status)

        return status

    def restore_size(self):
        width, height = self.get_default_size()
        self.resize(width, height)

    def enable_cover(self):
        if not self.coverimage.get_visible():
            self.coverimage.show()

    def disable_cover(self):
        if self.coverimage.get_visible():
            self.coverimage.hide()
            self.restore_size()

    def on_delete_event(self, window, event):
        self.hide_on_delete()
        return True

    def on_tray_left_click(self, status):
        self.show_all()

    def on_tray_right_click(self, icon, event_button, event_time):
        self.create_traymenu(event_button, event_time)

    def on_autoresume(self, widget):
        if widget.get_active():
            self.b.player.autoresume = True
            self.b.player.manual_control = False
            if not self.b.found and self.b.song_status != "Playing":
                self.b.dbus.playpause()
        else:
            self.b.player.autoresume = False

    def on_toggleinterlude_btn(self, widget):
        if self.b.use_interlude_music:
            self.b.use_interlude_music = False
            self.interlude_box.hide()
            self.b.player.pause()
            if self.b.song_status != "Playing":
                self.b.dbus.playpause()
            widget.set_label("Enable player")
        else:
            self.b.use_interlude_music = True
            self.interlude_box.show()
            widget.set_label("Disable player")
        self.restore_size()

    def on_interlude_audio_changed (self, player):
        "Audio source for interlude music has changed."
        log.debug("Interlude track changed to {}.".format(self.b.player.get_current_uri()))
        gtk.timeout_add(self.slider_update_interval, self.update_slider)
        uri = self.b.player.get_current_uri()
        if uri.startswith("file://"):
            uri = os.path.basename(uri)
        self.interlude_label.set_text(uri)

    def on_interlude_tag_changed (self, bus, message):
        "Read and display tag information from AudioPlayer.player.bus."
        taglist = message.parse_tag()

        if "artist" in taglist.keys():
            try:
                label = taglist["artist"] + " - " + taglist["title"]
                if len(label) > 5:
                    self.interlude_label.set_text(label)
            except KeyError as e:
                log.debug("Exception when trying to set interlude label: {}.".format(e))

    def on_play_btn(self, widget):
        "Interlude play button."
        if self.b.use_interlude_music:
            if not self.b.player.is_playing():
                self.b.player.manual_control = False
                self.b.player.play()
            else:
                self.b.player.manual_control = True
                self.b.player.pause()
                if not self.b.found and (self.b.song_status != "Playing" or
                                         not self.b.current_song):
                    self.b.dbus.playpause()

    def on_prev_btn(self, widget):
        "Interlude previous button."
        if self.b.use_interlude_music:
            self.b.player.prev()

    def on_next_btn(self, widget):
        "Interlude next button."
        if self.b.use_interlude_music:
            self.b.player.next()

    def on_shuffle_btn(self, widget):
        "Interlude open playlist button."
        if self.b.use_interlude_music:
            self.b.player.shuffle()

    def on_open_btn(self, widget):
        "Interlude open playlist button."
        if not self.b.use_interlude_music:
            return

        dialog = gtk.FileChooserDialog("Load playlist or audio folder/file",
                                        None,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        dialog.set_current_folder(util.CONFIG_DIR)

        all_filter = gtk.FileFilter()
        all_filter.set_name("All files")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)

        av_filter = gtk.FileFilter()
        av_filter.set_name("Audio and video files")
        for fmt in self.b.player.formats:
            av_filter.add_pattern("*." + fmt)
        dialog.add_filter(av_filter)

        audio_filter = gtk.FileFilter()
        audio_filter.set_name("Audio files")
        for fmt in self.b.player.formats[:6]:
            audio_filter.add_pattern("*." + fmt)
        dialog.add_filter(audio_filter)

        playlist_filter = gtk.FileFilter()
        playlist_filter.set_name("Playlists")
        playlist_filter.add_pattern("*.m3u")
        dialog.add_filter(playlist_filter)

        dialog.set_filter(playlist_filter)
        dialog.set_select_multiple(True)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            file_list = dialog.get_filenames()
            self.b.player.load_playlist(self.b.player.parse_playlist(file_list))

        dialog.destroy()

    def on_slider_change(self, slider):
        "When the slider was moved, detect_ad the song position accordingly."
        seek_time_secs = slider.get_value()
        self.b.player.player.seek_simple(self.b.player.gst.FORMAT_TIME,
                                         self.b.player.gst.SEEK_FLAG_FLUSH |
                                         self.b.player.gst.SEEK_FLAG_KEY_UNIT,
                                         seek_time_secs * self.b.player.gst.SECOND)

    def on_togglecover(self, widget):
        "Button that toggles cover art."
        if self.coverimage.get_visible():
            self.use_cover_art = False
            self.disable_cover()
            log.debug("Disabled cover art.")
        else:
            self.use_cover_art = True
            self.enable_cover()
            log.debug("Enabled cover art.")

    def on_autohidecover(self, widget):
        """CheckButton that determines whether to automatically hide
        cover art when a commercial is playing"""
        if widget.get_active():
            self.autohide_cover = True
            self.togglecover_btn.set_sensitive(False)
            log.debug("Enabled cover autohide.")
        else:
            self.autohide_cover = False
            self.togglecover_btn.set_sensitive(True)
            self.enable_cover()
            log.debug("Disabled cover autohide.")

    def on_toggleblock(self, widget):
        "Button to block/unblock the current song."
        if self.b.found:
            self.b.unblock_current()
            widget.set_label("Block")
        else:
            self.b.block_current()
            widget.set_label("Unblock")
            if self.b.use_interlude_music:
                self.b.player.manual_control = False

    def on_autodetect(self, widget):
        if widget.get_active():
            self.b.autodetect = True
        else:
            self.b.autodetect = False

    def on_togglemute(self, widget):
        if widget.get_active():
            widget.set_label("Unmute")
            self.b.toggle_mute(1)
        else:
            widget.set_label("Mute")
            self.b.toggle_mute(2)

    def on_automute(self, widget):
        if widget.get_active():
            self.togglemute_btn.set_sensitive(False)
            self.toggleblock_btn.set_sensitive(True)
            self.b.automute = True
            log.debug("Enabled automute.")
        else:
            self.b.automute = False
            self.togglemute_btn.set_sensitive(True)
            self.toggleblock_btn.set_sensitive(False)
            self.b.toggle_mute(2)
            log.debug("Disabled automute.")
        # Nasty togglebuttonses. Always need correcting.
        if self.b.is_sink_muted or self.b.is_fully_muted:
            self.togglemute_btn.set_label("Unmute")
            if not self.togglemute_btn.get_active():
                self.togglemute_btn.set_active(True)
        else:
            self.togglemute_btn.set_active(False)
            if self.togglemute_btn.get_active():
                self.togglemute_btn.set_active(False)
            self.togglemute_btn.set_label("Mute")

    def on_togglelist(self, widget):
        if widget.get_active():
            widget.set_label("Close List")
            self.editor = Notepad()
        else:
            if self.editor:
                widget.set_label("Open List")
                self.editor.destroy()

    def on_toggleplay(self, widget):
        self.b.dbus.playpause()

    def on_nextsong(self, widget):
        self.b.dbus.next()

    def on_prevsong(self, widget):
        self.b.dbus.prev()

    def on_exit_btn(self, widget):
        self.stop()


def main():
    "Entry point for the GUI-version of Blockify."
    BlockifyUI(blockify.initialize(__doc__))


if __name__ == "__main__":
    main()
