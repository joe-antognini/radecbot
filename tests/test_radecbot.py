"""Unit tests for radecbot.py"""

import os
import shutil
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import skyfield

from .context import radecbot
from radecbot import radecbot

EPHEMERIDES_TEST_PATH = Path(__file__).parent / 'fixtures/de421_excerpt.bsp'


class TestLoadEphemerides(unittest.TestCase):
    def test_load_ephemerides_no_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            def _mock_download(url, filename):
                shutil.copy(
                    str(EPHEMERIDES_TEST_PATH),
                    os.path.join(tmpdir, 'de421.bsp'),
                )

            with unittest.mock.patch.object(
                radecbot.Loader, 'download'
            ) as mock_download:
                mock_download.side_effect = _mock_download
                ephemerides = radecbot.load_ephemerides(
                    cache_dir=tmpdir
                )

            self.assertTrue(
                isinstance(ephemerides, skyfield.jpllib.SpiceKernel)
            )


class TestMoonPhase(unittest.TestCase):
    def test_moon_illumination(self):
        self.assertEqual(radecbot.moon_illumination(0), 0)
        self.assertEqual(radecbot.moon_illumination(180), 100)
        self.assertEqual(radecbot.moon_illumination(360), 0)
