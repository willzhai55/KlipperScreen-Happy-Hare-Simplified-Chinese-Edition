# Happy Hare ERCF Software
# Main ERCF management panel
#
# Copyright (C) 2023  moggieuk#6538 (discord)
#                     moggieuk@hotmail.com
#
import logging, gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return ErcfMain(*args)

class ErcfMain(ScreenPanel):
    TOOL_UNKNOWN = -1
    TOOL_BYPASS = -2

    GATE_UNKNOWN = -1
    GATE_EMPTY = 0
    GATE_AVAILABLE = 1

    DUMMY = -99

    def __init__(self, screen, title):
        super().__init__(screen, title)

        # We need to keep track of just a little bit of UI state
        self.ui_runout_mark = 0.
        self.ui_sel_tool = self.DUMMY

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
            'all':             ['check_gates', 'tool', 'eject', 'picker', 'pause', 'unlock', 'resume', 'manage', 'manage', 'more'],
            'printing':        [                                          'pause',                     'manage',           'more'],
            'paused':          ['check_gates', 'tool', 'eject', 'picker',          'unlock', 'resume', 'manage', 'manage', 'more'],
            'idle':            ['check_gates', 'tool', 'eject', 'picker', 'pause', 'unlock',           'manage', 'manage', 'more'],
            'locked':          [                                                   'unlock',                               'more'],
            'not_locked':      ['check_gates', 'tool', 'eject', 'picker', 'pause',           'resume', 'manage', 'manage', 'more'],
            'bypass_loaded':   [                       'eject',           'pause', 'unlock', 'resume', 'manage', 'manage', 'more'],
            'bypass_unloaded': ['check_gates', 'tool',          'picker', 'pause', 'unlock', 'resume', 'manage', 'manage', 'more'],
            'bypass_unknown':  ['check_gates', 'tool', 'eject', 'picker', 'pause', 'unlock', 'resume', 'manage', 'manage', 'more'],
            'tool_loaded':     ['check_gates', 'tool', 'eject', 'picker', 'pause', 'unlock', 'resume', 'manage', 'manage', 'more'],
            'tool_unloaded':   ['check_gates', 'tool',          'picker', 'pause', 'unlock', 'resume', 'manage', 'manage', 'more'],
            'tool_unknown':    ['check_gates', 'tool', 'eject', 'picker', 'pause', 'unlock', 'resume', 'manage', 'manage', 'more'],
            'disabled':        [                                                                                                      ],
        }

        self.labels = {
            'check_gates': self._gtk.Button('ercf_checkgates', _("Gates"), 'color1'),
            'manage': self._gtk.Button('ercf_manage', _("Manage..."),'color2'),
            't_decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'tool': self._gtk.Button('extruder', _('Load T0'), 'color2'),
            't_increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'picker': self._gtk.Button('ercf_tool_picker', _('Colors'), 'color3'),
            'eject': self._gtk.Button('ercf_eject', _('Eject'), 'color4'),
            'pause': self._gtk.Button('pause', _('Pause'), 'color1'),
            'unlock': self._gtk.Button('ercf_unlock', _('Unlock'), 'color2'),
            'resume': self._gtk.Button('resume', _('Resume'), 'color3'),
            'more': self._gtk.Button('ercf_gear', _('More...'), 'color4'),
            'tool_icon': self._gtk.Image('extruder', self._gtk.img_width * 0.8, self._gtk.img_height * 0.8),
            'tool_label': self._gtk.Label('Unknown'),
            'filament': self._gtk.Label('Filament: Unknown'),
            'select_bypass_img': self._gtk.Image('ercf_select_bypass'), # Alternative for tool
            'load_bypass_img': self._gtk.Image('ercf_load_bypass'),     # Alternative for picker
            'unload_bypass_img': self._gtk.Image('ercf_unload_bypass'), # Alternative for eject
        }
        self.labels['eject_img'] = self.labels['eject'].get_image()
        self.labels['tool_img'] = self.labels['tool'].get_image()
        self.labels['tool_picker_img'] = self.labels['picker'].get_image()

        self.labels['check_gates'].connect("clicked", self.select_check_gates)
        self.labels['manage'].connect("clicked", self.menu_item_clicked, "manage", {
            "panel": "ercf_manage", "name": _("ERCF Management")})
        self.labels['t_decrease'].connect("clicked", self.select_tool, -1)
        self.labels['tool'].connect("clicked", self.select_tool, 0)
        self.labels['t_increase'].connect("clicked", self.select_tool, 1)
        self.labels['picker'].connect("clicked", self.select_picker)
