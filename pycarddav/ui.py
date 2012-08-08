#!/usr/bin/env python
# vim: set ts=4 sw=4 expandtab sts=4:
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <geier@lostpackets.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return Christian Geier
# ----------------------------------------------------------------------------
"""
The pycarddav interface to add, edit, or select a VCard.
"""

from __future__ import print_function

try:
    import sys
    import urwid

except ImportError, error:
    print(error)
    sys.exit(1)


class SelText(urwid.Text):
    """
    Selectable Text with an aditional href varibale
    """
    def __init__(self, text, href):
        urwid.Text.__init__(self, text)
        self.href = href

    def selectable(self):
        """needs to be implemented"""
        return True

    def keypress(self, _, key):
        """needs to be implemented"""
        return key


class SelectedButton(Exception):
    def __init__(self, exit_token=None):
        Exception.__init__(self)
        self.exit_token = exit_token


class Selected(Exception):
    """
    used for signalling that an item was chosen in urwid
    """
    pass


def edit(card):
    """proper edit"""

    def buttons():
        def save_button_callback(button):
            raise SelectedButton(exit_token='Save')
        savebutton = urwid.Button('OK', on_press=save_button_callback)

        def cancel_button_callback(button):
            raise SelectedButton(exit_token='Cancel')
        cancelbutton = urwid.Button('Cancel',
                on_press=cancel_button_callback)
        return urwid.GridFlow([savebutton, cancelbutton],
                10, 7, 1, 'center')

    fieldwidgets = []
    for prop in card:
        label = urwid.Text(prop.prop)
        value = urwid.Edit('', prop.value)
        editwidget = urwid.Columns([('fixed', 8, label),
                                    ('flow', value)])

        fieldwidgets.append(urwid.Padding(editwidget, ('fixed left', 3),
                                                      ('fixed right', 3)))

    fieldwidgets.append(buttons())
    listwalker = urwid.SimpleListWalker(fieldwidgets)
    listbox = urwid.ListBox(listwalker)
    header = urwid.Text('Please edit your contacts')
    frame = urwid.Frame(listbox, header=header)
    try:
        urwid.MainLoop(frame, None).run()
    except SelectedButton as sel:
        print(sel.exit_token)


def select_entry(names):
    """interactive href selector (urwid based)

    returns: href
    return type: string
    """
    if len(names) is 1:
        return names[0][1]
    if names == list():
        return None
    name_list = list()
    for one in names:
        name_list.append(SelText(one[0], one[1]))
    palette = [('header', 'white', 'black'),
        ('reveal focus', 'black', 'dark cyan', 'standout'), ]
    content = urwid.SimpleListWalker([
        urwid.AttrMap(w, None, 'reveal focus') for w in name_list])

    listbox = urwid.ListBox(content)
    show_key = urwid.Text(u"", wrap='clip')
    head = urwid.AttrMap(show_key, 'header')
    top = urwid.Frame(listbox, head)

    def show_all_input(input, raw):
        """used for urwid test
        to be removed
        """
        show_key.set_text(u"Pressed: " + u" ".join([
            unicode(i) for i in input]))
        return input

    def keystroke(input):
        """used for urwid test
        to be removed
        """
        if input == 'q':
            raise urwid.ExitMainLoop()
        if input is 'enter':
            listbox.get_focus()[0].original_widget
            raise Selected()

    loop = urwid.MainLoop(top, palette,
        input_filter=show_all_input, unhandled_input=keystroke)
    try:
        loop.run()
    except Selected:
        return names[listbox.get_focus()[1]][1]
