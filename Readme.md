# Overview
madx is a Python wrapper around the madx library from CERN (http://madx.web.cern.ch/madx/).
The package is self contained and has no dependencies.

# Usage
Currently the package provides a simple wrapper around the madx command

```python
import madx
results, output = execute(instructions)
```

The execute method accepts a list of strings containing the madx instructions. The results and the output of the madx execution are returned in two different variables. Each of them is a list of strings with the respective output.
