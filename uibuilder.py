import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QGroupBox, QVBoxLayout


def get_indent_level(line):
    spaces = re.match(r'\s*', line)
    if spaces:
        return len(spaces[0]) / 4
    return 0


def parse_line(line):
    def next_match(reg, text):
        match = re.search(reg, text)
        if match:
            m = match.group(1)
            return m, text[len(match.group(0)):]
        return None, text

    indent = get_indent_level(line)
    line = line.strip()
    name, line = next_match(r'(\w+)', line)
    id, line = next_match(r'#([\w\-_\d]+)\b', line)
    class_name, line = next_match(r'\.([\w\-_\d]*)', line)

    attrs = {}
    attr_match, line = next_match(r'\((.*)\)', line)
    if attr_match:
        for attr in attr_match.split(r'\s*,\s*'):
            key, val = attr.split('=')
            attrs[key] = val

    text, line = next_match(r' ([\w -]*)', line)
    return indent, name, id, class_name, attrs, text


class UIBuilder:
    def __init__(self, widget, raw):
        # ignore all comments and blank lines
        self.raw = [line for line in raw.split('\n') if not re.match(r'(\s*//)|(\s*$)', line)]
        self.top = widget
        self.widgets_by_id = {}
        self.widgets_by_class = []
        self.parse(self.top, 0, self.raw)

    def by_id(self, id):
        return self.widgets_by_id[id]

    def by_class(self, class_name):
        return [w['widget'] for w in self.widgets_by_class if w['class'] == class_name]

    def set_text(self, id, text):
        widget = self.by_id(id)

        if hasattr(widget, 'setText'):
            widget.setText(text)
        else:
            widget.setTitle(text)

    def set_stylesheet(self, id, ss):
        widget = self.by_id(id)
        widget.setStyleSheet(ss)
        self.top.style().unpolish(widget)
        self.top.style().polish(widget)

    def create(self, widget_name):
        if widget_name == 'QHBoxLayout':
            return QHBoxLayout()
        elif widget_name == 'QVBoxLayout':
            return QVBoxLayout()
        elif widget_name == 'QLabel':
            return QLabel()
        elif widget_name == 'QGroupBox':
            return QGroupBox()

    def parse(self, parent, level, lines):
        last_line = None
        skipping_children = False
        for index, line in enumerate(lines):
            indent, widget_name, id, class_name, attrs, text = parse_line(line)

            if indent < level:  # done with this block
                return
            elif indent > level:  # need to add children to the previous created widget or layout
                if not skipping_children:
                    skipping_children = True
                    self.parse(last_line, indent, lines[index:])
                continue
            elif skipping_children and level == indent:  # done skipping past children we've already parsed
                skipping_children = False

            if widget_name == 'stretch':
                parent.addStretch()
            else:
                w = self.create(widget_name)
                last_line = w
                if id:
                    w.setObjectName(id)
                    self.widgets_by_id[id] = w
                if class_name:
                    self.widgets_by_class.append({
                        "widget": w,
                        "class": class_name
                    })
                if attrs:
                    if 'align' in attrs:
                        alignments = {
                            "left": Qt.AlignLeft,
                            "right": Qt.AlignRight,
                            "hcenter": Qt.AlignHCenter
                        }
                        w.setAlignment(alignments[attrs['align']])
                if text:
                    if hasattr(w, 'setText'):
                        w.setText(text)
                    else:
                        w.setTitle(text)

                # add this widget to the parent
                if 'layout' in widget_name.lower():
                    if hasattr(parent, 'addLayout'):
                        parent.addLayout(w)
                    else:
                        parent.setLayout(w)
                else:
                    parent.addWidget(w)
