# Happy Hare ERCF Software
# State recovery panel
#
# Copyright (C) 2023  moggieuk#6538 (discord)
#                     moggieuk@hotmail.com
#
import logging, gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return ErcfRecovery(*args)

class ErcfRecovery(ScreenPanel):
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
            'all':        ['tool', 'gate', 'filament', 'manual', 'auto', 'reset'],
            'disabled':   [                                                     ],
        }

        self.labels = {
            't_decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'tool': self._gtk.Label("T0"),
            't_increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'g_decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'gate': self._gtk.Label("Gate #0"),
            'g_increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'filament': Gtk.CheckButton("Filament: Unknown"),
            'reset': self._gtk.Button('ercf_reset', _('Reset ERCF'), 'color1'),
            'auto': self._gtk.Button('ercf_recover_auto', _('Auto Recover'), 'color2'),
            'manual': self._gtk.Button('ercf_recover_manual', _('Set State'), 'color1'),
        }

        self.labels['t_decrease'].connect("clicked", self.select_toolgate, 'tool', -1)
        self.labels['t_increase'].connect("clicked", self.select_toolgate, 'tool', 1)
        self.labels['g_decrease'].connect("clicked", self.select_toolgate, 'gate', -1)
        self.labels['g_increase'].connect("clicked", self.select_toolgate, 'gate', 1)
        self.labels['filament'].connect("notify::active", self.select_toolgate, 'loaded')
        self.labels['reset'].connect("clicked", self.select_reset)
        self.labels['auto'].connect("clicked", self.select_auto)
        self.labels['manual'].connect("clicked", self.select_manual)

        self.labels['t_increase'].set_halign(Gtk.Align.START)
        self.labels['t_increase'].set_margin_start(10)
        self.labels['t_decrease'].set_halign(Gtk.Align.END)
        self.labels['t_decrease'].set_margin_end(10)
        self.labels['g_increase'].set_halign(Gtk.Align.START)
        self.labels['g_increase'].set_margin_start(10)
        self.labels['g_decrease'].set_halign(Gtk.Align.END)
        self.labels['g_decrease'].set_margin_end(10)
        self.labels['filament'].set_halign(Gtk.Align.CENTER)

        self.labels['tool'].get_style_context().add_class("ercf_tool_text")
        self.labels['gate'].get_style_context().add_class("ercf_gate_text")
        self.labels['filament'].get_style_context().add_class("ercf_recover")

        for i in ['current_state', 'tool_label', 'gate_label', 'filament_label', 'future_state']:
            self.labels[i] = Gtk.Label()
            self.labels[i].set_xalign(0.5 if i.endswith("state") else 0)
            self.labels[i].set_yalign(0.7 if i.endswith("state") else 0.5)
            self.labels[i].get_style_context().add_class("ercf_recover")
        self.labels['current_state'].set_label("Current ERCF State:")
        self.labels['future_state'].set_label("Reset State To:")

        status_grid = Gtk.Grid()
        status_grid.set_column_homogeneous(True)
        status_grid.set_row_homogeneous(True)
        status_grid.attach(self.labels['current_state'],     0, 0, 3, 1)
        status_grid.attach(self._gtk.Image('extruder'),      0, 1, 1, 1)
        status_grid.attach(self.labels['tool_label'],        1, 1, 2, 1)
        status_grid.attach(self._gtk.Image('ercf_gate'),     0, 2, 1, 1)
        status_grid.attach(self.labels['gate_label'],        1, 2, 2, 1)
        status_grid.attach(self._gtk.Image('ercf_filament'), 0, 3, 1, 1)
        status_grid.attach(self.labels['filament_label'],    1, 3, 2, 1)

        status_grid.attach(self.labels['future_state'],      3, 0, 3, 1)
        status_grid.attach(self.labels['t_decrease'],        3, 1, 1, 1)
        status_grid.attach(self.labels['tool'],              4, 1, 1, 1)
        status_grid.attach(self.labels['t_increase'],        5, 1, 1, 1)
        status_grid.attach(self.labels['g_decrease'],        3, 2, 1, 1)
        status_grid.attach(self.labels['gate'],              4, 2, 1, 1)
        status_grid.attach(self.labels['g_increase'],        5, 2, 1, 1)
        status_grid.attach(self.labels['filament'],          3, 3, 3, 1)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.attach(status_grid,           0, 0, 4, 2)
        grid.attach(self.labels['reset'],  0, 2, 1, 1)
        grid.attach(self.labels['auto'],   1, 2, 1, 1)
        grid.attach(self.labels['manual'], 2, 2, 2, 1)

        scroll = self._gtk.ScrolledWindow()
        scroll.add(grid)
        self.content.add(scroll)

    def activate(self):
        self.ui_sel_tool = self.ui_sel_gate = self.ui_sel_loaded = self.DUMMY
        self.init_toolgate_values()

    def process_update(self, action, data):
        if action == "notify_status_update":
            if 'ercf' in data:
                e_data = data['ercf']
                if 'tool' in e_data or 'gate' in e_data or 'filament' in e_data:
                    self.update_state_labels()
                    self.update_toolgate_buttons()
                if 'enabled' in e_data:
                    self.update_active_buttons()

    # Dynamically update button sensitivity based on state
    def update_active_buttons(self):
        ercf = self._printer.get_stat("ercf")
        printer_state = self._printer.get_stat("print_stats")['state']
        servo = ercf['servo']
        enabled = ercf['enabled']
        ui_state = []
        if not enabled:
            ui_state.append("disabled")

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
            if label == "tool":
                self.update_toolgate_buttons(sensitive)

    # Get starting values
    def init_toolgate_values(self):
        ercf = self._printer.get_stat("ercf")
        if self.ui_sel_tool == self.DUMMY:
            self.ui_sel_tool = ercf['tool']
        if self.ui_sel_gate == self.DUMMY:
            self.ui_sel_gate = ercf['gate']
        if self.ui_sel_loaded == self.DUMMY:
            self.ui_sel_loaded = 0 if ercf['filament'] == "Unloaded" else 1 if ercf['filament'] == "Loaded" else -1

    def get_possible_gates(self, tool):
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])
        endless_spool_groups = ercf['endless_spool_groups']
        ttg_map = ercf['ttg_map']
        gate_status = ercf['gate_status']

        gate = ttg_map[tool]
        group = endless_spool_groups[tool]

        best_gate = -1
        possible_gates = []
        for i in range(num_gates):
            check = (gate + i) % num_gates
            if endless_spool_groups[check] == group:
                possible_gates.append(check)
                if best_gate == -1 and gate_status[check] != self.GATE_EMPTY:
                    best_gate = check
        if best_gate == -1:
            best_gate = gate
        return best_gate, possible_gates

    def select_toolgate(self, widget, toolgate, param=0):
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])

        if toolgate == "tool":
            if param < 0 and self.ui_sel_tool > self.min_tool:
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
            if param < 0 and self.ui_sel_gate > (self.min_tool if self.ui_sel_tool == self.TOOL_BYPASS else 0):
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

    def update_toolgate_buttons(self, tool_sensitive=True):
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])

        # Set sensitivity of +/- buttons
        if not tool_sensitive:
            self.labels['t_decrease'].set_sensitive(False)
            self.labels['t_increase'].set_sensitive(False)
        else:
            if self.ui_sel_tool == self.min_tool:
                self.labels['t_decrease'].set_sensitive(False)
            else:
                self.labels['t_decrease'].set_sensitive(True)

            if self.ui_sel_tool == num_gates -1:
                self.labels['t_increase'].set_sensitive(False)
            else:
                self.labels['t_increase'].set_sensitive(True)

        if self.ui_sel_tool == self.TOOL_BYPASS or not tool_sensitive:
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

        if (self.ui_sel_tool == self.DUMMY or self.ui_sel_gate == self.DUMMY
                or self.ui_sel_loaded == self.DUMMY or self.ui_sel_tool == self.TOOL_UNKNOWN
                or self.ui_sel_gate == self.TOOL_UNKNOWN or not tool_sensitive):
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
            self.labels['filament'].set_label("Filament: Loaded")
            self.labels['filament'].set_active(True)
        elif self.ui_sel_loaded == 0:
            self.labels['filament'].set_label("Filament: Unloaded")
            self.labels['filament'].set_active(False)
        else:
            self.labels['filament'].set_label("Filament: Unknown")
            self.labels['filament'].set_active(False)

    def update_state_labels(self):
        ercf = self._printer.get_stat("ercf")
        tool = ercf['tool']
        gate = ercf['gate']
        filament = ercf['filament']

        tool_str = (f"T{tool}") if tool >= 0 else "Bypass" if tool == self.TOOL_BYPASS else "Unknown"
        gate_str = (f"#{gate}") if gate >= 0 else "Bypass" if gate == self.TOOL_BYPASS else "Unknown"
        self.labels['tool_label'].set_label(f"Tool: {tool_str}")
        self.labels['gate_label'].set_label(f"Gate: {gate_str}")
        self.labels['filament_label'].set_label(f"Filament: {filament}")

    def select_manual(self, widget):
        ercf = self._printer.get_stat("ercf")
        endless_spool = ercf['endless_spool']
        warning = ""
        loaded = "Loaded" if self.ui_sel_loaded == 1 else "Unloaded"
        if self.ui_sel_gate != self.TOOL_BYPASS:
            suggested_gate, possible_gates = self.get_possible_gates(self.ui_sel_tool)
            if self.ui_sel_gate != suggested_gate:
                warning = (f"\n\nSpecified gate may not the correct gate for T{self.ui_sel_tool}.\nProceed will update the TTG map and mark the gate available")
                if endless_spool and len (possible_gates) > 1:
                    warning += (f"\nEndlessSpool group includes gates: {possible_gates}")
            summary = (f"T{self.ui_sel_tool} on Gate #{self.ui_sel_gate} with filament {loaded}")
        else:
            self.ui_sel_gate = self.TOOL_BYPASS
            summary = (f"Bypass (on bypass gate) with filament {loaded}")

        sel_loaded = self.ui_sel_loaded
        if self.ui_sel_loaded == -1:
            sel_loaded = 0 # Assume unloaded
        self._screen._confirm_send_action(
            None,
            _("This will set the ERCF state to:\n\n" + summary + warning + "\n\nSure you want to continue?"),
            "printer.gcode.script",
            {'script': f"ERCF_RECOVER TOOL={self.ui_sel_tool} GATE={self.ui_sel_gate} LOADED={self.ui_sel_loaded}"}
        )

    def select_auto(self, widget):
        self._screen._confirm_send_action(
            None,
            _("This will automatically attempt to reset the ERCF filament state\n\nSure you want to continue?"),
            "printer.gcode.script",
            {'script': "ERCF_RECOVER"}
        )

    def select_reset(self, widget):
        self._screen._confirm_send_action(
            None,
            _("This will reset persisted ERCF state to defaults including\n\nTTG map, EndlessSpool groups, gate status and selector position\n\nSure you want to continue?"),
            "printer.gcode.script",
            {'script': "ERCF_RESET"}
        )

