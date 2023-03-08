# Happy Hare ERCF Software
# Basic management panel (generally in recovery situation)
#
# Copyright (C) 2022  moggieuk#6538 (discord)
#
import logging, gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return ErcfManage(*args)


class ErcfManage(ScreenPanel):
    TOOL_UNKNOWN = -1
    TOOL_BYPASS = -2

    GATE_UNKNOWN = -1
    GATE_EMPTY = 0
    GATE_AVAILABLE = 1

    DUMMY = -99

    def __init__(self, screen, title):
        super().__init__(screen, title)

        # We need to keep track of just a little bit of UI state
        self.ui_sel_tool = self.ui_sel_gate = self.DUMMY
        self.ui_sel_loaded = self.DUMMY

        self.has_bypass = False
        self.min_tool = 0
        if 'ercf' in self._printer.get_config_section_list():
            ercf_config = self._printer.get_config_section("ercf")
            if 'bypass_selector' in ercf_config:
                if float(ercf_config['bypass_selector']) > 0.:
                    self.has_bypass = True
                    self.min_tool = self.TOOL_BYPASS

        # btn_states: the "gaps" are what functionality the state takes away
        self.btn_states = {
            'all':          ['gate', 'check', 'recover', 'load', 'eject', 'home', 'motors_off', 'servo_up', 'servo_down', 'load_ext', 'unload_ext'],
            'not_homed':    [                 'recover',                  'home', 'motors_off', 'servo_up', 'servo_down', 'load_ext', 'unload_ext'],
            'servo_up':     ['gate', 'check', 'recover', 'load', 'eject', 'home', 'motors_off',             'servo_down', 'load_ext', 'unload_ext'],
            'servo_down':   ['gate', 'check', 'recover', 'load', 'eject', 'home', 'motors_off', 'servo_up',               'load_ext', 'unload_ext'],
            'gate_changed': ['gate',          'recover',                  'home', 'motors_off', 'servo_up',               'load_ext', 'unload_ext'],
            'disabled':     [                                                                                                                     ],
        }

        self.labels = {
            'g_decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'gate': self._gtk.Button('ercf_select_gate', _('Gate'), 'color4'),
            'g_increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'home': self._gtk.Button('home', _('Home'), 'color3'),
            'motors_off': self._gtk.Button('motor-off', _('Motors Off'), 'color4'),
            'check': self._gtk.Button('ercf_checkgates', _('Check Gate'), 'color1'),
            'recover': self._gtk.Button('ercf_maintenance', _('Recover State...'), 'color2'),
            'servo_up': self._gtk.Button('arrow-up', _('Servo Up'), 'color3'),
            'servo_down': self._gtk.Button('arrow-down', _('Servo Down'), 'color4'),
            'load': self._gtk.Button('ercf_load', _('Load'), 'color1'),
            'eject': self._gtk.Button('ercf_eject', _('Eject'), 'color2'),
            'load_ext': self._gtk.Button('ercf_load_extruder', _('Load Extruder'), 'color3'),
            'unload_ext': self._gtk.Button('ercf_unload_extruder', _('Unoad Extruder'), 'color4'),
        }

        self.labels['g_decrease'].connect("clicked", self.select_gate, -1)
        self.labels['gate'].connect("clicked", self.select_gatebutton, -1)
        self.labels['g_increase'].connect("clicked", self.select_gate, 1)
        self.labels['check'].connect("clicked", self.select_checkgate, 1)
        self.labels['recover'].connect("clicked", self.menu_item_clicked, "recover", {
            "panel": "ercf_recover", "name": _("ERCF State Recovery")})
        self.labels['load'].connect("clicked", self.select_load, 1)
        self.labels['eject'].connect("clicked", self.select_eject, 1)
        self.labels['home'].connect("clicked", self.select_home)
        self.labels['motors_off'].connect("clicked", self.select_motors_off)
        self.labels['servo_up'].connect("clicked", self.select_servo_up)
        self.labels['servo_down'].connect("clicked", self.select_servo_down)
        self.labels['load_ext'].connect("clicked", self.select_load_extruder)
        self.labels['unload_ext'].connect("clicked", self.select_unload_extruder)

        self.labels['g_increase'].set_halign(Gtk.Align.START)
        self.labels['g_increase'].set_margin_start(10)
        self.labels['g_decrease'].set_halign(Gtk.Align.END)
        self.labels['g_decrease'].set_margin_end(10)

        gate_grid = Gtk.Grid()
        gate_grid.set_column_homogeneous(False)
        gate_grid.attach(self.labels['g_decrease'],   0, 0, 1, 1)
        gate_grid.attach(self.labels['gate'],         1, 0, 1, 1)
        gate_grid.attach(self.labels['g_increase'],   2, 0, 1, 1)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.attach(gate_grid,                  0, 0, 2, 1)
        grid.attach(self.labels['home'],        2, 0, 1, 1)
        grid.attach(self.labels['motors_off'],  3, 0, 1, 1)
        grid.attach(self.labels['check'],       0, 1, 1, 1)
        grid.attach(self.labels['recover'],     1, 1, 1, 1)
        grid.attach(self.labels['servo_up'],    2, 1, 1, 1)
        grid.attach(self.labels['servo_down'],  3, 1, 1, 1)
        grid.attach(self.labels['load'],        0, 2, 1, 1)
        grid.attach(self.labels['eject'],       1, 2, 1, 1)
        grid.attach(self.labels['load_ext'],    2, 2, 1, 1)
        grid.attach(self.labels['unload_ext'],  3, 2, 1, 1)

        self.content.add(grid)

    def activate(self):
        self.ui_sel_tool = self.ui_sel_gate = self.ui_sel_loaded = self.DUMMY
        self.init_toolgate_values()
        self.update_gate_buttons()

    def process_update(self, action, data):
        if action == "notify_status_update":
            if 'ercf' in data:
                e_data = data['ercf']
                if 'tool' in e_data or 'gate' in e_data or 'filament' in e_data:
                    self.update_gate_buttons() # PAUL check this
                if 'enabled' in e_data or 'servo' in e_data:
                    self.update_active_buttons()

    # Dynamically update button sensitivity based on state
    def update_active_buttons(self):
        ercf = self._printer.get_stat("ercf")
        printer_state = self._printer.get_stat("print_stats")['state']
        enabled = ercf['enabled']
        servo = ercf['servo']
        is_homed = ercf['is_homed']
        current_gate = ercf['gate']
        ui_state = []
        if enabled:
            ui_state.append("servo_up" if servo == "Up" else "servo_down" if servo == "Down" else "all")
            if not is_homed:
                ui_state.append("not_homed")
            if current_gate != self.ui_sel_gate:
                ui_state.append("gate_changed")
        else:
            ui_state.append("disabled")
        # PAUL more to do

        logging.info(f"*-*-*-* >>>>> ui_state={ui_state}")
        for label in self.btn_states['all']:
            enabled = True
            for state in ui_state:
                if not label in self.btn_states[state]:
                    enabled = False
                    break
            if enabled:
                self.labels[label].set_sensitive(True)
            else:
                self.labels[label].set_sensitive(False)
