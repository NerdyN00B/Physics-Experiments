# VirtualBench 8012

This software allows you to interface with the VirtualBench 8012. It can be used
as a standalone class or run a script. The VirtualBench can sample at 1GHz and
can measure at most 1M samples.

Additionally a script `clean_data.py` is provided. This file can be used to clean the data you get when saving it from the normal interface. To use it simply double-click it.

# Requirements

- 32-bit Python, on the TOO computers this can be found
  under `C:\Python32\python32.exe`;
- `numpy`;
- `pyvirtualbench`;
- `matplotlib`;

# Usage

As a recommendation copy the file `virtualbench.py` (optionally also copy `virtualbency.bat`) to your own `P:` drive. The
serial number ('S/N') of can be found on the bottom of the VirtualBench. Before
the device starts measuring it needs to be triggered by a rapidly changing
voltage on the `TRIG` port, an easy way to do so it by touching it with your finger.

## Run as a script

You can run the file `virtualbench.bat` by double-clicking it. This will run `virtualbench.py` using 32-bit Python on the lab computers. Alternatively open `cmd.exe` or `powershell.exe`. Then run the following command:

```
C:\Python32\python32.exe virtualbench.py
```

This will run the main function of the script. It will ask you which
VirtualBench you want to use and some parameters. At the end of the script it
will plot the data and ask to save it to a file. In case of a failure the
software will try to save your data to `P:\backup.csv`.

## Use as a class

To import the class in your own project you can use the following code:

```python
from virtualbench import VirtualBench8012

# Create a VirtualBench8012 object
serial_number = '305D14A'
virtual_bench = VirtualBench8012(serial_number)

# Set the parameters
sample_rate = 500_000_000
acquisition_time = 1E-3
pretrigger_time = 1E-9
expected_amplitude = 1

# Configure the VirtualBench
virtual_bench.configure(sample_rate, acquisition_time, pretrigger_time,
                        expected_amplitude)

# Take a single measurement
data = virtual_bench()
```

## Parameters

| Parameter | Description                                                   |
| --------- |---------------------------------------------------------------|
| `sample_rate` | The sample rate, the maximum sample rate is 1GHz (Hz).        |
| `acquisition_time` | How long we will measure, at most 1M samples (s).             |
| `pretrigger_time` | How long we will wait before measuring after the trigger (s). |
| `expected_amplitude` | The highest expected amplitude of the signal (V).             |

# Contact

This software is maintained by the TOO group at the Leiden Institute of Physics.
If you have any questions or comments, please contact the group
at <TOO@physics.leidenuniv.nl>.
