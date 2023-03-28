# Happy Hare ERCF Software
# Display and editing of TTG map and endless spool groups
#
# Copyright (C) 2023  moggieuk#6538 (discord)
#                     moggieuk@hotmail.com
#
import logging, gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Pango, Gdk
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return ErcfToolmap(*args)

class ErcfToolmap(ScreenPanel):

    #        0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15
    box =  [' ', '╵', '╶', '└', '╷', '│', '┌', '├', '╴', '┘', '─', '┴', '┐', '┤', '┬', '┼']
    box += ['╹', '╹', '┖', '┖', '╿', '╿', '┞', '┞', '┚', '┚', '┸', '┸', '┦', '┦', '╀', '╀'] # ╹ 16
    box += ['╺', '┕', '╺', '┕', '┍', '┝', '┍', '┝', '╼', '┶', '╼', '┶', '┮', '┾', '┮', '┾'] # ╺ 32
    box += ['┗', '┗', '┗', '┗', '┡', '┡', '┡', '┡', '┺', '┺', '┺', '┺', '╄', '╄', '╄', '╄'] # ┗ 48
    box += ['╻', '╽', '┎', '┟', '╻', '╽', '┎', '┟', '┒', '┧', '┰', '╁', '┒', '┧', '┰', '╁'] # ╻ 64
    box += ['┃', '┃', '┠', '┠', '┃', '┃', '┠', '┠', '┨', '┨', '╂', '╂', '┨', '┨', '╂', '╂'] # ┃ 80
    box += ['┏', '┢', '┏', '┢', '┏', '┢', '┏', '┢', '┲', '╆', '┲', '╆', '┲', '╆', '┲', '╆'] # ┏ 96
    box += ['┣', '┣', '┣', '┣', '┣', '┣', '┣', '┣', '╊', '╊', '╊', '╊', '╊', '╊', '╊', '╊'] # ┣ 112
    box += ['╸', '┙', '╾', '┵', '┑', '┥', '┭', '┽', '┙', '┙', '╾', '┵', '┑', '┥', '┭', '┽'] # ╸ 128
    box += ['┛', '┛', '┹', '┹', '┩', '┩', '╃', '╃', '┛', '┛', '┹', '┹', '┩', '┩', '╃', '╃'] # ┛ 144
    box += ['━', '┷', '━', '┷', '┯', '┿', '┯', '┿', '━', '┷', '━', '┷', '┯', '┿', '┯', '┿'] # ━ 160
    box += ['┻', '┻', '┻', '┻', '╇', '╇', '╇', '╇', '┻', '┻', '┻', '┻', '╇', '╇', '╇', '╇'] # ┻ 176
    box += ['┓', '┪', '┓', '╅', '┓', '┪', '┱', '╅', '┓', '┪', '┱', '╅', '┓', '┪', '┱', '╅'] # ┓ 192
    box += ['┫', '┫', '╉', '╉', '┫', '┫', '╉', '╉', '┫', '┫', '╉', '╉', '┫', '┫', '╉', '╉'] # ┫ 208
    box += ['┳', '╈', '┳', '╈', '┳', '╈', '┳', '╈', '┳', '╈', '┳', '╈', '┳', '╈', '┳', '╈'] # ┳ 224
    box += ['╂', '╂', '╂', '╂', '╂', '╂', '╂', '╂', '╂', '╂', '╂', '╂', '╂', '╂', '╂', '╂'] # ╋ 240 (+crossover)
    #box += ['╋', '╋', '╋', '╋', '╋', '╋', '╋', '╋', '╋', '╋', '╋', '╋', '╋', '╋', '╋', '╋'] # ╋ 240 (accurate)
    box += ['▫', '▻', '▣', '►', '▶', '▪']

    def __init__(self, screen, title):
        super().__init__(screen, title)

        # We need to keep track of just a little bit of UI state
        self.ui_sel_tool = self.ui_sel_es_group = 0
        self.ui_endless_spool_groups = self.ui_ttg_map = None

        ercf = self._printer.get_stat("ercf")
        num_tools = len(ercf['gate_status'])

        self.labels = {
            't_decrease': self._gtk.Button('decrease', None, 'color1', scale=self.bts * 1.2),
            'tool': self._gtk.Label("T0"),
            't_increase': self._gtk.Button('increase', None, 'color2', scale=self.bts * 1.2),
            'g_decrease': self._gtk.Button('decrease', None, 'color1', scale=self.bts * 1.2),
            'gate': self._gtk.Label("#0"),
            'g_increase': self._gtk.Button('increase', None, 'color2', scale=self.bts * 1.2),
            'save': self._gtk.Button('ercf_save', 'Save', 'color3'),
            'es_decrease': self._gtk.Button('decrease', None, scale=self.bts * 0.6),
            'es_group': self._gtk.Label("EndlessSpool - Editing ES Group: A"),
            'es_increase': self._gtk.Button('increase', None, scale=self.bts * 0.6),
            'reset': self._gtk.Button('refresh', 'Reset', scale=self.bts, position=Gtk.PositionType.LEFT, lines=1),
        }

        self.labels['t_decrease'].connect("clicked", self.select_toolgate, 'tool', -1)
        self.labels['t_increase'].connect("clicked", self.select_toolgate, 'tool', 1)
        self.labels['g_decrease'].connect("clicked", self.select_toolgate, 'gate', -1)
        self.labels['g_increase'].connect("clicked", self.select_toolgate, 'gate', 1)
        self.labels['es_decrease'].connect("clicked", self.select_es, -1)
        self.labels['es_increase'].connect("clicked", self.select_es, 1)
        self.labels['save'].connect("clicked", self.select_reset_save, "save")
        self.labels['reset'].connect("clicked", self.select_reset_save, "reset")

        self.labels['tool'].get_style_context().add_class("ercf_tool_text")
        self.labels['gate'].get_style_context().add_class("ercf_gate_text")
        self.labels['es_decrease'].get_style_context().add_class("ercf_es_gate")
        self.labels['es_increase'].get_style_context().add_class("ercf_es_gate")
        self.labels['save'].set_vexpand(False)
        self.labels['save'].set_hexpand(False)
        self.labels['reset'].set_halign(Gtk.Align.CENTER)
        self.labels['reset'].set_valign(Gtk.Align.START)
        self.labels['reset'].set_vexpand(False)

        tool_grid = Gtk.Grid()
        tool_grid.set_row_homogeneous(True)
        tool_grid.set_vexpand(False)

        tool_grid.attach(self.labels['t_decrease'], 0, 0, 1, 1)
        tool_grid.attach(self.labels['tool'],       0, 1, 1, 1)
        tool_grid.attach(self.labels['t_increase'], 0, 2, 1, 1)

        gate_grid = Gtk.Grid()
        gate_grid.set_row_homogeneous(True)
        gate_grid.set_vexpand(False)

        gate_grid.attach(self.labels['g_decrease'], 0, 0, 1, 1)
        gate_grid.attach(self.labels['gate'],       0, 1, 1, 1)
        gate_grid.attach(self.labels['g_increase'], 0, 2, 1, 1)

        ttg_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        ttg_box.set_valign(Gtk.Align.CENTER)
        ttg_box.set_halign(Gtk.Align.CENTER)
        for i in range(num_tools):
            name = (f'toolmap{i}')
            self.labels[name] = Gtk.Label()
            self.labels[name].get_style_context().add_class("ercf_status")
            self.labels[name].set_xalign(0)
            ttg_box.pack_start(self.labels[name], False, True, 0)

        es_flowbox = Gtk.FlowBox(orientation=Gtk.Orientation.HORIZONTAL)
        es_flowbox.set_vexpand(False)
        for i in range(num_tools):
            g = self.labels[f'es_gate{i}'] = self._gtk.Button(label=str(i))
            g.connect("clicked", self.select_es_gate, int(i))
            g.get_style_context().add_class("ercf_es_gate")
            es_flowbox.add(g)

        es_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        es_box.set_vexpand(False)
        es_box.pack_start(self.labels['es_decrease'], False, True, 0)
        es_box.pack_start(self.labels['es_increase'], False, True, 0)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)

        top_pad = Gtk.Box()
        top_pad.set_vexpand(True)
        mid_pad = Gtk.Box()
        mid_pad.set_vexpand(True)

        save_box = Gtk.Box()
        save_box.pack_start(self.labels['save'], True, True, 20)

        grid.attach(top_pad,                  0, 0, 14, 1)
        grid.attach(Gtk.Box(),                0, 1,  1, 1)
        grid.attach(tool_grid,                1, 1,  2, 2)
        grid.attach(ttg_box,                  3, 1,  8, 1)
        grid.attach(gate_grid,               11, 1,  2, 2)
        grid.attach(Gtk.Box(),               13, 1,  1, 1)
        grid.attach(self.labels['reset'],     3, 2,  8, 1)
        grid.attach(mid_pad,                  0, 3, 14, 1)
        grid.attach(es_box,                   0, 4,  2, 3)
        grid.attach(self.labels['es_group'],  2, 4,  9, 1)
        grid.attach(save_box,                11, 4,  3, 3)
        grid.attach(es_flowbox,               2, 5,  9, 2)

        scroll = self._gtk.ScrolledWindow()
        scroll.add(grid)
        self.content.add(scroll)

    def activate(self, param=0):
        ercf = self._printer.get_stat("ercf")
        self.ui_ttg_map = ercf['ttg_map']
        self.ui_endless_spool_groups = self.map_unique_groups(ercf['endless_spool_groups'])
        self.ui_sel_es_group = self.ui_endless_spool_groups[self.ui_ttg_map[self.ui_sel_tool]]
        self.update_map()
        self.update_es_group()

    def map_unique_groups(self, groups):
        unique_groups = list(set(groups))
        unique_groups.sort()
        mapping = {group: index for index, group in enumerate(unique_groups)}
        return [mapping[group] for group in groups]

    def first_empty_groups(self, groups):
        unique_groups = list(set(groups))
        unique_groups.sort()
        group = 0
        while group in unique_groups:
            group += 1
        return group

    def convert_number_to_letter(self, number):
        if number >= 0:
            return chr(ord('A') + number)
        else:
            return '?'

    def build_es_spool_gate_group(self, es_group):
        gates = []
        for g in range(len(self.ui_endless_spool_groups)):
            if self.ui_endless_spool_groups[g] == es_group:
                gates.append(g)
        return gates

    def gen_map(self, htool=-1, hgate=-1):
        num_gates = len(self.ui_ttg_map)
        tool_map = [[0 for y in range(num_gates)] for x in range(num_gates+4)]
    
        for tool in range(num_gates):
            gate = self.ui_ttg_map[tool]
            bold = 16 if (gate == hgate or tool == htool) else 1
            y = tool
            tool_map[0][tool] |= 256 | (bold >> 3)
            for x in range(tool+1):
                tool_map[x+1][y] = tool_map[x+1][y] | (10 * bold)
            if gate == tool:
                tool_map[tool+2][y] = tool_map[tool+2][y] | (10 * bold)
            else:
                if gate > tool:
                    tool_map[tool+2][y] = tool_map[tool+2][y] | (12 * bold)
                    dir = 1
                else:
                    tool_map[tool+2][y] = tool_map[tool+2][y] | (9 * bold)
                    dir = -1
                for y in range(tool + dir, tool + (gate - tool), dir):
                    tool_map[tool+2][y] = tool_map[tool+2][y] | (5 * bold)
                if gate > tool:
                    tool_map[tool+2][y+1] = tool_map[tool+2][y+1] | (3 * bold)
                else:
                    tool_map[tool+2][y-1] = tool_map[tool+2][y-1] | (6 * bold)
            for x in range(tool+3, num_gates+3):
                tool_map[x][gate] = tool_map[x][gate] | (10 * bold)
            tool_map[num_gates+3][gate] |= 257 | (bold >> 3)
        return tool_map

    def update_map(self):
        tool = self.ui_sel_tool
        gate = self.ui_ttg_map[tool]
        es_group = self.ui_endless_spool_groups[self.ui_ttg_map[self.ui_sel_tool]]
        gates_in_group = self.build_es_spool_gate_group(es_group)

        self.labels['tool'].set_text(f"T{tool}")
        tool_map = self.gen_map(htool=tool, hgate=-1)
        grp = '╸' if len(gates_in_group) == 1 else '┓' + ('┫' * (len(gates_in_group) - 2)) + '┛'
        cnt = 0
        for y in range(len(tool_map[0])):
            msg = (f"T{y}  ")[:4]
            for x in range(len(tool_map)):
                msg += self.box[tool_map[x][y]]
            msg += (f" Gate #{y}  ")[:10]
            if y in gates_in_group:
                msg += grp[cnt]
                cnt = (cnt + 1) if cnt < (len(grp) - 1) else 0
                msg += self.convert_number_to_letter(es_group) if cnt == 1 or len(grp) == 1 else ""
            else:
                msg += ' ' if cnt == 0 else '┃'
            self.labels[f'toolmap{y}'].set_text(msg)
        self.labels[f'es_gate{gate}'].get_style_context().add_class("distbutton_active")
        self.labels['tool'].set_label(f"T{tool}")
        self.labels['gate'].set_label(f"Gate #{gate}")

    def update_es_group(self):
        gates_in_group = self.build_es_spool_gate_group(self.ui_sel_es_group)
        for g in range(len(self.ui_ttg_map)):
            if g in gates_in_group:
                self.labels[f"es_gate{g}"].get_style_context().add_class("distbutton_active")
            else:
                self.labels[f"es_gate{g}"].get_style_context().remove_class("distbutton_active")
        grp = self.convert_number_to_letter(self.ui_sel_es_group)
        self.labels['es_group'].set_label(f"EndlessSpool - Editing ES Group: {grp}")

    def process_update(self, action, data):
        if action == "notify_status_update":
            if 'configfile' in data:
                return
            elif 'ercf' in data:
                e_data = data['ercf']
                if 'ttg_map' in e_data or 'endless_spool_groups' in e_data:
                    self.activate()

    def select_toolgate(self, widget, toolgate, param=0):
        ercf = self._printer.get_stat("ercf")
        num_gates = len(ercf['ttg_map'])

        if toolgate == "tool":
            if param < 0 and self.ui_sel_tool > 0:
                self.ui_sel_tool -= 1
            elif param > 0 and self.ui_sel_tool < num_gates - 1:
                self.ui_sel_tool += 1
        else:
            if param < 0 and self.ui_ttg_map[self.ui_sel_tool] > 0:
                self.ui_ttg_map[self.ui_sel_tool] -= 1
            elif param > 0 and self.ui_ttg_map[self.ui_sel_tool] < num_gates - 1:
                self.ui_ttg_map[self.ui_sel_tool] += 1

        self.ui_sel_es_group = self.ui_endless_spool_groups[self.ui_ttg_map[self.ui_sel_tool]]
        self.update_map()
        self.update_es_group()

    def select_es(self, widget, param=0):
        ercf = self._printer.get_stat("ercf")
        max_grp_number = len(ercf['ttg_map'])

        if param < 0 and self.ui_sel_es_group > 0:
            self.ui_sel_es_group -= 1
        elif param > 0 and self.ui_sel_es_group < max_grp_number - 1:
            self.ui_sel_es_group += 1

        self.update_es_group()

    def select_es_gate(self, widget, gate):
        if self.ui_endless_spool_groups[gate] == self.ui_sel_es_group:
            self.ui_endless_spool_groups[gate] = self.first_empty_groups(self.ui_endless_spool_groups)
        else:
            self.ui_endless_spool_groups[gate] = self.ui_sel_es_group

        self.update_map()
        self.update_es_group()

    def select_reset_save(self, widget, action):
        label = Gtk.Label()
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.CENTER)
        label.set_vexpand(True)
        label.set_valign(Gtk.Align.CENTER)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        if action == "reset":
            label.set_text("This will reset the TTG map and EndlessSpool groups\n\nto the default defined in your ERCF configuration\n\nAre you sure you want to continue?")
        else:
            label.set_text("This will set the ERCF TTG map and ALL EndlessSpool groups\n\nto the configuration defined on this panel\n\nAre you sure you want to continue?")

        grid = self._gtk.HomogeneousGrid()
        grid.attach(label, 0, 0, 1, 1)
        buttons = [
            {"name": _("Apply"), "response": Gtk.ResponseType.APPLY},
            {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
        ]
        dialog = self._gtk.Dialog(self._screen, buttons, grid, self.reset_save_confirm, action)
        dialog.set_title(_("Confirm TTG/EndlessSpool Reset"))

    def reset_save_confirm(self, dialog, response_id, action):
        self._gtk.remove_dialog(dialog)
        if response_id == Gtk.ResponseType.APPLY:
            if action == "reset":
                self._screen._ws.klippy.gcode_script(f"ERCF_REMAP_TTG RESET=1 QUIET=1")
                self._screen._ws.klippy.gcode_script(f"ERCF_ENDLESS_SPOOL RESET=1 QUIET=1")
            else:
                ttg_map=",".join(map(str,self.ui_ttg_map))
                groups=",".join(map(str,self.ui_endless_spool_groups))
                self._screen._ws.klippy.gcode_script(f"ERCF_REMAP_TTG MAP={ttg_map} QUIET=1")
                self._screen._ws.klippy.gcode_script(f"ERCF_ENDLESS_SPOOL GROUPS={groups} QUIET=1")

