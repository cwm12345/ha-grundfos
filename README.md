<!-- Written by Claude, guided by Chris. -->

# Grundfos pumps for Home Assistant

A Home Assistant integration for Grundfos pumps with a CIM 500 Modbus TCP
module (or a CIM 200 behind a Modbus TCP gateway): MAGNA3 and MAGNA3-D
circulators, E-pumps with MGE motors and CUE drives. Read-only.

It follows Home Assistant's Modbus integration pattern: the device model lives
in the [grundfos-modbus](https://github.com/cwm12345/grundfos-modbus) library,
the integration is written in core's layout under `core/`, and
`scripts/vendor.py` builds the HACS version in `custom_components/` with the
library vendored in.

Requires Home Assistant 2026.10 or newer (the `modbus` integration's shared
connections and modbus-connection 4.12+).

Tested on one MAGNA3 40-80 F with a CIM 500.

## Before you start: the CIM 500

- Its rotary switch must be at **1 (Modbus TCP)**. Out of the box it's at 0
  (PROFINET), where the IP fields can't be edited. Changing the switch resets
  the module's network settings to the factory address, 192.168.1.100.
- The module has **two IP addresses**: its web server (Network Settings page)
  and its Modbus TCP address (Real Time Ethernet Protocol page, which only
  shows editable fields once the switch is at 1). This integration needs the
  **Modbus TCP** one.
- The module is powered by the pump. If the pump's supply is switched by a
  zone relay, the module, and every entity here, is unavailable whenever the
  pump is off. That's expected; it isn't a fault. Set the integration up while
  the pump is running.

## Setup

Settings → Devices & services → Add integration → Grundfos, then give:

- the module's Modbus TCP address and port (502);
- the unit ID (a CIM 500 ignores it; leave it at 1).

The device is named for the product the module reports, e.g. "MAGNA3".

## Entities

- **Sensors:** liquid temperature, flow, head, power, energy, speed, relative
  performance, control mode, operating mode, alarm and warning (decoded).
  Diagnostics: setpoints, process feedback, control source, flow estimation,
  electronics temperature, motor current, DC-link voltage, motor frequency,
  specific energy, operating and powered hours, starts, pumped volume, raw
  alarm and warning codes.
- **Only when the pump supplies them:** inlet/outlet/remote pressures, remote
  flow, remote and ambient temperatures, motor values, and the heat meter
  (heat power, heat energy, supply/return difference), which needs a second
  temperature sensor on the pump.
- **Binary sensors:** running, started, alarm, warning, and diagnostics for
  remote control, at max/min speed, at max power and low-flow stop.

## Up front

This was built for one installation and is shared as a starting point. I'm
not planning to be a long-term maintainer; fork freely.

## License

[Unlicense](LICENSE): public domain.
