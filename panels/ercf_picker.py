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

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_spacing(10)

        ercf = self._printer.get_stat("ercf")
        num_tools = len(ercf['gate_status'])
        for i in range(num_tools):
            status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            status = self.labels[f'status_{i}'] = self._gtk.Image()
            available = self.labels[f'available_{i}'] = Gtk.Label("Unknown")
            status_box.pack_start(status, True, True, 0)
            status_box.pack_start(available, True, True, 0)

            tool = self.labels[f'tool_{i}'] = self._gtk.Button('extruder', f'T{i}', 'color2')
            tool.connect("clicked", self.select_tool, i)

            color = self.labels[f'color_{i}'] = Gtk.Label(f'⬤')
            color.get_style_context().add_class("ercf_color_swatch")
            color.set_xalign(0.7)

            material = self.labels[f'material_{i}'] = Gtk.Label("n/a")
            material.get_style_context().add_class("ercf_material_text")
            material.set_xalign(0.1)

            gate_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            gate = self.labels[f'gate_{i}'] = Gtk.Label("n/a")
            gate.get_style_context().add_class("ercf_gate_text")
            gate.set_halign(Gtk.Align.START)
            gate.set_valign(Gtk.Align.END)
            alt_gates = self.labels[f'alt_gates_{i}'] = Gtk.Label("n/a")
            alt_gates.set_halign(Gtk.Align.START)
            alt_gates.set_valign(Gtk.Align.START)
            gate_box.pack_start(gate, True, True, 0)
            gate_box.pack_start(alt_gates, True, True, 0)

            grid.attach(status_box, 0, i, 3, 1)
            grid.attach(tool,       3, i, 3, 1)
            grid.attach(color,      6, i, 2, 1)
            grid.attach(material,   8, i, 3, 1)
            grid.attach(gate_box,  11, i, 5, 1)

        self.labels['unknown_icon'] = self._gtk.Image('ercf_unknown').get_pixbuf()
        self.labels['available_icon'] = self._gtk.Image('ercf_tick').get_pixbuf()
        self.labels['empty_icon'] = self._gtk.Image('ercf_cross').get_pixbuf()

        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(grid)
        self.content.add(scroll)

    def activate(self):
        ercf = self._printer.get_stat("ercf")
        endless_spool = ercf['endless_spool']
        tool_map = self.build_tool_map()
        gate_status = ercf['gate_status']
        gate_material = ercf['gate_material']
        gate_color = ercf['gate_color']
        num_tools = len(gate_status)

        for i in range(num_tools):
            t_map = tool_map[i]
            gate = t_map['gate']
            color = Gdk.RGBA()
            if not Gdk.RGBA.parse(color, gate_color[gate]):
                Gdk.RGBA.parse(color, '#' + gate_color[gate])

            gate_str = (f"Gate #{t_map['gate']}")
            alt_gate_str = ''
            if endless_spool == 1 and len(t_map['alt_gates']) > 0:
                alt_gate_str = '+(' + ', '.join(map(str, t_map['alt_gates'][:6]))
                alt_gate_str += ', ...)' if len(t_map['alt_gates']) > 6 else ')'

            if gate_status[gate] == 1:
                status_icon = 'available_icon'
                status_str = "Available"
            elif gate_status[gate] == 0:
                status_icon = 'empty_icon'
                status_str = "Empty"
            else: 
                status_icon = 'unknown_icon'
                status_str = "Unknown"

            self.labels[f'status_{i}'].clear()
            self.labels[f'status_{i}'].set_from_pixbuf(self.labels[f'{status_icon}'])
            self.labels[f'available_{i}'].set_label(status_str)
            self.labels[f'tool_{i}'].set_sensitive(gate_status[i] != self.GATE_EMPTY)
            self.labels[f'color_{i}'].override_color(Gtk.StateType.NORMAL, color)
            self.labels[f'material_{i}'].set_label(gate_material[gate][:6])
            self.labels[f'gate_{i}'].set_label(gate_str)
            self.labels[f'alt_gates_{i}'].set_label(alt_gate_str)


    # Structure is:
    # tool_map = [ { 'gate': <gate>, 'alt_gates': <alternative_gates> }, ... ]
    def build_tool_map(self):
        tool_map = []
        ercf = self._printer.get_stat("ercf")
        endless_spool_groups = ercf['endless_spool_groups']
        ttg_map = ercf['ttg_map']
        num_tools = len(ttg_map)
        for tool in range(num_tools):
            es_group = endless_spool_groups[tool]
            alt_gates = []
            for i in range(len(endless_spool_groups) - 1):
                alt = (tool + i + 1) % num_tools
                if endless_spool_groups[alt] == es_group:
                    alt_gates.append(alt)
            tool_map.append({ 'gate': ttg_map[tool], 'alt_gates': alt_gates })
        return tool_map

    def process_update(self, action, data):
        if action == "notify_status_update":
            if 'configfile' in data:
                return
            elif 'ercf' in data:
                e_data = data['ercf']
                if 'tool' in e_data or 'gate' in e_data or 'gate_status' in e_data or 'gate_material' in e_data or 'gate_color' in e_data:
                    self.activate()

    def select_tool(self, widget, selected_tool):
        ercf = self._printer.get_stat("ercf")
        tool = ercf['tool']
        filament = ercf['filament']
        if tool == self.TOOL_BYPASS and filament == "Loaded":
            # Should not of got here but do nothing for safety
            pass
        else:
            self._screen._ws.klippy.gcode_script(f"ERCF_CHANGE_TOOL TOOL={selected_tool}")
            self._screen._menu_go_back()

