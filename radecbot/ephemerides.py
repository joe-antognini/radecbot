"""Calculate ephemerides."""

from enum import Enum

import skyfield.api
from skyfield.framelib import ecliptic_frame


EPHEMERIDES_FILE = 'de421.bsp'


class Planets(Enum):
    SUN = 'sun'
    MOON = 'moon'
    MERCURY = 'mercury'
    VENUS = 'venus'
    EARTH = 'earth'
    MARS = 'mars'
    JUPITER = 'jupiter barycenter'
    SATURN = 'saturn barycenter'
    URANUS = 'uranus barycenter'
    NEPTUNE = 'neptune barycenter'


SYMBOLS = {
    Planets.SUN: '☉',
    Planets.MOON: '☾',
    Planets.MERCURY: '☿',
    Planets.VENUS: '♀',
    Planets.MARS: '♂',
    Planets.JUPITER: '♃',
    Planets.SATURN: '♄',
    Planets.URANUS: '⛢',
    Planets.NEPTUNE: '♆',
}


def get_planet_radec(ephemerides, planet, t):
    position = ephemerides[Planets.EARTH.value].at(t).observe(
        ephemerides[planet.value]
    )
    ra, dec, _ = position.radec()

    return ra, dec


def get_all_radecs(ephemerides, t):
    radecs = {}

    for planet in Planets:
        if planet == Planets.EARTH:
            continue
        
        ra, dec = get_planet_radec(ephemerides, planet, t)

        radecs[planet] = (ra, dec)
    
    return radecs


def get_moon_phase(ephemerides, t):
    sun = ephemerides[Planets.SUN.value]
    earth = ephemerides[Planets.EARTH.value]
    moon = ephemerides[Planets.MOON.value]

    apparent_sun = earth.at(t).observe(sun).apparent()
    _, solar_longitude, _ = apparent_sun.frame_latlon(ecliptic_frame)

    apparent_moon = earth.at(t).observe(moon).apparent()
    _, lunar_longitude, _ = apparent_moon.frame_latlon(ecliptic_frame)

    return (lunar_longitude.degrees - solar_longitude.degrees) % 360


def compose_planet_tweet():
    ephemerides = skyfield.api.load(EPHEMERIDES_FILE)
    t = skyfield.api.load.timescale().now()

    radecs = get_all_radecs(ephemerides, t)

    s = ['Current planetary RA/Decs:\n']
    for planet in Planets:
        if planet in {Planets.EARTH, Planets.SUN, Planets.MOON}:
            continue

        ra, dec = radecs[planet]

        ra_hr, ra_min, ra_sec = map(int, map(round, ra.hms()))
        dec_deg, dec_min, dec_sec = map(int, map(round, dec.dms()))
        s.append(
                f'{SYMBOLS[planet]}: '
                f'{ra_hr:02d}h{ra_min:02d}m{ra_sec:02d}s; '
                f'{dec_deg:+03d}°{abs(dec_min):01d}′{abs(dec_sec):02}″'
        )

    return '\n'.join(s)


def get_phase_str(phase):
    if phase >= 345 or phase < 15:
        phase_str = 'new'
    elif phase >= 15 and phase < 75:
        phase_str = 'waxing crescent'
    elif phase >= 75 and phase < 105:
        phase_str = 'at first quarter'
    elif phase >= 105 and phase < 165:
        phase_str = 'waxing gibbous'
    elif phase >= 165 and phase < 195:
        phase_str = 'full'
    elif phase >= 195 and phase < 255:
        phase_str = 'waning gibbous'
    elif phase >= 255 and phase < 285:
        phase_str = 'at third quarter'
    elif phase >= 285 and phase < 345:
        phase_str = 'waning crescent'

    return 'The moon is ' + phase_str + '.'


def compose_moonsun_tweet():
    ephemerides = skyfield.api.load(EPHEMERIDES_FILE)
    t = skyfield.api.load.timescale().now()
    radecs = get_all_radecs(ephemerides, t)

    s = ['Current RA/Dec of the Sun & Moon:\n']
    for planet in [Planets.SUN, Planets.MOON]:
        ra, dec = radecs[planet]

        ra_hr, ra_min, ra_sec = map(int, map(round, ra.hms()))
        dec_deg, dec_min, dec_sec = map(int, map(round, dec.dms()))
        s.append(
            f'{SYMBOLS[planet]}: '
            f'{ra_hr:02d}h{ra_min:02d}m{ra_sec:02d}s; '
            f'{dec_deg:+03d}°{abs(dec_min):01d}′{abs(dec_sec):02}″'
        )

    moon_phase = get_moon_phase(ephemerides, t)
    s.append('')
    s.append(get_phase_str(moon_phase))

    return '\n'.join(s)

print(compose_moonsun_tweet())
