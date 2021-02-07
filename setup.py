"""Setup script for radecbot.

Radecbot is a bot that tweets the right ascension and declinations of the Sun,
Moon, and planets.

"""

from setuptools import setup

with open('README.md') as fp:
    long_description=fp.read()

setup(
    name='radecbot',
    version='0.1.0',
    description='Twitter bot that tweets the positions of the Sun, Moon, and '
                'planets.',
    long_description=long_description,
    url='https://github.com/joe-antognini/radecbot',
    author='Joseph Antognini',
    author_email='joe.antognini@gmail.com',
    license='MIT',
    packages=['radecbot'],
    install_requires=[
        'numpy==1.20.0',
        'skyfield==1.36',
        'tweepy==3.10.0',
    ],
    entry_points={
        'console_scripts':
            ['radecbot=radecbot.radecbot'],
    },
    include_package_data=True,
    setup_requires=['pytest-runner'],
    test_requires=['pytest'],
    python_requires='>=3.6',
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Astronomy',
    ],
)
