#!/usr/bin/env python2

import os


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


_name = "blockify"
_license = "MIT"


setup(
    name=_name,
    description="Mutes spotify advertisements.",
    long_description=read("README.md"),
    version="0.7",
    license=_license,
    url="https://github.com/mikar/%s" % _name,
    author="Max Demian",
    author_email="mikar@gmx.de",
    packages=[_name],
    package_data={_name: ["blockify_list"]},
    install_package_data=True,
    entry_points={
                  "console_scripts": [
                      "{0} = {0}.{0}:main".format(_name),
                  ],
                  "gui_scripts": [
                      "{0}-ui = {0}.{0}_ui:main".format(_name),
                  ],
              }
)
