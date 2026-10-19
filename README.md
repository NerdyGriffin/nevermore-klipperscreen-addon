# Nevermore KlipperScreen Add-On

Shows the Nevermore StealthMax intake VOC index and the vent state (Open / Closed) in the
KlipperScreen title bar, after the extruder, bed and chamber readouts. Display only.

It uses KlipperScreen's add-on loader (`addons/<name>.py`, available in builds newer than v0.4.7,
September 2026), so no KlipperScreen file is modified.

## Requirements

- KlipperScreen with the add-on loader (`_load_addons` in `screen.py`).
- The [nevermore-controller](https://github.com/sanaahamel/nevermore-controller) Klipper module
  (`[nevermore]` section) for the VOC index.
- The `NEVERMORE_OPEN_VENT` / `NEVERMORE_CLOSE_VENT` macros from
  [klipper-nerdygriffin-macros](https://github.com/NerdyGriffin/klipper-nerdygriffin-macros)
  (`nevermore.cfg`) for the vent state, which is read from
  `gcode_macro _NEVERMORE_VARS.vent_open`. Without them the vent shows `?`.

On a printer without `[nevermore]` the add-on does nothing.

## Install

```bash
cd ~
git clone https://github.com/NerdyGriffin/nevermore-klipperscreen-addon.git
cd nevermore-klipperscreen-addon
./install.sh
```

Then enable add-ons: in KlipperScreen go to Settings and turn on **Enable Add-ons**, or add
`enable_addons: True` under `[main]` in `KlipperScreen.conf`. Restart KlipperScreen:

```bash
sudo systemctl restart KlipperScreen
```

`./install.sh -h` lists the options; `./install.sh -u` uninstalls.

The installer symlinks `KlipperScreen/nevermore.py` to `~/KlipperScreen/addons/nevermore.py` and
the icons into every theme's `images/` directory, and lists the icon links in
`~/KlipperScreen/.git/info/exclude`.

## Moonraker update manager

Append the contents of `moonraker.conf` from this repo to `~/printer_data/config/moonraker.conf`.
Moonraker restarts KlipperScreen after an update.

## Display

| Item | Source | Shown as |
|---|---|---|
| VOC | `nevermore.intake_gas` (VOC index, 100 = baseline) | number, `?` when the controller is disconnected |
| Vent | `gcode_macro _NEVERMORE_VARS.vent_open` | `Open`, `Closed`, or `?` until a vent macro has run |

`titlebar_name_type: full` or `short` in the printer's section of `KlipperScreen.conf` replaces the
icons with `VOC:` / `Vent:` or `V:` / `Vt:` prefixes, matching KlipperScreen's own items.

## Credits

Icons are from [Material Design Icons](https://pictogrammers.com/library/mdi/) (`air-filter`,
`window-shutter-open`), Apache License 2.0.

Licensed under the GNU GPLv3, see `LICENSE`.