# PAUL        self.labels['picker'].connect("clicked", self.menu_item_clicked, "picker", {
# PAUL           "panel": "ercf_picker", "name": _("ERCF Tool Picker")})
        self.labels['eject'].connect("clicked", self.select_eject)
        self.labels['pause'].connect("clicked", self.select_pause)
        self.labels['unlock'].connect("clicked", self.select_unlock)
        self.labels['resume'].connect("clicked", self.select_resume)
        self.labels['more'].connect("clicked", self._screen._go_to_submenu, "ercf")

        self.labels['t_increase'].set_halign(Gtk.Align.START)
        self.labels['t_increase'].set_margin_start(10)
        self.labels['t_decrease'].set_halign(Gtk.Align.END)
        self.labels['t_decrease'].set_margin_end(10)

        self.labels['manage'].get_style_context().add_class("ercf_manage_button")
        self.labels['tool_icon'].get_style_context().add_class("ercf_tool_image")
        self.labels['tool_label'].get_style_context().add_class("ercf_tool_text")
        self.labels['tool_label'].set_xalign(0)
        self.labels['filament'].set_xalign(0)
        self.labels['manage'].set_valign(Gtk.Align.CENTER)

        scale = Gtk.Scale.new_with_range(orientation=Gtk.Orientation.VERTICAL, min=-30., max=0., step=0.1)
        self.labels['scale'] = scale
        scale.add_mark(0., Gtk.PositionType.RIGHT, f"0")
        scale.set_show_fill_level(True)
        scale.set_restrict_to_fill_level(False)
        scale.set_inverted(True)
        scale.set_value_pos(Gtk.PositionType.TOP)
        scale.set_digits(1)
        scale.set_can_focus(False)
        scale.get_style_context().add_class("ercf_runout")
        scale.connect("format_value", self._mm_format)

        runout_frame = Gtk.Frame()
        self.labels['runout_frame'] = runout_frame
        runout_frame.set_label(f"Clog")
        runout_frame.set_label_align(0.5, 0)
        runout_frame.add(scale)

        manage_grid = Gtk.Grid()
        manage_grid.set_column_homogeneous(True)
        manage_grid.set_row_homogeneous(True)
        manage_grid.attach(Gtk.Label(),           0, 0, 1, 3)
        manage_grid.attach(self.labels['manage'], 1, 0, 2, 3)

        runout_layer = Gtk.Notebook()
        self.labels['runout_layer'] = runout_layer
        runout_layer.set_show_tabs(False)
        runout_layer.insert_page(runout_frame, None, 0)
        runout_layer.insert_page(manage_grid, None, 1)
        
        # TextView has problems in this use case so use 5 separate labels... Simple!
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        for i in range(5):
            name = (f'status{i+1}')
            self.labels[name] = Gtk.Label("Gates: |#0 |#1 |#2 |#3 |#4 |#5 |#6 |#7 |#8 |")
            self.labels[name].get_style_context().add_class("ercf_status")
            self.labels[name].set_xalign(0)
            if i < 4:
                status_box.pack_start(self.labels[name], False, True, 0)
            else:
                self.labels[name].get_style_context().add_class("ercf_status_filament")

        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_box.pack_start(self.labels['tool_icon'], False, True, 0)
        top_box.pack_start(self.labels['tool_label'], True, True, 0)
        top_box.pack_start(self.labels['filament'], True, True, 0)

        top_grid = Gtk.Grid()
        top_grid.set_vexpand(False)
        top_grid.set_column_homogeneous(True)
        top_grid.attach(top_box,                0, 0,  9, 1)
        top_grid.attach(runout_layer,           9, 0,  3, 3)
        top_grid.attach(status_box,             0, 1, 10, 1)
        top_grid.attach(self.labels['status5'], 0, 2, 12, 1)

        tool_grid = Gtk.Grid()
        tool_grid.set_column_homogeneous(False)
        tool_grid.attach(self.labels['t_decrease'], 0, 0, 1, 1)
        tool_grid.attach(self.labels['tool'],       1, 0, 1, 1)
        tool_grid.attach(self.labels['t_increase'], 2, 0, 1, 1)

        middle_grid = Gtk.Grid()
        middle_grid.set_vexpand(True)
        middle_grid.set_column_homogeneous(True)
        middle_grid.attach(tool_grid,                  0, 0, 3, 1)
        middle_grid.attach(self.labels['picker'],      3, 0, 1, 1)
        middle_grid.attach(self.labels['eject'],       4, 0, 1, 1)
        middle_grid.attach(self.labels['check_gates'], 5, 0, 1, 1)

        lower_grid = Gtk.Grid()
        lower_grid.set_vexpand(True)
        lower_grid.set_column_homogeneous(True)
        lower_grid.attach(self.labels['pause'],  0, 0, 1, 1)
        lower_grid.attach(self.labels['unlock'], 1, 0, 1, 1)
        lower_grid.attach(self.labels['resume'], 2, 0, 1, 1)
        lower_grid.attach(self.labels['more'],   3, 0, 1, 1)

        self.content.pack_start(top_grid, False, True, 0)
        self.content.add(middle_grid)
        self.content.add(lower_grid)

    def activate(self):
        logging.info(f"PAUL ---- activate on ercf_main called")
        self.init_tool_value()
