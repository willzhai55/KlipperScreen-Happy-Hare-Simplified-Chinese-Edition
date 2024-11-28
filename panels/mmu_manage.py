# Happy Hare MMU Software
# Basic manual operation panel (generally in recovery situation)
#
# Copyright (C) 2023  moggieuk#6538 (discord)
#                     moggieuk@hotmail.com
#
import logging, gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel

class Panel(ScreenPanel):
    TOOL_UNKNOWN = -1
    TOOL_BYPASS = -2

    NOT_SET = -99

    def __init__(self, screen, title):
        super().__init__(screen, title)

        # We need to keep track of just a little bit of UI state
        self.ui_sel_gate = self.NOT_SET
        self.ui_action_button_name = self.ui_action_button_label = None

        self.has_bypass = False
        self.min_gate = 0
        self.has_bypass = self._printer.get_stat("mmu")['has_bypass']
        if self.has_bypass:
            self.min_gate = self.TOOL_BYPASS

        # btn_states: The "gaps" are what functionality the state takes away. Multiple states are combined
        self.btn_states = {
            'all':             ['gate', 'checkgate', 'recover', 'load', 'unload', 'home', 'motors_off', 'servo_up', 'servo_move', 'servo_down', 'load_ext', 'unload_ext'],
            'homed':           ['gate', 'checkgate', 'recover', 'load', 'unload',         'motors_off', 'servo_up', 'servo_move', 'servo_down', 'load_ext', 'unload_ext'],
            'not_homed':       [                     'recover',         'unload', 'home', 'motors_off', 'servo_up', 'servo_move', 'servo_down', 'load_ext', 'unload_ext'],
            'servo_up':        ['gate', 'checkgate', 'recover', 'load', 'unload', 'home', 'motors_off',             'servo_move', 'servo_down', 'load_ext', 'unload_ext'],
            'servo_move':      ['gate', 'checkgate', 'recover', 'load', 'unload', 'home', 'motors_off', 'servo_up',               'servo_down', 'load_ext', 'unload_ext'],
            'servo_down':      ['gate', 'checkgate', 'recover', 'load', 'unload', 'home', 'motors_off', 'servo_up', 'servo_move',               'load_ext', 'unload_ext'],
            'bypass_loaded':   [                     'recover',         'unload',         'motors_off', 'servo_up', 'servo_move', 'servo_down',             'unload_ext'],
            'bypass_unloaded': ['gate', 'checkgate', 'recover', 'load',           'home', 'motors_off', 'servo_up', 'servo_move', 'servo_down', 'load_ext', 'unload_ext'],
            'bypass_unknown':  ['gate', 'checkgate', 'recover', 'load', 'unload', 'home', 'motors_off', 'servo_up', 'servo_move', 'servo_down', 'load_ext', 'unload_ext'],
            'tool_loaded':     [                     'recover',         'unload',         'motors_off', 'servo_up', 'servo_move', 'servo_down',             'unload_ext'],
            'tool_unloaded':   ['gate', 'checkgate', 'recover', 'load',           'home', 'motors_off', 'servo_up', 'servo_move', 'servo_down', 'load_ext', 'unload_ext'],
            'tool_unknown':    ['gate', 'checkgate', 'recover', 'load', 'unload', 'home', 'motors_off', 'servo_up', 'servo_move', 'servo_down', 'load_ext', 'unload_ext'],
            'busy':            [                                                                                                                                        ],
            'disabled':        [                                                                                                                                        ],
        }

        self.labels = {
            'g_decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'gate': self._gtk.Button('mmu_select_gate', _('Gate'), 'color4'),
            'g_increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'home': self._gtk.Button('home', _('Home'), 'color2'),
            'motors_off': self._gtk.Button('motor-off', _('Motors Off'), 'color3'),
            'checkgate': self._gtk.Button('mmu_checkgates', _('Check Gate'), 'color4'),
            'recover': self._gtk.Button('mmu_maintenance', _('Recover State...'), 'color1'),
            'servo_up': self._gtk.Button('arrow-up', _('Servo Up'), 'color1'),
            'servo_move': self._gtk.Button('arrow-right', _('Servo Move'), 'color2'),
            'servo_down': self._gtk.Button('arrow-down', _('Servo Down'), 'color3'),
            'load': self._gtk.Button('mmu_load', _('Load'), 'color1'),
            'unload': self._gtk.Button('mmu_unload', _('Unload'), 'color2'),
            'load_ext': self._gtk.Button('mmu_load_extruder', _('Load Extruder'), 'color3'),
            'unload_ext': self._gtk.Button('mmu_unload_extruder', _('Unload Extruder'), 'color4'),
        }

        self.labels['g_decrease'].connect("clicked", self.select_gate, -1)
        self.labels['gate'].connect("clicked", self.select_gate, 0)
        self.labels['g_increase'].connect("clicked", self.select_gate, 1)
        self.labels['checkgate'].connect("clicked", self.select_checkgate)
        self.labels['recover'].connect("clicked", self.menu_item_clicked, {"panel": "mmu_recover", "name": "MMU State Recovery"})
        self.labels['load'].connect("clicked", self.select_load)
        self.labels['unload'].connect("clicked", self.select_unload)
        self.labels['home'].connect("clicked", self.select_home)
        self.labels['motors_off'].connect("clicked", self.select_motors_off)
        self.labels['servo_up'].connect("clicked", self.select_servo_up)
        self.labels['servo_move'].connect("clicked", self.select_servo_move)
        self.labels['servo_down'].connect("clicked", self.select_servo_down)
        self.labels['load_ext'].connect("clicked", self.select_load_extruder)
        self.labels['unload_ext'].connect("clicked", self.select_unload_extruder)

        self.labels['g_increase'].set_hexpand(False)
        self.labels['g_increase'].get_style_context().add_class("mmu_sel_increase")
        self.labels['g_decrease'].set_hexpand(False)
        self.labels['g_decrease'].get_style_context().add_class("mmu_sel_decrease")

        gate_grid = Gtk.Grid()
        gate_grid.set_column_homogeneous(False)
        gate_grid.attach(self.labels['g_decrease'], 0, 0, 1, 1)
        gate_grid.attach(self.labels['gate'],       1, 0, 1, 1)
        gate_grid.attach(self.labels['g_increase'], 2, 0, 1, 1)

        servo_grid = Gtk.Grid()
        servo_grid.set_column_homogeneous(True)
        servo_grid.attach(self.labels['servo_up'],   0, 0, 1, 1)
        servo_grid.attach(self.labels['servo_move'], 1, 0, 1, 1)
        servo_grid.attach(self.labels['servo_down'], 2, 0, 1, 1)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.attach(gate_grid,                 0, 0, 2, 1)
        grid.attach(servo_grid,                2, 0, 2, 1)
        grid.attach(self.labels['recover'],    0, 1, 1, 1)
        grid.attach(self.labels['home'],       1, 1, 1, 1)
        grid.attach(self.labels['motors_off'], 2, 1, 1, 1)
        grid.attach(self.labels['checkgate'],  3, 1, 1, 1)
        grid.attach(self.labels['load'],       0, 2, 1, 1)
        grid.attach(self.labels['unload'],      1, 2, 1, 1)
        grid.attach(self.labels['load_ext'],   2, 2, 1, 1)
        grid.attach(self.labels['unload_ext'], 3, 2, 1, 1)

        scroll = self._gtk.ScrolledWindow()
        scroll.add(grid)
        self.content.add(scroll)

        self.ui_sel_gate = self.NOT_SET
        self.ui_action_button_name = None
        self.ui_action_button_label = ""

    def activate(self):
        self.init_gate_values()
        if self.ui_action_button_name != None:
            self.labels[self.ui_action_button_name].set_label(self.ui_action_button_label)

    def process_update(self, action, data):
        if action == "notify_status_update":
            if 'mmu' in data:
                e_data = data['mmu']
                if 'gate' in e_data:
                    self.ui_sel_gate = e_data['gate']
                    if e_data['gate'] >= 0:
                        self.labels['load'].set_label(f"Load #{e_data['gate']}")
                    else:
                        self.labels['load'].set_label(f"Load")
                if 'action' in e_data:
                    action = e_data['action']
                    if self.ui_action_button_name != None:
                        if action == "Idle" or action == "Unknown":
                            self.labels[self.ui_action_button_name].set_label(self.ui_action_button_label) # Restore original button label
                            self.ui_action_button_name = None
                        else:
                            self.labels[self.ui_action_button_name].set_label(action) # Use button to convey action status
                self.update_active_buttons()

    def init_gate_values(self):
        # Get starting values
        mmu = self._printer.get_stat("mmu")
        if self.ui_sel_gate == self.NOT_SET and mmu['gate'] != self.TOOL_UNKNOWN:
            self.ui_sel_gate = mmu['gate']
        else:
            self.ui_sel_gate = 0

    def select_gate(self, widget, param=0):
        mmu = self._printer.get_stat("mmu")
        num_gates = len(mmu['gate_status'])

        if param < 0 and self.ui_sel_gate > self.min_gate:
            self.ui_sel_gate -= 1
            if self.ui_sel_gate == self.TOOL_UNKNOWN:
                self.ui_sel_gate = self.TOOL_BYPASS
        elif param > 0 and self.ui_sel_gate < num_gates - 1:
            self.ui_sel_gate += 1
            if self.ui_sel_gate == self.TOOL_UNKNOWN:
                self.ui_sel_gate = 0
        elif param == 0:
            self.ui_action_button_name = 'gate'
            self.ui_action_button_label = self.labels[self.ui_action_button_name].get_label()
            if self.ui_sel_gate == self.TOOL_BYPASS:
                self._screen._ws.klippy.gcode_script(f"MMU_SELECT_BYPASS")
            elif mmu['filament'] != "Loaded":
                self._screen._ws.klippy.gcode_script(f"MMU_SELECT GATE={self.ui_sel_gate}")
            return
        self.update_gate_buttons()

    def select_gatebutton(self, widget):
        self.ui_action_button_name = 'gate'
        self.ui_action_button_label = self.labels[self.ui_action_button_name].get_label()
        self._screen._ws.klippy.gcode_script(f"MMU_SELECT GATE={self.ui_sel_gate}")

    def select_checkgate(self, widget):
        self.ui_action_button_name = 'checkgate'
        self.ui_action_button_label = self.labels[self.ui_action_button_name].get_label()
        mmu = self._printer.get_stat("mmu")
        current_gate = mmu['gate']
        self._screen._ws.klippy.gcode_script(f"MMU_CHECK_GATE GATE={current_gate} QUIET=1")

    def select_load(self, widget):
        self.ui_action_button_name = 'load'
        self.ui_action_button_label = self.labels[self.ui_action_button_name].get_label()
        self._screen._ws.klippy.gcode_script(f"MMU_LOAD TEST=0") # TEST=0 is to aid backward compatibility of MMU_LOAD command

    def select_unload(self, widget):
        self.ui_action_button_name = 'unload'
        self.ui_action_button_label = self.labels[self.ui_action_button_name].get_label()
        self._screen._ws.klippy.gcode_script(f"MMU_UNLOAD")

    def select_home(self, widget):
        self.ui_action_button_name = 'home'
        self.ui_action_button_label = self.labels[self.ui_action_button_name].get_label()
        self._screen._ws.klippy.gcode_script(f"MMU_HOME")

    def select_motors_off(self, widget):
        self._screen._confirm_send_action(
            None,
            "This will reset MMU positional state and require re-homing\n\nSure you want to continue?",
            "printer.gcode.script",
            {'script': "MMU_MOTORS_OFF"}
        )

    def select_servo_up(self, widget):
        self._screen._ws.klippy.gcode_script(f"MMU_SERVO POS=up")

    def select_servo_move(self, widget):
        self._screen._ws.klippy.gcode_script(f"MMU_SERVO POS=move")

    def select_servo_down(self, widget):
        self._screen._ws.klippy.gcode_script(f"MMU_SERVO POS=down")

    def select_load_extruder(self, widget):
        self.ui_action_button_name = 'load_ext'
        self.ui_action_button_label = self.labels[self.ui_action_button_name].get_label()
        self._screen._ws.klippy.gcode_script(f"MMU_LOAD EXTRUDER_ONLY=1")

    def select_unload_extruder(self, widget):
        self.ui_action_button_name = 'unload_ext'
        self.ui_action_button_label = self.labels[self.ui_action_button_name].get_label()
        self._screen._ws.klippy.gcode_script(f"MMU_UNLOAD EXTRUDER_ONLY=1")

    # Dynamically update button sensitivity based on state
    def update_active_buttons(self):
        mmu = self._printer.get_stat("mmu")
        enabled = mmu['enabled']
        servo = mmu.get('servo', None)
        is_homed = mmu['is_homed']
        gate = mmu['gate']
        tool = mmu['tool']
        action = mmu['action']
        filament = mmu['filament']
        ui_state = []
        if enabled:
            ui_state.extend(['servo_up'] if servo == 'Up' else ['servo_down'] if servo == 'Down' else ['servo_move'] if servo == 'Move' else [] if servo == 'Unknown' else ['servo_up', 'servo_down', 'servo_move', 'homed'])
            if not is_homed:
                ui_state.append("not_homed")

            if tool == self.TOOL_BYPASS:
                if filament == "Loaded":
                    ui_state.append("bypass_loaded")
                elif filament == "Unloaded":
                    ui_state.append("bypass_unloaded")
                else:
                    ui_state.append("bypass_unknown")
            elif tool >= 0:
                if filament == "Loaded":
                    ui_state.append("tool_loaded")
                elif filament == "Unloaded":
                    ui_state.append("tool_unloaded")
                else:
                    ui_state.append("tool_unknown")

            if action != "Idle" and action != "Unknown":
                ui_state.append("busy")
        else:
            ui_state.append("disabled")

        logging.debug(f"mmu_manage: ui_state={ui_state}")
        for label in self.btn_states['all']:
            sensitive = True
            for state in ui_state:
                if not label in self.btn_states[state]:
                    sensitive = False
                    break
            if sensitive:
                self.labels[label].set_sensitive(True)
            else:
                self.labels[label].set_sensitive(False)
            if label == "gate":
                gate_sensitive = sensitive
        self.update_gate_buttons(gate_sensitive)

    def update_gate_buttons(self, gate_sensitive=True):
        mmu = self._printer.get_stat("mmu")
        gate = mmu['gate']
        filament = mmu['filament']
        num_gates = len(mmu['gate_status'])
        action = mmu['action']
        if (gate == self.TOOL_BYPASS and filament != "Unloaded") or not gate_sensitive:
            self.labels['g_decrease'].set_sensitive(False)
            self.labels['g_increase'].set_sensitive(False)
        else:
            if self.ui_sel_gate == self.min_gate:
                self.labels['g_decrease'].set_sensitive(False)
            else:
                self.labels['g_decrease'].set_sensitive(True)

            if self.ui_sel_gate == num_gates -1:
                self.labels['g_increase'].set_sensitive(False)
            else:
                self.labels['g_increase'].set_sensitive(True)

        if action == "Idle":
            if self.ui_sel_gate >= 0:
                self.labels['gate'].set_label(f"Gate #{self.ui_sel_gate}")
                if mmu['gate'] == self.ui_sel_gate:
                    self.labels['gate'].set_sensitive(False)
                else:
                    self.labels['gate'].set_sensitive(gate_sensitive)
            elif self.ui_sel_gate == self.TOOL_BYPASS:
                self.labels['gate'].set_label(f"Bypass")
                if mmu['gate'] == self.ui_sel_gate:
                    self.labels['gate'].set_sensitive(False)
                else:
                    self.labels['gate'].set_sensitive(gate_sensitive)
            else:
                self.labels['gate'].set_label(f"Unknown")
        else:
            self.labels['gate'].set_label(action)
            self.labels['gate'].set_sensitive(False)

        if self.ui_sel_gate == self.TOOL_BYPASS:
            self.labels['checkgate'].set_sensitive(False)
        elif gate_sensitive:
            self.labels['checkgate'].set_sensitive(True)