# PAUL TODO           if label == "gate":
#                self.update_gate_buttons(sensitive)

    def init_toolgate_values(self):
        # PAUL may not be needed because can use real state..?
        # Get starting values
        ercf = self._printer.get_stat("ercf")
        if self.ui_sel_tool == self.DUMMY:
            self.ui_sel_tool = ercf['tool']
        if self.ui_sel_gate == self.DUMMY:
            self.ui_sel_gate = ercf['gate']
        if self.ui_sel_loaded == self.DUMMY:
            self.ui_sel_loaded = 0 if ercf['filament'] == "Unloaded" else 1

    def select_gate(self, widget, param=0):
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])

        if param < 0 and self.ui_sel_gate > (self.min_tool if self.ui_sel_tool == self.TOOL_BYPASS else 0):
            self.ui_sel_gate -= 1
            if self.ui_sel_gate == self.TOOL_UNKNOWN:
                self.ui_sel_gate = self.TOOL_BYPASS
        elif param > 0 and self.ui_sel_gate < num_gates - 1:
            self.ui_sel_gate += 1
            if self.ui_sel_gate == self.TOOL_UNKNOWN:
                self.ui_sel_gate = 0

        self.update_gate_buttons()

    def select_gatebutton(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_SELECT GATE={self.ui_sel_gate}")

    def select_checkgate(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_CHECKGATES GATE={self.ui_sel_gate}")

    def select_load(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_LOAD TEST=0") # TEST=0 is to aid backward compatibility

    def select_eject(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_EJECT")

    def select_home(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_HOME")

    def select_motors_off(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_MOTORS_OFF")

    def select_servo_up(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_SERVO_UP")

    def select_servo_down(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_SERVO_DOWN")

    def select_load_extruder(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_LOAD EXTRUDER_ONLY=1")

    def select_unload_extruder(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_EJECT EXTRUDER_ONLY=1")

    def update_gate_buttons(self):
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])
        if self.ui_sel_tool == self.TOOL_BYPASS:
            self.labels['g_decrease'].set_sensitive(False)
            self.labels['g_increase'].set_sensitive(False)
        else:
            if self.ui_sel_gate == (self.min_tool if self.ui_sel_tool == self.TOOL_BYPASS else 0):
                self.labels['g_decrease'].set_sensitive(False)
            else:
                self.labels['g_decrease'].set_sensitive(True)

            if self.ui_sel_gate == num_gates -1:
                self.labels['g_increase'].set_sensitive(False)
            else:
                self.labels['g_increase'].set_sensitive(True)

#        if (self.ui_sel_tool == self.DUMMY or self.ui_sel_gate == self.DUMMY
#                or self.ui_sel_loaded == self.DUMMY or self.ui_sel_tool == self.TOOL_UNKNOWN
#                or self.ui_sel_gate == self.TOOL_UNKNOWN):
#            self.labels['manual'].set_sensitive(False)
#        else:
#            self.labels['manual'].set_sensitive(True)

        if self.ui_sel_gate >= 0:
            self.labels['gate'].set_label(f"Gate #{self.ui_sel_gate}")
        elif self.ui_sel_gate == self.TOOL_BYPASS:
            self.labels['gate'].set_label(f"Bypass")
        else:
            self.labels['gate'].set_label(f"n/a")

