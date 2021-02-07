# RA/Dec Twitter bot

This is the code used to run the RA/Dec Twitter Bot, [@ra_dec_bot][1].  This
bot periodically tweets the right ascensions and declinations of the Sun, Moon,
and planets, along with the phase and illumination of the Moon.

Each time the script is called, it will generate two tweets.  One will look
something like this:

> Current RA/Dec of the Sun & Moon:
> 
> ☉: 21h22m18s; -15°23′32″
> ☾: 17h06m14s; -22°50′09″
> 
> The moon is a waning crescent and is 34% illuminated.

And the other will look something like this:

> Current planetary RA/Decs:
>
> ☿: 21h31m14s; -11°2′08″
> ♀: 20h36m25s; -19°27′05″
> ♂: 02h50m31s; +17°45′15″
> ♃: 20h55m14s; -17°55′50″
> ♄: 20h32m43s; -19°15′42″
> ⛢: 02h17m57s; +13°20′03″
> ♆: 23h21m54s; -05°15′59″

## Installation

The purpose of this code is more to be inspected rather than to be widely
distributed and in common use.  I want it to be easy to see where the numbers
that [@ra_dec_bot][1] tweets come from.  Since this is unlikely to be widely
installed, I didn't want to pollute the Python package index namespace and so
the installation will take a few more steps than the typical Python package
(though hopefully not too many).

1. Clone the repository.
2. `cd /path/to/repo`
3. Run `pip install -r requirements.txt`.

### Setting up the Twitter API keys

If you would like to run a Twitter bot of your own, you will need to follow the
instructions to set up a Twitter developer account.

You will need to create an app associated with the account you will be tweeting
from, and then generate API keys.  In particular, in order to tweet you will
need the following:

* API Key
* API Secret Key
* Bearer token
* Access token
* Acess token secret

These should be stored in a YAML file in `$HOME/.config/radecbot/config.yaml`.

## Usage

To run the script and tweet, simply run

```
python /path/to/repo/radecbot/radecbot.py
```

This will generate the text for the two tweets and automatically post them
(assuming you have set up the API keys correctly).

The first time the script is run it will need to download the ephemerides from
JPL.  While the ephemerides are not an especially large file (17 MB), their
server is also not especially fast so it will take a little longer on your
first run.  Subsequently, `radecbot` caches the ephemerides at
`$HOME/.cache/radecbot`.  This will tide you over until 2053, at which point
you will need to download a new set of ephemerides.

## FAQs

### Where do the positions come from?

This code uses [Skyfield][2] to calculate the current positions of the Sun,
Moon, and planets.  Behind the scenes Skyfield is using a set of ephemerides
provided by JPL.  In particular, `radecbot` uses the DE421 ephemerides, which
is valid from July 29, 1899 to October 9, 2053.

[1]: https://twitter.com/ra_dec_bot

[2]: https://rhodesmill.org/skyfield/
