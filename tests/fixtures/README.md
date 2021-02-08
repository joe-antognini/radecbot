The file `de421_excerpt.bsp` contains an excerpt of the JPL DE421 ephemerides
for only a single day: January 1, 2021.  To generate it, run the following:

```sh
python -m jplephem excerpt \
    2021/1/1 \
    2021/1/2 \
    https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp \
    /path/to/repo/root/tests/fixtures/de421_exceprt.bsp
```
