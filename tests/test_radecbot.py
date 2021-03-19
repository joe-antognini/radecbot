"""Unit tests for radecbot.py"""

import os
import shutil
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import skyfield
import skyfield.api

from .context import radecbot
from radecbot import radecbot  # noqa: F811

EPHEMERIDES_TEST_PATH = Path(__file__).parent / 'fixtures/de421_excerpt.bsp'


class TestLoadEphemerides(unittest.TestCase):
    def test_load_ephemerides_no_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:

            def _mock_download(url, filename):
                shutil.copy(
                    str(EPHEMERIDES_TEST_PATH),
                    os.path.join(tmpdir, radecbot.EPHEMERIDES_FILE),
                )

            with unittest.mock.patch.object(
                radecbot.Loader, 'download'
            ) as mock_download:
                mock_download.side_effect = _mock_download
                ephemerides = radecbot.load_ephemerides(cache_dir=tmpdir)

            self.assertTrue(
                isinstance(ephemerides, skyfield.jpllib.SpiceKernel)
            )


class TestEphemerides(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        shutil.copy(
            str(EPHEMERIDES_TEST_PATH),
            os.path.join(self.tmpdir.name, radecbot.EPHEMERIDES_FILE),
        )

        self.loader = skyfield.api.Loader(self.tmpdir.name)
        if not os.path.exists(self.loader.path_to(radecbot.EPHEMERIDES_FILE)):
            raise FileNotFoundError(
                'Test fixture at '
                f'{self.loader.to_path(radecbot.EPHEMERIDES_FILE)} not found.'
            )
        self.ephemerides = self.loader(radecbot.EPHEMERIDES_FILE)
        self.time = skyfield.api.load.timescale().utc(2021, 1, 1, 12, 0, 0)

    def test_get_planet_radec(self):
        ra, dec = radecbot.get_planet_radec(
            self.ephemerides, radecbot.Planets.JUPITER, self.time
        )

        # These values are taken from JPL's Horizons webpage:
        # https://ssd.jpl.nasa.gov/horizons.cgi
        #
        # At 12:00 pm UTC on January 1, 2021 this website puts Jupiter at:
        # 20h20m2.53s; -20°3'4.9"
        expected_ra = skyfield.units.Angle(hours=20.33403611)
        expected_dec = skyfield.units.Angle(degrees=-20.0513611)

        # Check that the two are equal to within 0.1 arcseconds.
        self.assertAlmostEqual(
            ra.arcseconds(), expected_ra.arcseconds(), delta=0.1
        )
        self.assertAlmostEqual(
            dec.arcseconds(), expected_dec.arcseconds(), delta=0.1
        )

    def test_get_all_radecs(self):
        radecs = radecbot.get_all_radecs(self.ephemerides, self.time)

        self.assertIn(radecbot.Planets.JUPITER, radecs)

        # See note above about the origins of these expected values.
        expected_ra = skyfield.units.Angle(hours=20.33403611)
        expected_dec = skyfield.units.Angle(degrees=-20.0513611)

        observed_ra, observed_dec = radecs[radecbot.Planets.JUPITER]
        self.assertAlmostEqual(
            observed_ra.arcseconds(), expected_ra.arcseconds(), delta=0.1
        )
        self.assertAlmostEqual(
            observed_dec.arcseconds(), expected_dec.arcseconds(), delta=0.1
        )

    def test_moon_phase(self):
        moon_phase = radecbot.moon_phase(self.ephemerides, self.time)

        # This expected phase was found by getting the position of the Sun and
        # moon from JPL's Horizon service for 12pm UTC on January 1, 2021.
        #
        # The RA and Dec were then converted to the ecliptic latitude and
        # longitude using NED's coordinate calculator here:
        # https://ned.ipac.caltech.edu/coordinate_calculator
        #
        # According to JPL Horizons, the RA and Dec of the Sun and Moon at this
        # time is:
        # Sun:  18h47m52.41s -22d58'49.6"
        # Moon: 08h50m15.88s +21d50'52.5"
        #
        # The ecliptic longitudes are then:
        # Sun:  281.00614978
        # Moon: 129.00427084
        #
        # The difference between these then gives the expeted phase.
        expected_phase = 207.998121
        self.assertAlmostEqual(moon_phase, expected_phase, delta=1 / 60)

    @unittest.mock.patch('radecbot.radecbot.get_all_radecs')
    @unittest.mock.patch('radecbot.radecbot.load_ephemerides')
    def test_compose_planet_tweet(self, mock_load_ephemerides, mock_radecs):
        mock_load_ephemerides.return_value = self.ephemerides

        ra = skyfield.units.Angle(hours=12.51)
        dec = skyfield.units.Angle(degrees=80.51)
        mock_radecs.return_value = {
            radecbot.Planets.MERCURY: (ra, dec),
            radecbot.Planets.VENUS: (ra, dec),
            radecbot.Planets.MARS: (ra, dec),
            radecbot.Planets.JUPITER: (ra, dec),
            radecbot.Planets.SATURN: (ra, dec),
            radecbot.Planets.URANUS: (ra, dec),
            radecbot.Planets.NEPTUNE: (ra, dec),
        }
        tweet = radecbot.compose_planet_tweet()

        expected_tweet = (
            'Current planetary RA/Decs:\n'
            '\n'
            '☿: 12h30m36s; +80°30′36″\n'
            '♀: 12h30m36s; +80°30′36″\n'
            '♂: 12h30m36s; +80°30′36″\n'
            '♃: 12h30m36s; +80°30′36″\n'
            '♄: 12h30m36s; +80°30′36″\n'
            '⛢: 12h30m36s; +80°30′36″\n'
            '♆: 12h30m36s; +80°30′36″'
        )

        self.assertEqual(tweet, expected_tweet)

    @unittest.mock.patch('radecbot.radecbot.get_all_radecs')
    @unittest.mock.patch('radecbot.radecbot.load_ephemerides')
    def test_compose_planet_tweet_neg_dec(
        self, mock_load_ephemerides, mock_radecs
    ):
        mock_load_ephemerides.return_value = self.ephemerides

        ra = skyfield.units.Angle(hours=12.51)
        dec = skyfield.units.Angle(degrees=-1.51)
        mock_radecs.return_value = {
            radecbot.Planets.MERCURY: (ra, dec),
            radecbot.Planets.VENUS: (ra, dec),
            radecbot.Planets.MARS: (ra, dec),
            radecbot.Planets.JUPITER: (ra, dec),
            radecbot.Planets.SATURN: (ra, dec),
            radecbot.Planets.URANUS: (ra, dec),
            radecbot.Planets.NEPTUNE: (ra, dec),
        }
        tweet = radecbot.compose_planet_tweet()

        expected_tweet = (
            'Current planetary RA/Decs:\n'
            '\n'
            '☿: 12h30m36s; -01°30′36″\n'
            '♀: 12h30m36s; -01°30′36″\n'
            '♂: 12h30m36s; -01°30′36″\n'
            '♃: 12h30m36s; -01°30′36″\n'
            '♄: 12h30m36s; -01°30′36″\n'
            '⛢: 12h30m36s; -01°30′36″\n'
            '♆: 12h30m36s; -01°30′36″'
        )

        self.assertEqual(tweet, expected_tweet)

    @unittest.mock.patch('radecbot.radecbot.moon_phase')
    @unittest.mock.patch('radecbot.radecbot.get_all_radecs')
    @unittest.mock.patch('radecbot.radecbot.load_ephemerides')
    def test_compose_moonsun_tweet(
        self, mock_load_ephemerides, mock_radecs, mock_moon_phase
    ):
        mock_load_ephemerides.return_value = self.ephemerides

        ra = skyfield.units.Angle(hours=12.51)
        dec = skyfield.units.Angle(degrees=80.51)
        mock_radecs.return_value = {
            radecbot.Planets.SUN: (ra, dec),
            radecbot.Planets.MOON: (ra, dec),
        }
        mock_moon_phase.return_value = 180
        tweet = radecbot.compose_moonsun_tweet()

        expected_tweet = (
            'Current RA/Dec of the Sun & Moon:\n'
            '\n'
            '☉: 12h30m36s; +80°30′36″\n'
            '☾: 12h30m36s; +80°30′36″\n'
            '\n'
            'The moon is full and is 100% illuminated.'
        )

        self.assertEqual(tweet, expected_tweet)

    @unittest.mock.patch('radecbot.radecbot.moon_phase')
    @unittest.mock.patch('radecbot.radecbot.get_all_radecs')
    @unittest.mock.patch('radecbot.radecbot.load_ephemerides')
    def test_compose_moonsun_tweet_neg_dec(
        self, mock_load_ephemerides, mock_radecs, mock_moon_phase
    ):
        mock_load_ephemerides.return_value = self.ephemerides

        ra = skyfield.units.Angle(hours=12.51)
        dec = skyfield.units.Angle(degrees=-0.51)
        mock_radecs.return_value = {
            radecbot.Planets.SUN: (ra, dec),
            radecbot.Planets.MOON: (ra, dec),
        }
        mock_moon_phase.return_value = 180
        tweet = radecbot.compose_moonsun_tweet()

        expected_tweet = (
            'Current RA/Dec of the Sun & Moon:\n'
            '\n'
            '☉: 12h30m36s; -00°30′36″\n'
            '☾: 12h30m36s; -00°30′36″\n'
            '\n'
            'The moon is full and is 100% illuminated.'
        )

        self.assertEqual(tweet, expected_tweet)


class TestMoonPhase(unittest.TestCase):
    def test_moon_illumination(self):
        self.assertEqual(radecbot.moon_illumination(0), 0)
        self.assertEqual(radecbot.moon_illumination(180), 100)
        self.assertEqual(radecbot.moon_illumination(360), 0)

    def test_phase_str(self):
        self.assertEqual(
            radecbot.phase_str(0),
            'The moon is new and is 0% illuminated.',
        )

        self.assertEqual(
            radecbot.phase_str(90),
            'The moon is at first quarter and is 50% illuminated.',
        )

        self.assertEqual(
            radecbot.phase_str(180),
            'The moon is full and is 100% illuminated.',
        )

        self.assertEqual(
            radecbot.phase_str(270),
            'The moon is at third quarter and is 50% illuminated.',
        )
