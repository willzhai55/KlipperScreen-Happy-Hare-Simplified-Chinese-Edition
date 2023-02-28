import logging, gi
import random # PAUL

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
        self.runout_mark = 0.
        self.ui_tool = 0

        self.labels = {
            'check_gates': self._gtk.Button('ercf_checkgates', _("Chk. Gates")),
            'pause': self._gtk.Button('pause', _('Pause'), 'color1'),
            'unlock': self._gtk.Button('ercf_unlock', _('Unlock'), 'color2'),
            'resume': self._gtk.Button('resume', _('Resume'), 'color3'),
            'manage': self._gtk.Button('ercf_gear', _('Manage...'), 'color4'),
            'decrease': self._gtk.Button('decrease', None, scale=self.bts * 1.2),
            'tool': self._gtk.Button('extruder', _('Load T0'), 'color2'),
            'increase': self._gtk.Button('increase', None, scale=self.bts * 1.2),
            'eject': self._gtk.Button('ercf_eject', _('Eject'), 'color3'),
            'bypass': self._gtk.Button('ercf_bypass', _('Sel. Bypass'), 'color4'),
            'load_bypass': self._gtk.Button('ercf_load_bypass', _('Load'), 'color4'),
            'tool_icon': self._gtk.Image('extruder', self._gtk.img_width * 0.8, self._gtk.img_height * 0.8),
            'tool_label': self._gtk.Label(f'Unknown'),
            'filament': self._gtk.Label(f'Filament: Unknown')
        }

        self.labels['check_gates'].connect("clicked", self.dummy)
        self.labels['decrease'].connect("clicked", self.select_tool, -1)
        self.labels['tool'].connect("clicked", self.select_tool, 0)
        self.labels['increase'].connect("clicked", self.select_tool, 1)
        self.labels['eject'].connect("clicked", self.select_eject)
        self.labels['pause'].connect("clicked", self.select_pause)
        self.labels['unlock'].connect("clicked", self.select_unlock)
        self.labels['resume'].connect("clicked", self.dummy)
        self.labels['manage'].connect("clicked", self._screen._go_to_submenu, "ercf")
#        self.labels['manage'].connect("clicked", self.select_manage)
        self.labels['bypass'].connect("clicked", self.select_bypass)
        self.labels['load_bypass'].connect("clicked", self.select_load_bypass)

        self.labels['increase'].set_halign(Gtk.Align.START)
        self.labels['increase'].set_margin_start(10)
        self.labels['decrease'].set_halign(Gtk.Align.END)
        self.labels['decrease'].set_margin_end(10)

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
        runout_frame.set_vexpand(True)
        runout_frame.set_label(f"Clog")
        runout_frame.set_label_align(0.5, 0)
        runout_frame.add(scale)

        status_tb = Gtk.TextBuffer()
        status_tv = Gtk.TextView()
        self.labels.update({
            "status_tb": status_tb,
            "status_tv": status_tv
        })
        status_tv.set_vexpand(False)
        status_tv.set_hexpand(False)
        status_tv.set_buffer(status_tb)
        status_tv.set_editable(False)
        status_tv.set_cursor_visible(False)
        status_tv.set_sensitive(False)

        filament_tb = Gtk.TextBuffer()
        filament_tv = Gtk.TextView()
        self.labels.update({
            "filament_tb": filament_tb,
            "filament_tv": filament_tv
        })
        filament_tv.set_vexpand(False)
        filament_tv.set_hexpand(False)
        filament_tv.set_buffer(filament_tb)
        filament_tv.set_editable(False)
        filament_tv.set_cursor_visible(False)
        filament_tv.set_sensitive(False)
        filament_tv.get_style_context().add_class("ercf_status_filament")

        status_window = Gtk.ScrolledWindow()
        status_window.set_vexpand(True)
        status_window.add(status_tv)

        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_box.pack_start(self.labels['tool_icon'], False, True, 0)
        top_box.pack_start(self.labels['tool_label'], True, True, 0)
        top_box.pack_start(self.labels['filament'], True, True, 0)

        top_grid = Gtk.Grid()
        top_grid.set_column_homogeneous(True)
        top_grid.attach(top_box,                    0, 0, 8, 1)
        top_grid.attach(self.labels['check_gates'], 8, 0, 2, 2)
        top_grid.attach(runout_frame,              10, 0, 2, 3)
        top_grid.attach(status_window,              0, 1, 8, 1)
