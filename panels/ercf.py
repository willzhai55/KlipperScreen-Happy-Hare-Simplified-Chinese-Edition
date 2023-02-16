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
        self.buttons = {
            'refresh': self._gtk.Button('refresh', _('Refresh'), 'color4'),
            'check_gates': self._gtk.Button('hashtag', _('Check Gates'), 'color4', scale=self.bts),
            'pause': self._gtk.Button('pause', _('Pause'), 'color4'),
            'unlock': self._gtk.Button('ercf_unlock', _('Unlock'), 'color1'),
            'resume': self._gtk.Button('resume', _('Resume'), 'color3'),
            'manage': self._gtk.Button('ercf_gear', _('Manage...'), 'color3'),
            'increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'tool': self._gtk.Button('extruder', _('T0'), 'color2'),
            'decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'eject': self._gtk.Button('ercf_eject', _('Eject'), 'color4'),
        }
        self.buttons['refresh'].connect("clicked", self.dummy)
        self.buttons['check_gates'].connect("clicked", self.dummy)
        self.buttons['pause'].connect("clicked", self.dummy, "p")
        self.buttons['unlock'].connect("clicked", self.dummy)
        self.buttons['resume'].connect("clicked", self.dummy)
        self.buttons['manage'].connect("clicked", self.dummy)
        self.buttons['increase'].connect("clicked", self.dummy)
        self.buttons['tool'].connect("clicked", self.dummy)
        self.buttons['decrease'].connect("clicked", self.dummy)
        self.buttons['eject'].connect("clicked", self.dummy)

        scale = Gtk.Scale.new_with_range(orientation=Gtk.Orientation.VERTICAL, min=-23, max=0, step=1)
        self.scale = scale
        scale.set_hexpand(True)
        scale.set_vexpand(True)
#        #scale.set_value(self.check_pin_value(pin))
        scale.add_mark(-5, Gtk.PositionType.BOTTOM, "5")
#        #scale.clear_marks()
        scale.set_inverted(True)
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.BOTTOM)

#        scale.set_editable(False)
        scale.set_can_focus(False)
#        scale.set_can_target(False)
        scale.set_value(-15)
        scale.set_digits(0)
#        scale.set_has_origin(True)
#        scale.get_style_context().add_class("fan_slider")

#        scale = Gtk.LevelBar(orientation=Gtk.Orientation.VERTICAL)
#        self.scale = scale
#        scale.set_hexpand(True)
#        scale.set_vexpand(True)
#        scale.set_min_value(0.)
#        scale.set_max_value(20)
#        scale.set_value(10)
#        scale.set_inverted(True)
#        scale.remove_offset_value(Gtk.LEVEL_BAR_OFFSET_LOW)
#        scale.remove_offset_value(Gtk.LEVEL_BAR_OFFSET_HIGH)
#        scale.remove_offset_value(Gtk.LEVEL_BAR_OFFSET_FULL)
#        scale.add_offset_value('headroom', 20)
#        scale.add_offset_value(Gtk.LEVEL_BAR_OFFSET_FULL, 8)

        self.buttons['increase'].set_halign(Gtk.Align.START)
        self.buttons['increase'].set_margin_start(10)
        self.buttons['decrease'].set_halign(Gtk.Align.END)
        self.buttons['decrease'].set_margin_end(10)

        top_grid = Gtk.Grid()
        top_grid.set_column_homogeneous(True)

        status_window = Gtk.ScrolledWindow()
        status_window.set_vexpand(True)
        status_frame = Gtk.Frame()
        status_frame.set_vexpand(True)
        status_frame.set_label(f"Status")
        status_frame.set_label_align(.5,.0)
        tb = Gtk.TextBuffer()
        tv = Gtk.TextView()
        tv.set_vexpand(True)
        tv.set_buffer(tb)
        tv.set_editable(False)
        tv.set_cursor_visible(False)
        tb.set_text("\nGates: |#0 |#1 |#2 |#3 |#4 |#5 |#6 |#7 |#8 |\nTools: |T0 | . |T1+|T3 |T4 |T5 |T6 |T7 |T8 |\nAvail: | * | * | * | . | . | . | . | . | . |\nSelct: | * |-------------------------------- T0\nERCF [T0] >>> [En] >>>>>>> [Ex] >> [Ts] >> [Nz] LOADED (@0.0 mm)")
        tv.connect("size-allocate", self._autoscroll)
#        tv.connect("focus-in-event", self._screen.remove_keyboard)

#        e1 = Gtk.Entry()
#        e1.set_hexpand(True)
#        e1.set_vexpand(True)
        status_frame.add(tv)
        status_window.add(status_frame)

#        runout_frame = Gtk.Frame()
#        runout_frame.set_vexpand(True)
#        runout_frame.set_label(f"Runout/Clog")
#        runout_frame.set_label_align(.5,.0)

        runout_grid = Gtk.Grid()
        runout_grid.set_column_homogeneous(True)
#        runout_box = Gtk.Box()
#        e4 = Gtk.Entry()
#        e4.set_hexpand(True)
#        e4.set_vexpand(True)
#        runout_box.add(scale)
#        runout_frame.add(runout_box)
        runout_grid.attach(Gtk.Label(), 0, 0, 1, 1)
        runout_grid.attach(scale, 1, 0, 1, 1)
        runout_grid.attach(Gtk.Label(), 2, 0, 1, 1)
#        runout_frame.add(runout_grid)

        top_grid.attach(status_window, 0, 0, 3, 1)
        top_grid.attach(runout_grid, 3, 0, 1, 1)

        middle_buttons_grid = Gtk.Grid()
        middle_buttons_grid.set_column_homogeneous(True)

        left_middle_grid = Gtk.Grid()
        left_middle_grid.set_column_homogeneous(True)
        left_middle_grid.attach(self.buttons['decrease'], 0, 0, 1, 1)
        left_middle_grid.attach(self.buttons['tool'], 1, 0, 1, 1)
        left_middle_grid.attach(self.buttons['increase'], 2, 0, 1, 1)

        right_middle_grid = Gtk.Grid()
        right_middle_grid.set_column_homogeneous(True)
        right_middle_grid.attach(self.buttons['eject'], 0, 0, 1, 1)
        right_middle_grid.attach(self.buttons['check_gates'], 1, 0, 2, 1)

        middle_buttons_grid.set_vexpand(False)

        middle_buttons_grid.attach(left_middle_grid, 0, 0, 2, 1)
        middle_buttons_grid.attach(right_middle_grid, 2, 0, 2, 1)
#        middle_buttons_grid.attach(self.buttons['refresh'], 0, 0, 1, 1)
#        middle_buttons_grid.attach(Gtk.Box(), 1, 0, 1, 1)
#        middle_buttons_grid.attach(self.buttons['check_gates'], 2, 0, 1, 1)
#        middle_buttons_grid.attach(Gtk.Box(), 3, 0, 1, 1)

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

