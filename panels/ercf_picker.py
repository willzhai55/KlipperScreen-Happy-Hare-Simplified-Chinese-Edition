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

        #
        # WORK IN PROGRESS.  EXPERIMENTAL LAYOUT FOR FEEDBACK
        #
        tool_map = [
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

        # Color string notes:
        # A standard name (Taken from the X11 rgb.txt file)
        # A hexadecimal value in the form “#rgb”, “#rrggbb”, “#rrrgggbbb” or ”#rrrrggggbbbb”
        # A RGB color in the form “rgb(r,g,b)” (In this case the color will have full opacity)
        # A RGBA color in the form “rgba(r,g,b,a)”
        # (last two cases, r/g/b are from 0-255 or % value, a is in the range 0 to 1.
        gate_map = [
                { 'material': 'PLA',  'color': 'red',     'status': 1  },
                { 'material': 'ABS',  'color': 'lt_grey', 'status': 1  },
                { 'material': 'PLA+', 'color': 'green',   'status': 1  },
                { 'material': 'ABS',  'color': '#1010FF', 'status': -1 },
                { 'material': 'ABS',  'color': 'cyan',    'status': 1  },
                { 'material': 'ABS',  'color': 'black',   'status': 0  },
                { 'material': 'ABS',  'color': 'grey',    'status': 0  },
                { 'material': 'ABS',  'color': 'white',   'status': 1  },
                { 'material': 'ABS',  'color': 'pink',    'status': 1  }
            ]

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_spacing(10)

        ercf = self._printer.get_stat("ercf")
        num_tools = len(ercf['gate_status'])
        endless_spool = ercf['endless_spool']
        for i in range(num_tools):
            t_map = tool_map[i]
            g_map = gate_map[t_map['gate']]
            logging.info(f"@@@************@@@ PAUL: i={i}, t_map={t_map}, g_map={g_map}")
            color = Gdk.RGBA()
            Gdk.RGBA.parse(color, g_map['color'])

            gate_str = (f"Gate #{t_map['gate']}")
            alt_gate_str = ''
            if endless_spool == 1 and len(t_map['alt_gates']) > 0:
                alt_gate_str = '+(' + ', '.join(map(str, t_map['alt_gates'][:5]))
                alt_gate_str += ', ...)' if len(t_map['alt_gates']) > 5 else ')'

            if g_map['status'] == 1:
                status_icon = 'ercf_tick'
                status_str = "Available"
            elif g_map['status'] == 0:
                status_icon = 'ercf_cross'
                status_str = "Unavailable"
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

            material = self.labels[f'material_{i}'] = Gtk.Label(g_map['material'])
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

            grid.attach(status_box, 0, i+1, 2, 1)
            grid.attach(name,       2, i+1, 2, 1)
            grid.attach(tool,       4, i+1, 2, 1)
            grid.attach(material,   6, i+1, 3, 1)
            grid.attach(gate_box,   9, i+1, 4, 1)

        grid.attach(Gtk.Label("Shhhhh.... INGORE THIS PANEL IT IS WIP :-)"), 0, 0, 12, 1) # WIP

        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(grid)
        self.content.add(scroll)

    def activate(self):
        pass

    def process_update(self, action, data):
        if action == "notify_status_update":
            if 'ercf' in data:
                e_data = data['ercf']
                if 'tool' in e_data or 'gate' in e_data or 'gate_status' in e_data:
                    pass
                    # This doesn't work because of intial call during activate
                    #self._screen._menu_go_back() # We don't support dynamic updates on this screen

    def select_tool(self, widget):
        logging.info(f"PAUL ---- select_tool")
        pass

