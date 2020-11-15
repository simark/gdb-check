from setuptools import setup
import sys

if sys.version_info.major != 3:
    print("gdb-check needs Python 3.")
    sys.exit(1)

setup(
    name="GDB check script",
    version="1.0.3",
    packages=["gdbcheck"],
    entry_points={"console_scripts": ["gdb-check = gdbcheck.gdbcheck:main"]},
    install_requires=[
        "termcolor",
    ],
)
