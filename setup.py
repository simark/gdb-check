from setuptools import setup

setup(
    name='GDB check script',
    version='1.0.1',
    packages=['gdbcheck'],
    entry_points={
        'console_scripts': [
            'gdb-check = gdbcheck.gdbcheck:main'
        ]
    },
    install_requires=[
        'termcolor',
    ]
)
