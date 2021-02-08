"""Calculate ephemerides."""

import os
from enum import Enum
from typing import Dict
from typing import Tuple

import numpy as np
import skyfield.api
import tweepy
import yaml
from skyfield.api import Loader
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


def load_ephemerides(
    cache_dir: str = None, ephemerides_file: str = EPHEMERIDES_FILE
) -> skyfield.jpllib.SpiceKernel:
    """Load the DE421 ephemeris.

    Note that the first time this function is called, it will need to download
    the DE421 epehemeris file from JPL.  This file is 17 MB, but the server is
    a little slow, so it can take about 10 seconds.  Subsequently, this data
    will be cached in `$HOME/.cache/radecbot` and loading will be fast.

    """
    if cache_dir is None:
        cache_dir = os.path.join(os.getenv('HOME'), '.cache/radecbot')

    loader = Loader(cache_dir)

    filename = os.path.join(cache_dir, ephemerides_file)
    if not os.path.exists(filename):
        url = loader.build_url(ephemerides_file)
        loader.download(url, filename)

    if not os.path.exists(loader.path_to(ephemerides_file)):
        raise FileNotFoundError(
            f'Ephemerides file {loader.path_to(ephemerides_file)} not found! '
            f'Did the download fail?'
        )

    return loader(ephemerides_file)


def get_planet_radec(
    ephemerides: skyfield.jpllib.SpiceKernel,
    planet: Planets,
    time: skyfield.timelib.Timescale,
) -> Tuple[skyfield.units.Angle, skyfield.units.Angle]:
    """Calculate the right ascension and declination of a planet."""
    position = (
        ephemerides[Planets.EARTH.value]
        .at(time)
        .observe(ephemerides[planet.value])
    )
    ra, dec, _ = position.radec()

    return ra, dec


def get_all_radecs(
    ephemerides: skyfield.jpllib.SpiceKernel, time: skyfield.timelib.Timescale
) -> Dict[Planets, Tuple[skyfield.units.Angle, skyfield.units.Angle]]:
    """Return a dictionary with the RAs and decs of all planets."""
    radecs = {}

    for planet in Planets:
        if planet == Planets.EARTH:
            continue

        ra, dec = get_planet_radec(ephemerides, planet, time)

        radecs[planet] = (ra, dec)

    return radecs


def moon_phase(
    ephemerides: skyfield.jpllib.SpiceKernel, time: skyfield.timelib.Timescale
) -> float:
    """Calculate the phase angle of the Moon.

    This will be 0 degrees at new moon, 90 degrees at first quarter, 180
    degrees at full moon, etc.

    """
    sun = ephemerides[Planets.SUN.value]
    earth = ephemerides[Planets.EARTH.value]
    moon = ephemerides[Planets.MOON.value]

    apparent_sun = earth.at(time).observe(sun).apparent()
    _, solar_longitude, _ = apparent_sun.frame_latlon(ecliptic_frame)

    apparent_moon = earth.at(time).observe(moon).apparent()
    _, lunar_longitude, _ = apparent_moon.frame_latlon(ecliptic_frame)

    return (lunar_longitude.degrees - solar_longitude.degrees) % 360


def moon_illumination(phase: float) -> float:
    """Calculate the percentage of the moon that is illuminated.

    Currently this value increases approximately linearly in time from new moon
    to full, and then linearly back down until the next new moon.

    Args:
        phase: float
            The phase angle of the Moon, in degrees.

    Returns:
        illumination: flaot
            The percentage of the Moon that is illuminated.

    """
    return 100 * (1 - np.abs(phase - 180) / 180)


def compose_planet_tweet() -> str:
    """Create a tweet with the positions of the planets.

    This will determine the position of the planets at the time this function
    is run.

    The output will look something like this:

        Current planetary RA/Decs:

        ☿: 21h31m14s; -11°2′08″
        ♀: 20h36m25s; -19°27′05″
        ♂: 02h50m31s; +17°45′15″
        ♃: 20h55m14s; -17°55′50″
        ♄: 20h32m43s; -19°15′42″
        ⛢: 02h17m57s; +13°20′03″
        ♆: 23h21m54s; -05°15′59″

    """
    ephemerides = load_ephemerides()
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


def phase_str(phase: float) -> str:
    """Create a string describing the phase of the Moon.

    For example, if the phase is 180 degrees, the result will look like this:

        The moon is full and is 100% illuminated.

    Args:
        phase: float
            The phase of the Moon in degrees.

    Returns: str
        A string describing the phase of the Moon.

    """
    if phase >= 345 or phase < 15:
        phase_str = 'new'
    elif phase >= 15 and phase < 75:
        phase_str = 'a waxing crescent'
    elif phase >= 75 and phase < 105:
        phase_str = 'at first quarter'
    elif phase >= 105 and phase < 165:
        phase_str = 'a waxing gibbous'
    elif phase >= 165 and phase < 195:
        phase_str = 'full'
    elif phase >= 195 and phase < 255:
        phase_str = 'a waning gibbous'
    elif phase >= 255 and phase < 285:
        phase_str = 'at third quarter'
    elif phase >= 285 and phase < 345:
        phase_str = 'a waning crescent'

    illumination = int(round(moon_illumination(phase)))
    return f'The moon is {phase_str} and is {illumination}% illuminated.'


def compose_moonsun_tweet():
    """Create a tweet with the positions of the Sun and Moon.

    This will determine the position of the Sun and Moon at the time this
    function is run.

    The output will look something like this:

        Current RA/Dec of the Sun & Moon:

        ☉: 21h22m18s; -15°23′32″
        ☾: 17h06m14s; -22°50′09″

        The moon is a waning crescent and is 34% illuminated.

    """
    ephemerides = load_ephemerides()
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

    current_moon_phase = moon_phase(ephemerides, t)
    s.append('')
    s.append(phase_str(current_moon_phase))

    return '\n'.join(s)


def tweet():
    """Compose two tweets and post them to Twitter.

    This will compose two tweets, one describing the positions of the planets
    and the other describing the position of the Sun & Moon.  It will then post
    these two tweets to Twitter.

    Note that the following need to be defined in the file
    `$HOME/.config/radecbot/config.yaml`:

    * API Key
    * API Secret Key
    * Bearer token
    * Access token
    * Acess token secret

    """
    config_path = os.path.join(
        os.getenv('HOME'), '.config/radecbot/config.yaml'
    )
    with open(config_path) as fp:
        config = yaml.safe_load(fp)
    auth = tweepy.OAuthHandler(config['api_key'], config['api_secret_key'])
    auth.set_access_token(
        config['access_token'], config['access_token_secret']
    )
    api = tweepy.API(auth)
    api.update_status(compose_planet_tweet())
    api.update_status(compose_moonsun_tweet())


if __name__ == '__main__':
    tweet()
