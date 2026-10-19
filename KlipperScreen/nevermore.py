# Nevermore KlipperScreen add-on: intake VOC index and vent state in the title bar.
#
# Copyright (C) 2026 NerdyGriffin
#
# This file may be distributed under the terms of the GNU GPLv3 license.
#
# Loaded by KlipperScreen's add-on loader (addons/nevermore.py -> init(screen)).
# Reads the `nevermore` object from the nevermore-controller Klipper module and
# `gcode_macro _NEVERMORE_VARS` from klipper-nerdygriffin-macros. Display only.

import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

NEVERMORE = "nevermore"
VENT_VARS = "gcode_macro _NEVERMORE_VARS"
SUBSCRIPTION = {
    NEVERMORE: ["intake_gas", "exhaust_gas", "connected"],
    VENT_VARS: ["vent_open"],
}
VENT_TEXT = {True: "Open", False: "Closed"}
VENT_ICON = {True: "nevermore-vent-open", False: "nevermore-vent-closed"}


class NevermoreTitlebar:
    def __init__(self, screen):
        self.screen = screen
        self.bp = screen.base_panel
        self.items = {}
        for key, icon in (("voc", "nevermore-voc"), ("vent", VENT_ICON[True])):
            label = Gtk.Label(label="?", ellipsize=Pango.EllipsizeMode.NONE)
            box = Gtk.Box()
            box.pack_start(label, False, False, 0)
            eventbox = Gtk.EventBox()
            eventbox.add(box)
            self.items[key] = {
                "icon": icon,
                "image": None,
                "label": label,
                "box": box,
                "eventbox": eventbox,
            }

        self._orig_show = self.bp.show_titlebar_items
        self._orig_clear = self.bp.clear_titlebar_items
        self._orig_update = self.bp.process_update
        self._orig_subscribe = screen.ws_subscribe
        self.bp.show_titlebar_items = self.show_titlebar_items
        self.bp.clear_titlebar_items = self.clear_titlebar_items
        self.bp.process_update = self.process_update
        screen.ws_subscribe = self.ws_subscribe

    # --- helpers -------------------------------------------------------------

    def _printer_name(self):
        return getattr(self.screen.state, "printer_name", "?")

    def has_nevermore(self):
        printer = self.screen.printer
        return printer is not None and NEVERMORE in printer.data

    def _stat(self, obj, key):
        printer = self.screen.printer
        if printer is None:
            return None
        return printer.data.get(obj, {}).get(key)

    def _img_size(self):
        return self.screen.gtk.img_scale * self.bp.bts

    def _texts(self):
        gas = self._stat(NEVERMORE, "intake_gas")
        connected = self._stat(NEVERMORE, "connected")
        voc = f"{int(gas)}" if isinstance(gas, (int, float)) and connected is not False else "?"
        vent_open = self._stat(VENT_VARS, "vent_open")
        vent = VENT_TEXT.get(vent_open, "?")
        self.items["vent"]["icon"] = VENT_ICON.get(vent_open, VENT_ICON[True])
        name_type = self.bp.titlebar_name_type
        if name_type == "full":
            return f"VOC: {voc}", f"Vent: {vent}"
        if name_type == "short":
            return f"V: {voc}", f"Vt: {vent}"
        return voc, vent

    def refresh(self):
        voc, vent = self._texts()
        self.items["voc"]["label"].set_label(voc)
        self.items["vent"]["label"].set_label(vent)
        image = self.items["vent"]["image"]
        if image is not None:
            size = self._img_size()
            image.set_from_pixbuf(self.screen.gtk.PixbufFromIcon(self.items["vent"]["icon"], size, size))

    def _rebuild_icons(self):
        img_size = self._img_size()
        for item in self.items.values():
            box = item["box"]
            for child in box.get_children():
                if child is not item["label"]:
                    box.remove(child)
            item["image"] = None
            if self.bp.titlebar_name_type is not None:
                continue
            icon = self.screen.gtk.Image(item["icon"], img_size, img_size)
            box.pack_start(icon, False, False, 3)
            box.reorder_child(icon, 0)
            item["image"] = icon

    # --- wrapped BasePanel / Screen methods ----------------------------------

    def show_titlebar_items(self):
        self._orig_show()
        try:
            if not self.has_nevermore():
                logging.info(f"nevermore: titlebar items skipped for {self._printer_name()}")
                return
            item_box = self.bp.control["item_box"]
            self._rebuild_icons()
            for item in self.items.values():
                if item["eventbox"].get_parent() is None:
                    item_box.add(item["eventbox"])
            self.refresh()
            item_box.show_all()
            logging.info(f"nevermore: titlebar items added for {self._printer_name()}")
        except Exception as e:
            logging.warning(f"nevermore: could not add titlebar items: {e}")

    def clear_titlebar_items(self):
        self._orig_clear()
        for item in self.items.values():
            item["label"].set_label("?")

    def process_update(self, action, data):
        result = self._orig_update(action, data)
        if action == "notify_status_update" and (NEVERMORE in data or VENT_VARS in data):
            try:
                self.refresh()
            except Exception as e:
                logging.warning(f"nevermore: refresh failed: {e}")
        return result

    def ws_subscribe(self):
        ws = self.screen._ws
        if ws is None or not self.has_nevermore():
            return self._orig_subscribe()
        api = ws.api
        orig_subscription = api.object_subscription

        def object_subscription(updates):
            updates["objects"].update(SUBSCRIPTION)
            return orig_subscription(updates)

        api.object_subscription = object_subscription
        try:
            return self._orig_subscribe()
        finally:
            api.object_subscription = orig_subscription


def init(screen):
    NevermoreTitlebar(screen)
    logging.info("nevermore: add-on initialised")
