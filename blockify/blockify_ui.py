import gtk

import blockify

class BlockifyUI(gtk.Window):

    def __init__(self):
        super(BlockifyUI, self).__init__()

        self.set_title("blockify")
        self.set_wmclass("blockify", "Blockify")
        self.set_size_request(300, 200)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_icon_from_file("data/sound.png")

        btn1 = gtk.Button("Button")
        btn1.set_sensitive(False)
        btn2 = gtk.Button("Button")
        btn3 = gtk.Button(stock=gtk.STOCK_CLOSE)
        btn4 = gtk.Button("Button")
        btn4.set_size_request(80, 40)

        fixed = gtk.Fixed()

        fixed.put(btn1, 20, 30)
        fixed.put(btn2, 100, 30)
        fixed.put(btn3, 20, 80)
        fixed.put(btn4, 100, 80)

        self.connect("destroy", gtk.main_quit)

        self.add(fixed)
        self.show_all()


BlockifyUI()
gtk.main()
# blockify.main()
