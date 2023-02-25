import logging, gi
import random # PAUL

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return ErcfPanel(*args)

class ErcfPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)

        #self.buttons['check_gates'] = self._gtk.Button(label=_("Select"))
#            'check_gates': self._gtk.Button('hashtag', _('Check Gates'), 'color4', scale=self.bts),
        self.buttons = {
            'status': self._gtk.Button('refresh', _('Status'), 'color4'),
            'check_gates': self._gtk.Button('ercf_checkgates', _('Gates'), 'color1'),
            'pause': self._gtk.Button('pause', _('Pause'), 'color1'),
            'unlock': self._gtk.Button('ercf_unlock', _('Unlock'), 'color2'),
            'resume': self._gtk.Button('resume', _('Resume'), 'color3'),
            'manage': self._gtk.Button('ercf_gear', _('Manage...'), 'color4'),
            'increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'tool': self._gtk.Button('extruder', _('T0'), 'color2'),
            'decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'eject': self._gtk.Button('ercf_eject', _('Eject'), 'color1'),
        }
        self.buttons['status'].connect("clicked", self.dummy)
        self.buttons['check_gates'].connect("clicked", self.dummy)
        self.buttons['pause'].connect("clicked", self.dummy, "p") # PAUL what is the "p"
        self.buttons['unlock'].connect("clicked", self.dummy)
        self.buttons['resume'].connect("clicked", self.dummy)
        self.buttons['manage'].connect("clicked", self.dummy)
        self.buttons['increase'].connect("clicked", self.dummy)
        self.buttons['tool'].connect("clicked", self.dummy)
        self.buttons['decrease'].connect("clicked", self.dummy)
        self.buttons['eject'].connect("clicked", self.dummy)

        self.buttons['increase'].set_halign(Gtk.Align.START)
        self.buttons['increase'].set_margin_start(10)
        self.buttons['decrease'].set_halign(Gtk.Align.END)
        self.buttons['decrease'].set_margin_end(10)

        scale = Gtk.Scale.new_with_range(orientation=Gtk.Orientation.VERTICAL, min=-23, max=0, step=1)
        self.scale = scale
        scale.add_mark(-5, Gtk.PositionType.RIGHT, "5")
#        #scale.clear_marks() PAUL will need when changing headroom
        scale.set_inverted(True)
        scale.set_value(-15) # PAUL starting value
        scale.set_value_pos(Gtk.PositionType.BOTTOM)
        scale.set_digits(1)
        scale.set_can_focus(False)
        scale.set_sensitive(False)

        runout_frame = Gtk.Frame()
        runout_frame.set_vexpand(True)
        runout_frame.set_label(f"Runout / Clog")
        runout_frame.set_label_align(.5, 1.0)
        runout_frame.add(scale)

        tb = Gtk.TextBuffer()
        tv = Gtk.TextView()
        tv.set_vexpand(True)
        tv.set_hexpand(False)
        tv.set_buffer(tb)
        tv.set_editable(False)
        tv.set_cursor_visible(False)
        tb.set_text("\nGates: |#0 |#1 |#2 |#3 |#4 |#5 |#6 |#7 |#8 |\nTools: |T0 | . |T1+|T3 |T4 |T5 |T6 |T7 |T8 |\nAvail: | * | * | * | . | . | . | . | . | . |\nSelct: | * |-------------------------------- T0\nERCF [T0] >>> [En] >>>>>>> [Ex] >> [Ts] >> [Nz] LOADED (@0.0 mm)")
        tv.set_sensitive(False)
#        tv.connect("size-allocate", self._autoscroll)
#        tv.connect("focus-in-event", self._screen.remove_keyboard)

        status_window = Gtk.ScrolledWindow()
        status_window.set_vexpand(True)
        status_window.add(tv)

        status_frame = Gtk.Frame()
        status_frame.set_vexpand(True)
#        status_frame.set_hexpand(False)
        status_frame.set_label(f"Status")
        status_frame.set_label_align(.5, 1.0)
        status_frame.add(status_window)

        top_grid = Gtk.Grid()
        top_grid.set_column_homogeneous(True)

        top_grid.attach(status_frame, 0, 0, 3, 2)
        top_grid.attach(runout_frame, 3, 0, 1, 1)
        top_grid.attach(Gtk.Label(" "), 3, 1, 1, 1)

        middle_buttons_grid = Gtk.Grid()
        middle_buttons_grid.set_column_homogeneous(True)

        middle_grid = Gtk.Grid()
        middle_grid.set_column_homogeneous(True)
        middle_grid.attach(self.buttons['decrease'], 0, 0, 1, 1)
        middle_grid.attach(self.buttons['tool'], 1, 0, 1, 1)
        middle_grid.attach(self.buttons['increase'], 2, 0, 1, 1)
        middle_grid.attach(self.buttons['eject'], 3, 0, 1, 1)
        middle_grid.attach(self.buttons['check_gates'], 4, 0, 1, 1)
        middle_grid.attach(self.buttons['status'], 5, 0, 1, 1)
        middle_buttons_grid.set_vexpand(False)

        middle_buttons_grid.attach(middle_grid, 0, 0, 4, 1)
#        middle_buttons_grid.attach(right_middle_grid, 2, 0, 2, 1)

        lower_buttons_grid = Gtk.Grid()
        lower_buttons_grid.set_column_homogeneous(True)
#        lower_buttons_grid.set_hexpand(True)
        lower_buttons_grid.set_vexpand(False)

        lower_buttons_grid.attach(self.buttons['pause'], 0, 0, 1, 1)
        lower_buttons_grid.attach(self.buttons['unlock'], 1, 0, 1, 1)
        lower_buttons_grid.attach(self.buttons['resume'], 2, 0, 1, 1)
        lower_buttons_grid.attach(self.buttons['manage'], 3, 0, 1, 1)

        self.content.add(top_grid)
        self.content.add(middle_buttons_grid)
        self.content.add(Gtk.Label(" "))
        self.content.add(lower_buttons_grid)
#        self.content.set_homogeneous(True)

#        self.labels.update({
#            "tb": tb,
#            "tv": tv
#        })

    def clear(self, widget=None):
        self.labels['tb'].set_text("")

    def dummy(self, widget, param=None):
        r = random.random() * -23
        logging.info("random=%.2f" % r)
        self.scale.set_value(r)

