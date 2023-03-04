# Happy Hare ERCF Software
# Main ERCF management panel
#
# Copyright (C) 2022  moggieuk#6538 (discord)
#
import logging, gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return ErcfPanel(*args)


class ErcfPanel(ScreenPanel):
    TOOL_UNKNOWN = -1
    TOOL_BYPASS = -2

    GATE_UNKNOWN = -1
    GATE_EMPTY = 0
    GATE_AVAILABLE = 1

    def __init__(self, screen, title):
        super().__init__(screen, title)

        # We need to keep track of just a little bit of UI state
        self.ui_runout_mark = 0.
        self.ui_sel_tool = 0
        # btn_states: the "gaps" are what functionality the state takes away
        self.btn_states = {
            'all':             ['check_gates', 'tool', 'eject', 'load_bypass', 'pause', 'unlock', 'resume', 'manage', 'recover'],
            'printing':        [                                               'pause',                     'manage',          ],
            'paused':          ['check_gates', 'tool', 'eject', 'load_bypass',          'unlock', 'resume', 'manage', 'recover'],
            'idle':            ['check_gates', 'tool', 'eject', 'load_bypass', 'pause', 'unlock',           'manage', 'recover'],
            'not_locked':      ['check_gates', 'tool', 'eject', 'load_bypass', 'pause',           'resume', 'manage', 'recover'],
            'bypass_loaded':   [                       'eject',                'pause', 'unlock', 'resume', 'manage', 'recover'],
            'bypass_unloaded': ['check_gates', 'tool',          'load_bypass', 'pause', 'unlock', 'resume', 'manage', 'recover'],
            'bypass_unknown':  ['check_gates', 'tool', 'eject', 'load_bypass', 'pause', 'unlock', 'resume', 'manage', 'recover'],
            'tool_loaded':     ['check_gates', 'tool', 'eject',                'pause', 'unlock', 'resume', 'manage', 'recover'],
            'tool_unloaded':   ['check_gates', 'tool',                         'pause', 'unlock', 'resume', 'manage', 'recover'],
            'tool_unknown':    ['check_gates', 'tool', 'eject', 'load_bypass', 'pause', 'unlock', 'resume', 'manage', 'recover'],
            'disabled':        [                                                                                                         ],
        }

        self.labels = {
            'check_gates': self._gtk.Button('ercf_checkgates', _("Chk. Gates")), # PAUL todo, add confirmation
            'recover': self._gtk.Button('ercf_recover', _("Recover")),
            't_decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'tool': self._gtk.Button('extruder', _('Load T0'), 'color2'),
            't_increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'load_bypass': self._gtk.Button('ercf_load_bypass', _('Load'), 'color3'),
            'eject': self._gtk.Button('ercf_eject', _('Eject'), 'color4'),
            'pause': self._gtk.Button('pause', _('Pause'), 'color1'),
            'unlock': self._gtk.Button('ercf_unlock', _('Unlock'), 'color2'),
            'resume': self._gtk.Button('resume', _('Resume'), 'color3'),
            'manage': self._gtk.Button('ercf_gear', _('Manage...'), 'color4'),
            'tool_icon': self._gtk.Image('extruder', self._gtk.img_width * 0.8, self._gtk.img_height * 0.8),
            'tool_label': self._gtk.Label('Unknown'),
            'filament': self._gtk.Label('Filament: Unknown'),
            'select_bypass_img': self._gtk.Image('ercf_select_bypass'),
            'load_bypass_img': self._gtk.Image('ercf_load_bypass'),
            'unload_bypass_img': self._gtk.Image('ercf_unload_bypass'),
        }
        self.labels['eject_img'] = self.labels['eject'].get_image()
        self.labels['tool_img'] = self.labels['tool'].get_image()

        self.labels['check_gates'].connect("clicked", self.select_check_gates)
        self.labels['recover'].connect("clicked", self.menu_item_clicked, "recover", {
            "panel": "ercf_recover", "name": _("ERCF State Recovery")})
        self.labels['t_decrease'].connect("clicked", self.select_tool, -1)
        self.labels['tool'].connect("clicked", self.select_tool, 0)
        self.labels['t_increase'].connect("clicked", self.select_tool, 1)
        self.labels['load_bypass'].connect("clicked", self.select_load_bypass)
        self.labels['eject'].connect("clicked", self.select_eject)
        self.labels['pause'].connect("clicked", self.select_pause)
        self.labels['unlock'].connect("clicked", self.select_unlock)
        self.labels['resume'].connect("clicked", self.select_resume)
        self.labels['manage'].connect("clicked", self._screen._go_to_submenu, "ercf")

        self.labels['t_increase'].set_halign(Gtk.Align.START)
        self.labels['t_increase'].set_margin_start(10)
        self.labels['t_decrease'].set_halign(Gtk.Align.END)
        self.labels['t_decrease'].set_margin_end(10)

        self.labels['tool_label'].get_style_context().add_class("ercf_tool_text")
        self.labels['tool_label'].set_xalign(0)
        self.labels['filament'].set_xalign(0)

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

        runout_layer = Gtk.Notebook()
        self.labels['runout_layer'] = runout_layer
        runout_layer.set_show_tabs(False)
        runout_layer.insert_page(runout_frame, None, 0)
        runout_layer.insert_page(self.labels['recover'], None, 1)
        
        status_tb = Gtk.TextBuffer()
        status_tv = Gtk.TextView()
        self.labels.update({
            "status_tb": status_tb,
            "status_tv": status_tv
        })
        status_tv.set_vexpand(True)
        status_tv.set_buffer(status_tb)
        status_tv.set_editable(False)
        status_tv.set_cursor_visible(False)
        status_tv.set_sensitive(False)

        status_window = Gtk.ScrolledWindow()
        status_window.set_hexpand(False)
        status_window.add(status_tv)

        filament_tb = Gtk.TextBuffer()
        filament_tv = Gtk.TextView()
        self.labels.update({
            "filament_tb": filament_tb,
            "filament_tv": filament_tv
        })
        filament_tv.set_vexpand(False)
        filament_tv.set_buffer(filament_tb)
        filament_tv.set_editable(False)
        filament_tv.set_cursor_visible(False)
        filament_tv.set_sensitive(False)
        filament_tv.get_style_context().add_class("ercf_status_filament")

        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_box.pack_start(self.labels['tool_icon'], False, True, 0)
        top_box.pack_start(self.labels['tool_label'], True, True, 0)
        top_box.pack_start(self.labels['filament'], True, True, 0)

        top_grid = Gtk.Grid()
        top_grid.set_vexpand(True)
        top_grid.set_column_homogeneous(True)
        top_grid.attach(top_box,                    0, 0, 8,  1)
        top_grid.attach(self.labels['check_gates'], 8, 0, 2,  3)
        top_grid.attach(runout_layer,              10, 0, 2,  3)
        top_grid.attach(status_window,              0, 1, 10, 1)
        top_grid.attach(self.labels['filament_tv'], 0, 2, 12, 1)

        middle_grid = Gtk.Grid()
        middle_grid.set_vexpand(True)
        middle_grid.set_column_homogeneous(True)
        middle_grid.attach(self.labels['t_decrease'],  0, 0, 1, 1)
        middle_grid.attach(self.labels['tool'],        1, 0, 1, 1)
        middle_grid.attach(self.labels['t_increase'],  2, 0, 1, 1)
        middle_grid.attach(self.labels['load_bypass'], 3, 0, 1, 1)
        middle_grid.attach(self.labels['eject'],       4, 0, 1, 1)
        middle_grid.attach(Gtk.Label("TODO"),          5, 0, 1, 1)

        lower_grid = Gtk.Grid()
        lower_grid.set_vexpand(True)
        lower_grid.set_column_homogeneous(True)
        lower_grid.attach(self.labels['pause'],  0, 0, 1, 1)
        lower_grid.attach(self.labels['unlock'], 1, 0, 1, 1)
        lower_grid.attach(self.labels['resume'], 2, 0, 1, 1)
        lower_grid.attach(self.labels['manage'], 3, 0, 1, 1)

        self.content.add(top_grid)
        self.content.add(middle_grid)
        self.content.add(lower_grid)

    def activate(self):
        logging.info(f"++++ PAUL: avtivate() called. Nothing to do yet!")
        self.ui_sel_tool = self._printer.get_stat("ercf")['tool']
        self.update_status()
        self.update_filament_status()
        self.update_tool()
        self.update_tool_buttons()
        self.update_active_buttons()
