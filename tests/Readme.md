# Overview

The correct operation of the madx package can be checked by execute this command (inside this directory): 

```
python -m madx.madx input.madx | diff output.dat -
```

The output should be something like this (i.e. only 2 lines, holding the date and time should be different - eventually there is a third line stating the OS if you are executing this on Mac OS X):

```
44,45c44,45
< @ DATE             %08s "21/09/16"
< @ TIME             %08s "13.24.15"
---
> @ DATE             %08s "26/09/16"
> @ TIME             %08s "09.23.13"
```