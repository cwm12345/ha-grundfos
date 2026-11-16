"""Tests for the Grundfos integration."""

# Written by Claude, guided by Chris.

from modbus_connection.mock import MockModbusUnit

from homeassistant.const import CONF_HOST, CONF_PORT

MOCK_HOST = "192.0.2.20"
MOCK_USER_INPUT = {CONF_HOST: MOCK_HOST, CONF_PORT: 502, "unit_id": 1}
MOCK_UNIQUE_ID = f"{MOCK_HOST}:502:1"
MOCK_TITLE = "MAGNA3"

NA = 0xFFFF

# A real MAGNA3 40-80 F through a CIM 500 (Modbus TCP), read live while one
# radiant zone was calling. It runs in constant flow. Zero-based holding
# register addresses: register 00021 is holding[20].
CIM: list[int] = [
    0,  # 00021 GENIbus CRC errors
    1,  # 00022 GENIbus data errors
    0x1001,  # 00023 CIM version 10.01
    0,  # 00024 Modbus address (unused on TCP)
    0,  # 00025-00026 telegrams sent: 222
    222,
    0,  # 00027-00028 telegrams received: 219
    219,
    NA,  # 00029 reserved
    1,  # 00030 unit family: circulator pumps
    10,  # 00031 unit type: MAGNA3
    0,  # 00032 unit version
    NA,  # 00033 reserved
    0,  # 00034-00035 product software version: not reported
    0,
    0x0506,  # 00036 software date: 5 June
    0x2018,  # 00037 software year
]
STATUS: list[int] = [
    8896,  # 00201 rotating, counterclockwise, on, at max speed
    969,  # 00202 process feedback 9.69 %
    7,  # 00203 control mode: constant flow
    0,  # 00204 operation mode: auto
    0,  # 00205 alarm: none
    0,  # 00206 warning: none
    0,  # 00207 bearing service
    0,  # 00208 drive state
    14,  # 00209 feedback sensor unit: W
    0,  # 00210 feedback sensor min
    22000,  # 00211 feedback sensor max
    1450,  # 00212 nominal frequency 145.0 Hz
    3386,  # 00213 min frequency 33.86 %
    10000,  # 00214 max frequency 100 %
    1024,  # 00215 setpoint range min 10.24 %
    9016,  # 00216 setpoint range max 90.16 %
    NA,  # 00217-00220 reserved
    NA,
    NA,
    NA,
    0,  # 00221 flow estimation within range
    10,  # 00222 Kp 1.0
    80,  # 00223 Ti 8.0 s
    1,  # 00224 direct control
    1,  # 00225 control source: display
]
DATA: list[int] = [
    803,  # 00301 head 0.803 bar
    22,  # 00302 flow 2.2 m3/h
    9803,  # 00303 relative performance 98.03 %
    4288,  # 00304 speed 4288 rpm
    1412,  # 00305 frequency 141.2 Hz
    0,  # 00306 digital inputs
    1,  # 00307 digital outputs
    6077,  # 00308 actual setpoint 60.77 %
    10,  # 00309 motor current 1.0 A
    1980,  # 00310 DC-link 198.0 V
    NA,  # 00311 motor voltage
    0,  # 00312-00313 power 199 W
    199,
    NA,  # 00314 remote flow
    NA,  # 00315 inlet pressure
    NA,  # 00316 remote pressure 1
    NA,  # 00317 feed tank level
    NA,  # 00318 power electronics temperature
    NA,  # 00319 motor temperature
    NA,  # 00320 remote temperature 1
    31515,  # 00321 electronics 315.15 K = 42.0 C
    32038,  # 00322 liquid 320.38 K = 47.23 C
    NA,  # 00323 bearing DE
    NA,  # 00324 bearing NDE
    NA,  # 00325 aux sensor
    103,  # 00326 specific energy 103 Wh/m3
    0,  # 00327-00328 operating hours 5760
    5760,
    0,  # 00329-00330 powered hours 5762
    5762,
    NA,  # 00331 torque
    0,  # 00332-00333 energy 1264 kWh
    1264,
    0,  # 00334-00335 starts 449
    449,
    NA,  # 00336 reserved
    NA,  # 00337 remote temperature 2
    6381,  # 00338 user setpoint 63.81 %
    803,  # 00339 differential pressure 0.803 bar
    NA,  # 00340 outlet pressure
    NA,  # 00341 remote pressure 2
    NA,  # 00342 load
    27386,  # 00343-00344 clock
    34255,
    1330,  # 00345 max flow limit 133.0 m3/h
    NA,  # 00346 remote differential temperature
    NA,  # 00347 inlet differential pressure
    NA,  # 00348 outlet differential pressure
    NA,  # 00349 remote differential pressure
    NA,  # 00350 storage tank level
    NA,  # 00351 ambient temperature
    0,  # 00352-00353 heat energy 1: 0, no heat meter
    0,
    NA,  # 00354-00355 heat power: not available
    NA,
    NA,  # 00356 heat differential temperature
    20,  # 00357-00358 volume 1: 13629.00 m3
    52180,
    0,  # 00359-00360 heat energy 2
    0,
    0,  # 00361-00362 volume 2
    0,
]


def seed_pump(unit: MockModbusUnit) -> None:
    """Seed a mock unit as the live MAGNA3."""
    for start, words in ((20, CIM), (200, STATUS), (300, DATA)):
        for offset, value in enumerate(words):
            unit.holding[start + offset] = value