#        top_grid.attach(self.labels['check_gates'], 8, 1, 2, 1)
        top_grid.attach(self.labels['filament_tv'], 0, 2, 10, 1)
        top_grid.attach(Gtk.Label(" "),             0, 3, 12, 1)

        middle_grid = Gtk.Grid()
        middle_grid.set_column_homogeneous(True)
        middle_grid.set_vexpand(False)
        middle_grid.attach(self.labels['decrease'],    0, 0, 1, 1)
        middle_grid.attach(self.labels['tool'],        1, 0, 1, 1)
        middle_grid.attach(self.labels['increase'],    2, 0, 1, 1)
        middle_grid.attach(self.labels['eject'],       3, 0, 1, 1)
        middle_grid.attach(self.labels['bypass'],      4, 0, 1, 1)
        middle_grid.attach(self.labels['load_bypass'], 5, 0, 1, 1)

        lower_grid = Gtk.Grid()
        lower_grid.set_column_homogeneous(True)
        lower_grid.set_vexpand(False)
        lower_grid.attach(self.labels['pause'],  0, 0, 1, 1)
        lower_grid.attach(self.labels['unlock'], 1, 0, 1, 1)
        lower_grid.attach(self.labels['resume'], 2, 0, 1, 1)
        lower_grid.attach(self.labels['manage'], 3, 0, 1, 1)

        self.content.add(top_grid)
        self.content.add(middle_grid)
        self.content.add(Gtk.Label(" "))
        self.content.add(lower_grid)

    def activate(self):
        logging.info(f"++++ PAUL: avtivate() called")

    def process_update(self, action, data):
        if action == "notify_gcode_response":
            pass
# This method works but assumes user has logging enabled
#            if data.startswith('// ERCF ['):
#                self.update_filament_pos(data[3:])
#                self.labels['filament_tb'].set_text(text[:s.rfind('\n')]) # Replace last line

        elif action == "notify_status_update":
            if 'ercf_encoder ercf_encoder' in data: # There is only one ercf_encoder
                ee_data = data['ercf_encoder ercf_encoder']
                self.update_encoder(ee_data)

            if 'ercf' in data:
                e_data = data['ercf']
                if 'tool' in e_data or 'gate' in e_data or 'ttg_map' in e_data or 'gate_status' in e_data:
                    self.update_status()
                if 'filament_visual' in e_data:
                    self.update_filament_status(e_data['filament_visual'])
                if 'enabled' in e_data:
                    # Deactivate or activate everything..
                    logging.info(f"+++++ PAUL: ENABLED")
#                    self.labels['status_frame'].set_sensitive(e_data['enabled'])
#                    self.labels['status_tv'].set_sensitive(e_data['enabled'])
                    self.labels['status_tv'].get_style_context().add_class("ercf_status_look_active")
# EXAMPLE of class removal                self.devices[device]['name'].get_style_context().remove_class(self.devices[device]['class'])
                    # PAUL
                if 'tool' in e_data:
                    self.tool = e_data['tool']
                if 'next_tool' in e_data:
                    self.next_tool = e_data['next_tool']
                if 'gate' in e_data:
                    self.gate = e_data['gate']
                if 'tool' in e_data or 'next_tool' in e_data:
                    self.update_tool(e_data)

