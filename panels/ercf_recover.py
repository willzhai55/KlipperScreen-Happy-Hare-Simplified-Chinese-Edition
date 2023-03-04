# Happy Hare ERCF Software
# State recovery panel
#
# Copyright (C) 2022  moggieuk#6538 (discord)
#
import logging, gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return ErcfRecoveryPanel(*args)


class ErcfRecoveryPanel(ScreenPanel):
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

        self.all_btns = ['t_decrease', 'tool', 't_increase', 'g_decrease', 'gate', 'g_increase', 'filament', 'manual', 'auto', "reset",
                'home', 'motors_off', 'servo_up', 'servo_down', 'load_ext', 'unload_ext']

        self.labels = {
            't_decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'tool': self._gtk.Label("T0"),
            't_increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'g_decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'gate': self._gtk.Label("Gate #0"),
            'g_increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'filament': Gtk.CheckButton("Filament: UNKNOWN"),
            'manual': self._gtk.Button('ercf_recover_manual', _('Set State'), 'color1'),
            'auto': self._gtk.Button('ercf_recover_auto', _('Auto Recover'), 'color2'),
            'reset': self._gtk.Button('ercf_reset', _('Reset ERCF')),
            'home': self._gtk.Button('home', _('Home'), 'color1'),
            'motors_off': self._gtk.Button('motor-off', _('Motors Off'), 'color2'),
            'servo_up': self._gtk.Button('arrow-up', _('Servo Up'), 'color3'),
            'servo_down': self._gtk.Button('arrow-down', _('Servo Down'), 'color3'),
            'load_ext': self._gtk.Button('ercf_load_extruder', _('Load Extruder'), 'color4'),
            'unload_ext': self._gtk.Button('ercf_unload_extruder', _('Unoad Extruder'), 'color4'),
        }

        self.labels['t_decrease'].connect("clicked", self.select_toolgate, 'tool', -1)
        self.labels['t_increase'].connect("clicked", self.select_toolgate, 'tool', 1)
        self.labels['g_decrease'].connect("clicked", self.select_toolgate, 'gate', -1)
        self.labels['g_increase'].connect("clicked", self.select_toolgate, 'gate', 1)
        self.labels['filament'].connect("notify::active", self.select_toolgate, 'loaded')
        self.labels['auto'].connect("clicked", self.select_auto)
        self.labels['manual'].connect("clicked", self.select_manual)

        self.labels['reset'].connect("clicked", self.select_reset)
        self.labels['home'].connect("clicked", self.select_home)
        self.labels['load_ext'].connect("clicked", self.select_load_extruder)
        self.labels['unload_ext'].connect("clicked", self.select_unload_extruder)

        self.labels['t_increase'].set_halign(Gtk.Align.START)
        self.labels['t_increase'].set_margin_start(10)
        self.labels['t_decrease'].set_halign(Gtk.Align.END)
        self.labels['t_decrease'].set_margin_end(10)
        self.labels['g_increase'].set_halign(Gtk.Align.START)
        self.labels['g_increase'].set_margin_start(10)
        self.labels['g_decrease'].set_halign(Gtk.Align.END)
        self.labels['g_decrease'].set_margin_end(10)

        self.labels['tool'].get_style_context().add_class("ercf_tool_text")
        self.labels['gate'].get_style_context().add_class("ercf_gate_text")
        self.labels['filament'].get_style_context().add_class("ercf_recover")

        recover_grid = Gtk.Grid()
        recover_grid.set_column_homogeneous(True)
        recover_grid.set_row_homogeneous(False)
        box = Gtk.Box()
        box.pack_start(Gtk.Label("ERCF STATE:"), True, True, 0)
        box.pack_start(self.labels['reset'], False, False, 0)
        recover_grid.attach(box,                         0, 0, 3, 1)
        recover_grid.attach(self.labels['t_decrease'],   0, 1, 1, 1)
        recover_grid.attach(self.labels['tool'],         1, 1, 1, 1)
        recover_grid.attach(self.labels['t_increase'],   2, 1, 1, 1)
        recover_grid.attach(self.labels['g_decrease'],   0, 2, 1, 1)
        recover_grid.attach(self.labels['gate'],         1, 2, 1, 1)
        recover_grid.attach(self.labels['g_increase'],   2, 2, 1, 1)
        recover_grid.attach(self.labels['filament'],     0, 3, 3, 1)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.attach(recover_grid,               0, 0, 2, 2)
        grid.attach(self.labels['home'],        2, 0, 1, 1)
        grid.attach(self.labels['motors_off'],  3, 0, 1, 1)
        grid.attach(self.labels['servo_up'],    2, 1, 1, 1)
        grid.attach(self.labels['servo_down'],  3, 1, 1, 1)
        grid.attach(self.labels['manual'],      0, 2, 1, 1)
        grid.attach(self.labels['auto'],        1, 2, 1, 1)
        grid.attach(self.labels['load_ext'],    2, 2, 1, 1)
        grid.attach(self.labels['unload_ext'],  3, 2, 1, 1)

        self.content.add(grid)

    def activate(self):
        logging.info(f"++++ PAUL: avtivate() called")
        self.ui_sel_tool = self.ui_sel_gate = self.ui_sel_loaded = self.DUMMY
        self.init_toolgate_values()
        self.update_toolgate_buttons()

    def process_update(self, action, data):
        if action == "notify_status_update":
            if 'ercf' in data:
                e_data = data['ercf']
                if 'tool' in e_data or 'gate' in e_data or 'filament' in e_data:
                    self.update_toolgate_buttons()
                if 'enabled' in e_data:
                    self.update_enabled(e_data['enabled'])

    def update_enabled(self, enabled):
        for i in self.all_btns:
            if enabled:
                self.labels[i].set_sensitive(True)
            else:
                self.labels[i].set_sensitive(False)

    def init_toolgate_values(self):
        # Get starting values
        ercf = self._printer.get_stat("ercf")
        if self.ui_sel_tool == self.DUMMY:
            self.ui_sel_tool = ercf['tool']
        if self.ui_sel_gate == self.DUMMY:
            self.ui_sel_gate = ercf['gate']
        if self.ui_sel_loaded == self.DUMMY:
            self.ui_sel_loaded = 0 if ercf['filament'] == "Unloaded" else 1

    def get_possible_gates(self, tool):
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])
        endless_spool_groups = ercf['endless_spool_groups']
        ttg_map = ercf['ttg_map']
        gate_status = ercf['gate_status']

        gate = ttg_map[tool]
        group = endless_spool_groups[tool]
        logging.info(f"@@@************@@@ PAUL: initial gate={gate}, group={group}")

        next_gate = -1
        checked_gates = []
        for i in range(num_gates):
            check = (gate + i + 1) % num_gates
            logging.info(f"@@@************@@@ PAUL: checking={check}")
            if endless_spool_groups[check] == group:
                checked_gates.append(check)
                if gate_status[check] != self.GATE_EMPTY:
                    next_gate = check
                    break
        if next_gate == -1:
            next_gate = gate
        logging.info(f"@@@************@@@ PAUL: next_gate={next_gate}, possible={checked_gates}")
        return next_gate, checked_gates

    def select_toolgate(self, widget, toolgate, param=0):
        logging.info(f"@@@************@@@ PAUL: select_toolgate toolgate={toolgate} param={param}")
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])

        if toolgate == "tool":
            if param < 0 and self.ui_sel_tool > -2:
                self.ui_sel_tool -= 1
                if self.ui_sel_tool == self.TOOL_UNKNOWN:
                    self.ui_sel_tool = self.TOOL_BYPASS
            elif param > 0 and self.ui_sel_tool < num_gates - 1:
                self.ui_sel_tool += 1
                if self.ui_sel_tool == self.TOOL_UNKNOWN:
                    self.ui_sel_tool = 0

            # Be smart about updating a gate. Only override if it is helpful / necessary
            if self.ui_sel_tool == self.TOOL_BYPASS:
                self.ui_sel_gate = self.TOOL_BYPASS
            elif self.ui_sel_tool >= 0:
                suggested_gate, possible_gates = self.get_possible_gates(self.ui_sel_tool)
                if self.ui_sel_gate == self.TOOL_UNKNOWN or self.ui_sel_gate == self.TOOL_BYPASS or not self.ui_sel_gate in possible_gates:
                    self.ui_sel_gate = suggested_gate
        elif toolgate == "gate":
            # PAUL TODO logic to use:
            # suggested_gate, possible_gates = self.get_possible_gates(self.ui_sel_tool)
            # for smart setting.  Only call if tool is not UNKNOWN
            # May want pop up to explain illegal values...? How to do?
            # Example popup... self._screen.show_popup_message(_("Can't set above the maximum:") + f' {max_temp}')
            if param < 0 and self.ui_sel_gate > -2:
                self.ui_sel_gate -= 1
                if self.ui_sel_gate == self.TOOL_UNKNOWN:
                    self.ui_sel_gate = self.TOOL_BYPASS
            elif param > 0 and self.ui_sel_gate < num_gates - 1:
                self.ui_sel_gate += 1
                if self.ui_sel_gate == self.TOOL_UNKNOWN:
                    self.ui_sel_gate = 0
        else:
            # Filament loaded switch
            if self.labels['filament'].get_active():
                self.ui_sel_loaded = 1
            else:
                self.ui_sel_loaded = 0

        self.update_toolgate_buttons()

    def select_manual(self, widget):
        loaded = "Loaded" if self.ui_sel_loaded == 1 else "Unloaded"
        summary = (f"T{self.ui_sel_tool} on Gate #{self.ui_sel_gate} with filament {loaded}")
        self._screen._confirm_send_action(
            None,
            _("This will set the ERCF state to\n\n" + summary + "\n\nSure you want to continue?"),
            "printer.gcode.script",
            {'script': f"ERCF_RECOVER TOOL={self.ui_sel_tool} GATE={self.ui_sel_gate} LOADED={self.ui_sel_loaded}"}
        )
        self._screen._menu_go_back()

    def select_auto(self, widget):
        self._screen._confirm_send_action(
            None,
            _("This will automatically attempt to reset the ERCF state\n\nSure you want to continue?"),
            "printer.gcode.script",
            {'script': "ERCF_RECOVER"}
        )
        self._screen._menu_go_back()

    def select_home(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_HOME")
        self._screen._menu_go_back()

    def select_load_extruder(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_LOAD EXTRUDER_ONLY=1")

    def select_unload_extruder(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_EJECT EXTRUDER_ONLY=1")

    def select_reset(self, widget):
        self._screen._confirm_send_action(
            None,
            _("This will reset persisted ERCF state to defaults including\n\nTTG map, EndlessSpool groups, gate status and selector position\n\nSure you want to continue?"),
            "printer.gcode.script",
            {'script': "ERCF_RESET"}
        )
        self._screen._menu_go_back()

    def update_toolgate_buttons(self):
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])
        if self.ui_sel_tool == self.TOOL_BYPASS:
            self.labels['t_decrease'].set_sensitive(False)
        else:
            self.labels['t_decrease'].set_sensitive(True)

        if self.ui_sel_tool == num_gates -1:
            self.labels['t_increase'].set_sensitive(False)
        else:
            self.labels['t_increase'].set_sensitive(True)

        if self.ui_sel_gate == self.TOOL_BYPASS:
            self.labels['g_decrease'].set_sensitive(False)
        else:
            self.labels['g_decrease'].set_sensitive(True)

        if self.ui_sel_gate == num_gates -1:
            self.labels['g_increase'].set_sensitive(False)
        else:
            self.labels['g_increase'].set_sensitive(True)

        if (self.ui_sel_tool == self.DUMMY or self.ui_sel_gate == self.DUMMY
                or self.ui_sel_loaded == self.DUMMY or self.ui_sel_tool == self.TOOL_UNKNOWN
                or self.ui_sel_gate == self.TOOL_UNKNOWN):
            self.labels['manual'].set_sensitive(False)
        else:
            self.labels['manual'].set_sensitive(True)

        if self.ui_sel_tool >= 0:
            self.labels['tool'].set_label(f"T{self.ui_sel_tool}")
        elif self.ui_sel_tool == self.TOOL_BYPASS:
            self.labels['tool'].set_label(f"Bypass")
        else:
            self.labels['tool'].set_label(f"n/a")

        if self.ui_sel_gate >= 0:
            self.labels['gate'].set_label(f"Gate #{self.ui_sel_gate}")
        elif self.ui_sel_gate == self.TOOL_BYPASS:
            self.labels['gate'].set_label(f"Bypass")
        else:
            self.labels['gate'].set_label(f"n/a")

        if self.ui_sel_loaded == 1:
            self.labels['filament'].set_label("Filament: LOADED")
        elif self.ui_sel_loaded == 0:
            self.labels['filament'].set_label("Filament: UNLOADED")
        else:
            self.labels['filament'].set_label("Filament: UNKNOWN")