#        self.update_tool() PAUL is this needed?

    def process_update(self, action, data):
        if action == "notify_status_update":
            if 'ercf_encoder ercf_encoder' in data: # There is only one ercf_encoder
                ee_data = data['ercf_encoder ercf_encoder']
                self.update_encoder(ee_data)

            if 'ercf' in data:
                e_data = data['ercf']
                if 'tool' in e_data or 'gate' in e_data or 'ttg_map' in e_data or 'gate_status' in e_data:
                    self.update_status()
                if 'filament_visual' in e_data:
                    self.update_filament_status()
                if 'tool' in e_data or 'next_tool' in e_data:
                    self.update_tool(e_data)
                if 'enabled' in e_data:
                    self.update_enabled()
                if 'action' in e_data:
                    self.update_encoder_pos()

            if 'ercf' in data or 'pause_resume' in data:
                if 'ercf' in data: logging.info(f">>> ercf found")
                if 'pause_resume' in data: logging.info(f">>> pause_resume found")
                self.update_active_buttons()
            elif 'print_stats' in data and 'state' in data['print_stats']:
                logging.info(f">>> print_stats found")
                self.update_active_buttons()

    def init_tool_value(self):
        ercf = self._printer.get_stat("ercf")
        if self.ui_sel_tool == self.DUMMY and ercf['tool'] >= 0:
            self.ui_sel_tool = ercf['tool']
        else:
            self.ui_sel_tool = 0

    def _mm_format(self, w, v):
        return f"{-v:.1f}mm"

    def select_check_gates(self, widget):
        self._screen._confirm_send_action(
            None,
            _("Check filament availabily in all ERCF gates?\n\nAre you sure you want to continue?"),
            "printer.gcode.script",
            {'script': "ERCF_CHECK_GATES"}
        )

    def select_tool(self, widget, param=0):
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])
        tool = ercf['tool']
        if param < 0 and self.ui_sel_tool > self.min_tool:
            self.ui_sel_tool -= 1
            if self.ui_sel_tool == self.TOOL_UNKNOWN:
                self.ui_sel_tool = self.TOOL_BYPASS
        elif param > 0 and self.ui_sel_tool < num_gates - 1:
            self.ui_sel_tool += 1
            if self.ui_sel_tool == self.TOOL_UNKNOWN:
                self.ui_sel_tool = 0
        elif param == 0:
            if self.ui_sel_tool == self.TOOL_BYPASS:
                self._screen._ws.klippy.gcode_script(f"ERCF_SELECT_BYPASS")
            elif self.ui_sel_tool != tool or ercf['filament'] != "Loaded":
                self._screen._ws.klippy.gcode_script(f"T{self.ui_sel_tool}")
            return
        self.update_tool_buttons()

    def select_eject(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_EJECT")

    def select_picker(self, widget):
        # This is a multipurpose button to select subpanel or load bypass
        ercf = self._printer.get_stat("ercf")
        tool = ercf['tool']
        if self.ui_sel_tool == self.TOOL_BYPASS:
            self._screen._ws.klippy.gcode_script(f"ERCF_LOAD_BYPASS")
        else:
            self._screen.show_panel('picker', 'ercf_picker', _("ERCF Tool Picker"), 1, False)
#            self.show_panel('picker', 'ercf_picker', _("ERCF Tool Picker"), 2, False)
#    def show_panel(self, panel_name, panel_type, title, remove=None, pop=True, **kwargs):

    def select_pause(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_PAUSE FORCE_IN_PRINT=1")

    def select_unlock(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_UNLOCK")

    def select_resume(self, widget):
        self._screen._ws.klippy.gcode_script(f"RESUME")

    def update_enabled(self):
        logging.info(f"@@@************@@@ PAUL: update_enabled")
        enabled = self._printer.get_stat("ercf")['enabled']
        for i in range(5):
            name = (f'status{i+1}')
            if enabled:
                self.labels[name].get_style_context().remove_class("ercf_disabled_text")
            else:
                self.labels[name].get_style_context().add_class("ercf_disabled_text")

    def update_tool(self, data=None):
        logging.info(f"@@@************@@@ PAUL: update_tool")
        ercf = self._printer.get_stat("ercf")
        tool = ercf['tool']
        next_tool = ercf['next_tool']
        text = ("T%d" % tool) if tool >= 0 else "Bypass" if tool == -2 else "Unknown"
        text += (" > T%d" % next_tool) if next_tool >= 0 and next_tool != tool else ""
        self.labels['tool_label'].set_text(text)
        if data != None and 'tool' in data:
            if tool == self.TOOL_BYPASS:
                self.labels['eject'].set_image(self.labels['unload_bypass_img'])
                self.labels['eject'].set_label(f"Unload")
            else:
                self.labels['eject'].set_image(self.labels['eject_img'])
                self.labels['eject'].set_label(f"Eject")

    def update_tool_buttons(self, tool_sensitive=True):
        logging.info(f"@@@************@@@ PAUL: update_tool_buttons")
        printer_state = self._printer.get_stat("print_stats")['state']
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])
        tool = ercf['tool']
        filament = ercf['filament']
        enabled = ercf['enabled']
        action = ercf['action']
        locked = ercf['is_locked']

        # Set sensitivity of +/- buttons
        if (tool == self.TOOL_BYPASS and filament != "Unloaded") or not tool_sensitive:
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

        # Set load button image and text
        if action == "Idle":
            if self.ui_sel_tool >= 0:
                self.labels['tool'].set_label(f"T{self.ui_sel_tool}")
                if ercf['tool'] == self.ui_sel_tool and filament == "Loaded":
                    self.labels['tool'].set_sensitive(False)
                else:
                    self.labels['tool'].set_sensitive(True)
            elif self.ui_sel_tool == self.TOOL_BYPASS:
                self.labels['tool'].set_label(f"Bypass")
                self.labels['tool'].set_sensitive(True)
            else:
                self.labels['tool'].set_label(f"n/a")
                self.labels['tool'].set_sensitive(True)
        else:
            self.labels['tool'].set_label(action)

        if self.ui_sel_tool == self.TOOL_BYPASS:
            self.labels['tool'].set_image(self.labels['select_bypass_img'])
            self.labels['picker'].set_image(self.labels['load_bypass_img'])
            self.labels['picker'].set_label(f"Load") # PAUL test me
        else:
            self.labels['tool'].set_image(self.labels['tool_img'])
            self.labels['picker'].set_image(self.labels['tool_picker_img'])

    def update_encoder(self, data):
        logging.info(f"@@@************@@@ PAUL: update_encoder")
        scale = self.labels['scale']
        if 'desired_headroom' in data:
            desired_headroom = data['desired_headroom']
            if self.ui_runout_mark != desired_headroom:
                self.ui_runout_mark = desired_headroom
                scale.clear_marks()
                scale.add_mark(-desired_headroom, Gtk.PositionType.RIGHT, f"{desired_headroom}")
        if 'detection_length' in data:
            scale.set_range(-data['detection_length'], 0.)
        if 'min_headroom' in data:
            scale.set_fill_level(-data['min_headroom'])
        if 'headroom' in data:
            scale.set_value(-data['headroom'])
        if 'detection_mode' in data:
            self.update_runout_mode(data['detection_mode'])
        if 'encoder_pos' in data:
            self.update_encoder_pos(data['encoder_pos'])

    def update_runout_mode(self, detection_mode):
        logging.info(f"@@@************@@@ PAUL: update_runout_mode")
        detection_mode_str = " (Auto)" if detection_mode == 2 else " (Man)" if detection_mode == 1 else ""
        self.labels['runout_frame'].set_label(f'Clog{detection_mode_str}')
        self.labels['runout_frame'].set_sensitive(detection_mode)

    def update_encoder_pos(self, encoder_pos=None):
        logging.info(f"@@@************@@@ PAUL: update_encoder_pos")
        if encoder_pos == None:
            encoder_pos = self._printer.get_stat('ercf_encoder ercf_encoder')['encoder_pos']
        ercf = self._printer.get_stat("ercf")
        filament = ercf['filament']
        action = ercf['action']
        if action == "Idle" or action == "Busy":
            pos_str = (f"Filament: {encoder_pos}mm") if filament != "Unloaded" else "Filament: Unloaded"
        elif action == "Loading" or action == "Unloading":
            pos_str = (f"{action}: {encoder_pos}mm")
        else:
            pos_str = (f"{action}")
        self.labels['filament'].set_label(f"{pos_str}")

    def update_filament_status(self):
        logging.info(f"@@@************@@@ PAUL: update_filament_status")
        filament_visual = self._printer.get_stat("ercf")['filament_visual']
        self.labels['status5'].set_label(filament_visual)

    def update_status(self):
        logging.info(f"@@@************@@@ PAUL: update_status")
        text, multi_tool = self.get_status_text() # PAUL multi_tool flag not yet used
        for i in range(4):
            name = (f'status{i+1}')
            self.labels[name].set_label(text[i])

    # Dynamically update button sensitivity based on state
    def update_active_buttons(self):
        logging.info(f"@@@************@@@ PAUL: update_active_buttons()")
        ercf = self._printer.get_stat("ercf")
        printer_state = self._printer.get_stat("print_stats")['state']
        locked = ercf['is_locked']
        is_paused = self._printer.get_stat("pause_resume")['is_paused']
        enabled = ercf['enabled']
        tool = ercf['tool']
        filament = ercf['filament']
        logging.info(f"*-*-*-* printer_state={printer_state}, locked={locked}, is_paused={is_paused}, enabled={enabled}, tool={tool}, filament={filament}")
        ui_state = []
        if enabled:
            if printer_state == "paused" or is_paused:
                ui_state.append("paused")
            elif printer_state == "printing":
                ui_state.append("printing")
            else:
                ui_state.append("idle")
            ui_state.append("locked" if locked else "not_locked")
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

            if "printing" in ui_state:
                self.labels['runout_layer'].set_current_page(0) # Clog display
            else:
                self.labels['runout_layer'].set_current_page(1) # Recovery
        else:
            ui_state.append("disabled")
            self.labels['runout_layer'].set_current_page(0)
            self.labels['t_increase'].set_sensitive(False)
            self.labels['t_decrease'].set_sensitive(False)

        logging.info(f"*-*-*-* >>>>> ui_state={ui_state}")
        for label in self.btn_states['all']:
            sensitive = True
            for state in ui_state:
                if not label in self.btn_states[state]:
                    sensitive = False
                    break
            logging.info(f"*-*-*-* >>>>> {label} > {sensitive}")
            if sensitive:
                self.labels[label].set_sensitive(True)
            else:
                self.labels[label].set_sensitive(False)
            if label == "tool":
                self.update_tool_buttons(sensitive)

    def get_status_text(self):
        ercf = self._printer.get_stat("ercf")
        gate_status = ercf['gate_status']
        tool_to_gate_map = ercf['ttg_map']
        gate_selected = ercf['gate']
        tool_selected = ercf['tool']
        num_gates = len(gate_status)

        multi_tool = False
        msg_gates = "Gates: "
        msg_tools = "Tools: "
        msg_avail = "Avail: "
        msg_selct = "Selct: "
        for g in range(num_gates):
            msg_gates += ("|#%d " % g)[:4]
            msg_avail += "| %s " % ("*" if gate_status[g] == self.GATE_AVAILABLE else " " if gate_status[g] == self.GATE_EMPTY else "?")
            tool_str = ""
            prefix = ""
            for t in range(num_gates):
                if tool_to_gate_map[t] == g:
                    if len(prefix) > 0: multi_tool = True
                    tool_str += "%sT%d" % (prefix, t)
                    prefix = "+"
            if tool_str == "": tool_str = " . "
            msg_tools += ("|%s " % tool_str)[:4]
            if gate_selected == g:
                icon = "*" if gate_status[g] == self.GATE_AVAILABLE else " " if gate_status[g] == self.GATE_EMPTY else "?"
                msg_selct += ("| %s " % icon)
            else:
                msg_selct += "|---" if gate_selected != self.GATE_UNKNOWN and gate_selected == (g - 1) else "----"
        msg_gates += "|"
        msg_tools += "|"
        msg_avail += "|"
        msg_selct += "|" if gate_selected == (num_gates - 1) else "-"
        msg = [msg_gates, msg_tools, msg_avail, msg_selct]
        return [msg_gates, msg_tools, msg_avail, msg_selct], multi_tool