#            if 'is_locked' in e_data:
#                if e_data['is_locked']:
#                    for i in 'increase', 'tool', 'decrease', 'eject', 'check_gates', 'pause', 'resume':
#                        self.labels[i].set_sensitive(True)
#                else:
#                    for i in 'increase', 'tool', 'decrease', 'eject', 'check_gates', 'unlock', 'resume':
#                        self.labels[i].set_sensitive(False)
#                    for i in 'increase', 'tool', 'decrease', 'eject', 'check_gates', 'unlock', 'resume':
#                        self.labels[i].set_sensitive(False)

    def _mm_format(self, w, v):
        return f"{-v:.1f}mm"

    def select_tool(self, widget, param=0):
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['gate_status'])
        tool = ercf['tool']
        if param < 0 and self.ui_tool > 0:
            self.ui_tool -= 1
            self.labels['tool'].set_label(f"Load T{self.ui_tool}")
        elif param > 0 and self.ui_tool < num_gates - 1:
            self.ui_tool += 1
            self.labels['tool'].set_label(f"Load T{self.ui_tool}")
        elif param == 0:
            if self.ui_tool != tool:
                self.labels['tool'].set_label(f"Loading")
            self._screen._ws.klippy.gcode_script(f"T{self.ui_tool}")

    def select_eject(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_EJECT")

    def select_bypass(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_SELECT_BYPASS")

    def select_load_bypass(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_LOAD_BYPASS")

    def select_pause(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_PAUSE")

    def select_unlock(self, widget):
        self._screen._ws.klippy.gcode_script(f"ERCF_UNLOCK")

    def select_unlock(self, widget):
        self._screen._ws.klippy.gcode_script(f"RESUME")

    def select_manage(self, widget):
        pass
#        self.menu_item_clicked, "gcode_macros", {
#            "name": "Macros",
#            "panel": "gcode_macros"
#        })
#        #self._screen.show_panel('ercf', "menu", None, 0, items=self._config.get_menu_items("__main actions ercf"))
#        itms=self._config.get_menu_items(menu="__main", subsection="actions")
#        self._screen.show_panel('ercf', "menu", None, 2, items=itms)

    def update_paused_locked(self, data):
        # PAUL TODO
        pass

    def update_paused(self, data):
        # PAUL TODO
        pass

    def update_printing(self, data):
        # PAUL TODO
        pass

    def update_idle(self, data):
        # PAUL TODO
        pass

    def update_tool(self, data):
        logging.info(f"@@@************@@@ PAUL: update_tool")
        ercf = self._printer.get_stat("ercf")
        tool = ercf['tool']
        next_tool = ercf['next_tool']
        text = ("T%d" % tool) if tool >= 0 else "Bypass" if tool == -2 else "Unknown"
        text += (" > T%d" % next_tool) if next_tool >= 0 and next_tool != tool else ""
        self.labels['tool_label'].set_text(text)
        if 'tool' in data:
            self.labels['tool'].set_label(f"Load T{self.ui_tool}")

    def update_encoder(self, data):
        logging.info(f"@@@************@@@ PAUL: update_encoder")
        scale = self.labels['scale']
        if 'desired_headroom' in data:
            desired_headroom = data['desired_headroom']
            if self.runout_mark != desired_headroom:
                self.runout_mark = desired_headroom
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

    def update_encoder_pos(self, encoder_pos):
        logging.info(f"@@@************@@@ PAUL: update_encoder_pos")
        ercf = self._printer.get_stat("ercf")
        filament = ercf['filament']
        pos_str = (f"{encoder_pos}mm") if filament != "Unloaded" else filament
        self.labels['filament'].set_label(f'Filament: {pos_str}')

    def update_filament_status(self, filament_visual):
        logging.info(f"@@@************@@@ PAUL: update_filament_status")
        self.labels['filament_tb'].set_text(filament_visual)

    def update_status(self):
        logging.info(f"@@@************@@@ PAUL: update_status")
        text, multi_tool = self.get_status_text() # PAUL multi_tool not yet used
        self.labels['status_tb'].set_text(text)

    def get_status_text(self):
        ercf = self._printer.get_stat("ercf")
        gate_status = ercf['gate_status']
        tool_to_gate_map = ercf['ttg_map']
        gate_selected = ercf['gate']
        tool_selected = ercf['tool']
        num_gates = len(gate_status)

        # This is pulled from Happy Hare driver and modified to reduce long lines
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
        #msg += "|%s\n" % (" Some gates support multiple tools!" if multi_tool else "") # PAUL highlight another way with HTML formating?
        msg += msg_avail
        msg += "|\n"
        msg += msg_selct
        msg += "|\n" if gate_selected == (num_gates - 1) else "-\n"
#        msg += ercf['filament_visual']
        return msg, multi_tool





# PAUL vvv testing
    def dummy(self, widget, param=None):
        logging.info(f"PAUL: dummy param={param}")
#        r = random.random() * 23
#        if r < self.min_headroom:
#            self.min_headroom = r
#        data = {'encoder_pos': 4546.3,
#                'desired_headroom': 5.5,
#                'detection_length': 23,
#                'min_headroom': self.min_headroom,
#                'headroom': r
#        }
#        self.update_runout(data)

