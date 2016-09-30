# Overview
madx is a Python wrapper around the madx library from CERN (http://madx.web.cern.ch/madx/).
The package is self contained and has no dependencies.

# Usage
Currently the package provides a simple wrapper around the madx command. It can be used in following 2 ways:


```python
import madx

instructions = madx.Instructions()
# ... use append() function to add instructions
instructions.append('exit;')

results = instructions.execute()
```


```python
import madx

instructions = []
# ... adding
instructions.append('exit;')

results = madx.execute(instructions)
```


While using the Instructions class, calling the `execute()` method on it will invoke madx with the current instructions in the instructions buffer.

The `execute()` method of the madx module accepts a list of strings containing the madx instructions.

The return value of both `execute()` methods is an object with two attributes, `data` and `output`.

```
data = results.data
output = results.output
```

`output` holds the output on standard out of the madx command. `data` holds the data returned by the madx command. `data` itself has 3 attributes `global_variables`, `variables` and `table`.
Depending on the instructions send to madx some of these attributes are filled. While using the madx instructions *write* and *twiss* the `global_variables` and `table` attributes are filled, for the madx instruction  *save* only the `variables` attribute is filled (the value of the other attributes are `None`).

Both `global_variables` and `variables` are dictionary with key value pairs. Table is a pandas DataFrame.

Note: If you are interested in the raw results of madx as string, there is a `raw_results` optional parameter to the `execute` function. If this is set to True the data attribute of the return value holds a list of strings.



# Installation
The package is currently supported for Linux and Mac OS X. It can be easily installed in an Anaconda Python installation by

```bash
conda install -c paulscherrerinstitute madx
```
