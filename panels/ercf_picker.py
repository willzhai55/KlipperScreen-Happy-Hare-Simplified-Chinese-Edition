# Happy Hare ERCF Software
# Display and selection of tools based on color and material
#
# Copyright (C) 2023  moggieuk#6538 (discord)
#                     moggieuk@hotmail.com
#
import logging, gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Pango, Gdk
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return ErcfPicker(*args)

class ErcfPicker(ScreenPanel):
    TOOL_UNKNOWN = -1
    TOOL_BYPASS = -2

    GATE_UNKNOWN = -1
    GATE_EMPTY = 0
    GATE_AVAILABLE = 1

    DUMMY = -99

    def __init__(self, screen, title):
        super().__init__(screen, title)

        self.init_tool_map()

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_spacing(10)

        ercf = self._printer.get_stat("ercf")
        num_tools = len(ercf['gate_status'])
        endless_spool = ercf['endless_spool']
        gate_map = ercf['gate_map']
        for i in range(num_tools):
            t_map = self.tool_map[i]
            g_map = gate_map[t_map['gate']]
            logging.info(f"@@@************@@@ PAUL: i={i}, t_map={t_map}, g_map={g_map}")
            color = Gdk.RGBA()
            Gdk.RGBA.parse(color, g_map['color'])

            gate_str = (f"Gate #{t_map['gate']}")
            alt_gate_str = ''
            if endless_spool == 1 and len(t_map['alt_gates']) > 0:
                alt_gate_str = '+(' + ', '.join(map(str, t_map['alt_gates'][:5]))
                alt_gate_str += ', ...)' if len(t_map['alt_gates']) > 5 else ')'

            if g_map['available'] == 1:
                status_icon = 'ercf_tick'
                status_str = "Available"
            elif g_map['available'] == 0:
                status_icon = 'ercf_cross'
                status_str = "Empty"
            else: 
                status_icon = 'ercf_unknown'
                status_str = "Unknown"

            status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            status = self.labels[f'status_{i}'] = self._gtk.Image(status_icon)
            available = self.labels[f'available_{i}'] = Gtk.Label(status_str)
            status_box.pack_start(status, True, True, 0)
            status_box.pack_start(available, True, True, 0)

            tool = self.labels[f'tool_{i}'] = self._gtk.Button('extruder', '', 'color1')
            tool.connect("clicked", self.select_tool)
            tool.override_background_color(Gtk.StateType.NORMAL, color)

            name = self.labels[f'name_{i}'] = Gtk.Label(f'T{i}')
            name.get_style_context().add_class("ercf_tool_text")
            name.set_xalign(0.5)

            material = self.labels[f'material_{i}'] = Gtk.Label(g_map['material'][:5])
            material.get_style_context().add_class("ercf_tool_text")
            material.set_xalign(0.2)

            gate_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            gate = self.labels[f'gate_{i}'] = Gtk.Label(gate_str)
            gate.get_style_context().add_class("ercf_gate_text")
            gate.set_halign(Gtk.Align.START)
            gate.set_valign(Gtk.Align.END)
            alt_gates = self.labels[f'alt_gates_{i}'] = Gtk.Label(alt_gate_str)
            alt_gates.set_halign(Gtk.Align.START)
            alt_gates.set_valign(Gtk.Align.START)
            gate_box.pack_start(gate, True, True, 0)
            gate_box.pack_start(alt_gates, True, True, 0)

            grid.attach(status_box, 0, i, 2, 1)
            grid.attach(name,       2, i, 2, 1)
            grid.attach(tool,       4, i, 2, 1)
            grid.attach(material,   6, i, 3, 1)
            grid.attach(gate_box,   9, i, 4, 1)

        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(grid)
        self.content.add(scroll)

    def activate(self):
        self.init_tool_map()

    def init_tool_map(self):
        # WORK IN PROGRESS. REPLACEMENT FOR ENDLESS SPOOL GROUPS
        # TODO Build this structure from existing endless_spool_groups
        self.tool_map = [
                { 'gate': 0, 'alt_gates': [3, 6] },
                { 'gate': 1, 'alt_gates': [2, 3, 4, 5, 6, 7, 8] },
                { 'gate': 2, 'alt_gates': []     },
                { 'gate': 3, 'alt_gates': []     },
                { 'gate': 4, 'alt_gates': []     },
                { 'gate': 5, 'alt_gates': []     },
                { 'gate': 6, 'alt_gates': []     },
                { 'gate': 7, 'alt_gates': []     },
                { 'gate': 8, 'alt_gates': []     }
            ]

    def process_update(self, action, data):
        if action == "notify_status_update":
            if 'ercf' in data:
                e_data = data['ercf']
                if 'tool' in e_data or 'gate' in e_data or 'gate_status' in e_data or 'gate_map' in e_data:
                    pass
                    # This doesn't work because of intial call will all the data. Maybe determine base on size of data and ignore first..
                    #self._screen._menu_go_back() # We don't support dynamic updates on this screen so just go back

    def select_tool(self, widget):
        ercf = self._printer.get_stat("ercf")
        tool = ercf['tool']
        filament = ercf['filament']
        if tool == self.TOOL_BYPASS and filament == "Loaded":
            # Should not of got here but do nothing for safety
            pass
        else:
            self._screen._ws.klippy.gcode_script(f"T{tool}")
            self._screen._menu_go_back()