#        self.update_encoder_pos() ? PAUL not possible as implemented
#        self.update_encoder() ? PAUL not possible as implemented

        # PAUL maybe move check gates button depending on num_games

    def process_update(self, action, data):
        if action == "notify_gcode_response":
            # if data.startswith('// ERCF ['):
            pass

        elif action == "notify_status_update":
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
                    self.update_tool_buttons()

            if 'ercf' in data or 'pause_resume' in data or 'print_stats' in data:
                if 'ercf' in data: logging.info(f">>> ercf found")
                if 'pause_resume' in data: logging.info(f">>> pause_resume found")
                if 'print_stats' in data: logging.info(f">>> print_stats found")
                self.update_active_buttons()

#                # Dynamically update button sensitivity based on state
#                ercf = self._printer.get_stat("ercf")
#                printer_state = self._printer.get_stat("print_stats")['state']
#                locked = ercf['is_locked']
#                is_paused = self._printer.get_stat("pause_resume")['is_paused']
#                enabled = ercf['enabled']
#                tool = ercf['tool']
#                filament = ercf['filament']
#                logging.info(f"*-*-*-* printer_state={printer_state}, locked={locked}, is_paused={is_paused}, enabled={enabled}, tool={tool}, filament={filament}")
#                ui_state = []
#                if enabled:
#                    if printer_state == "paused" or is_paused:
#                        ui_state.append("paused")
#                    elif printer_state == "printing":
#                        ui_state.append("printing")
#                    else:
#                        ui_state.append("idle")
#                    if locked:
#                        ui_state.append("locked")
#
#                    if tool == self.TOOL_BYPASS:
#                        if filament == "Loaded":
#                            ui_state.append("bypass_loaded")
#                        elif filament == "Unloaded":
#                            ui_state.append("bypass_unloaded")
#                        else:
#                            ui_state.append("bypass_unknown")
#                    elif tool >= 0:
#                        if filament == "Loaded":
#                            ui_state.append("tool_loaded")
#                        elif filament == "Unloaded":
#                            ui_state.append("tool_unloaded")
#                        else:
#                            ui_state.append("tool_unknown")
#                    if "printing" in ui_state:
#                        self.labels['runout_layer'].set_current_page(0) # Clog display
#                    else:
#                        self.labels['runout_layer'].set_current_page(1) # Recovery
#                else:
#                    ui_state.append("disabled")
#                    self.labels['runout_layer'].set_current_page(0)
#                    self.labels['t_increase'].set_sensitive(False)
#                    self.labels['t_decrease'].set_sensitive(False)
#    
#                logging.info(f"*-*-*-* >>>>> ui_state={ui_state}")
#                for label in self.btn_states['all']:
#                    enabled = True
#                    for state in ui_state:
#                        if not label in self.btn_states[state]:
#                            enabled = False
#                            break
#                    if enabled:
#                        self.labels[label].set_sensitive(True)
#                    else:
#                        self.labels[label].set_sensitive(False)

    def _mm_format(self, w, v):
        return f"{-v:.1f}mm"

    def select_check_gates(self, widget):
        self._screen._confirm_send_action(
            None,
            _("Check filament availabily in all ERCF gates?"),
            "printer.gcode.script",
            {'script': "ERCF_CHECK_GATES"}
        )

    def select_tool(self, widget, param=0):
        logging.info(f"PAUL - select_tool()")
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])
        tool = ercf['tool']
        filament = ercf['filament']
        if param < 0 and self.ui_sel_tool > -2:
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
                self.labels['tool'].set_label(f"Loading")
                logging.info(f"PAUL - TODO label set to Loading")
                self._screen._ws.klippy.gcode_script(f"T{self.ui_sel_tool}")
            return
        self.update_tool_buttons()

    def update_tool_buttons(self):
        logging.info(f"PAUL --------------------------------------- update_tool_buttons()")
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])
        tool = ercf['tool']
        filament = ercf['filament']
        enabled = ercf['enabled']
        action = ercf['action']
        if (tool == self.TOOL_BYPASS and filament != "Unloaded") or not enabled:
            self.labels['t_decrease'].set_sensitive(False)
            self.labels['t_increase'].set_sensitive(False)
        else:
            if self.ui_sel_tool == self.TOOL_BYPASS:
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
            elif self.ui_sel_tool == self.TOOL_BYPASS:
                self.labels['tool'].set_label(f"Bypass")
            else:
                self.labels['tool'].set_label(f"n/a")
        else:
            self.labels['tool'].set_label(action)

        if self.ui_sel_tool == self.TOOL_BYPASS:
            self.labels['tool'].set_image(self.labels['select_bypass_img'])
        else:
            self.labels['tool'].set_image(self.labels['tool_img'])

    def select_eject(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_EJECT")

    def select_load_bypass(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_LOAD_BYPASS")

    def select_pause(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_PAUSE")

    def select_unlock(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_UNLOCK")

    def select_resume(self, widget):
        self._screen._ws.klippy.gcode_script(f"RESUME")

    def update_enabled(self):
        enabled = self._printer.get_stat("ercf")['enabled']
        if enabled:
            pass
# PAUL TODO
#            self.labels['status_tv'].get_style_context().remove_class("ercf_status_look_inactive")
#            self.labels['filament_tv'].get_style_context().remove_class("ercf_status_look_inactive")
        else:
            pass
#            self.labels['status_tv'].get_style_context().add_class("ercf_status_look_inactive")
#            self.labels['filament_tv'].get_style_context().add_class("ercf_status_look_inactive")

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
        #logging.info(f"@@@************@@@ PAUL: update_encoder_pos")
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
        self.labels['filament_tb'].set_text(filament_visual)

    def update_status(self):
        logging.info(f"@@@************@@@ PAUL: update_status")
        text, multi_tool = self.get_status_text() # PAUL multi_tool flag not yet used
        self.labels['status_tb'].set_text(text)

    # Dynamically update button sensitivity based on state
    def update_active_buttons(self):
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
            if not locked:
                ui_state.append("not_locked")

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
            enabled = True
            for state in ui_state:
                if not label in self.btn_states[state]:
                    enabled = False
                    break
            if enabled:
                self.labels[label].set_sensitive(True)
            else:
                self.labels[label].set_sensitive(False)

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
        msg = ""
        for g in range(num_gates):
            msg_gates += ("|#%d " % g)[:4]
            msg_avail += "| %s " % ("*" if gate_status[g] == self.GATE_AVAILABLE else "." if gate_status[g] == self.GATE_EMPTY else "?")
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
                icon = "*" if gate_status[g] == self.GATE_AVAILABLE else "." if gate_status[g] == self.GATE_EMPTY else "?"
                msg_selct += ("| %s " % icon)
            else:
                msg_selct += "|---" if gate_selected != self.GATE_UNKNOWN and gate_selected == (g - 1) else "----"
        msg += msg_gates
        msg += "|\n"
        msg += msg_tools
        msg += "|\n"
        msg += msg_avail
        msg += "|\n"
        msg += msg_selct
        msg += "|\n" if gate_selected == (num_gates - 1) else "-\n"
        return msg, multi_tool

