from os.path import dirname, join
from blockify.util import VERSION

from setuptools import setup, find_packages


def read(filename):
    with open(join(dirname(__file__), filename)) as f:
        return f.read()


_name = "blockify"
_license = "MIT"

setup(
    name=_name,
    description="Mute spotify advertisements.",
    long_description=read("README.md"),
    keywords=["spotify", "music", "commercials", "adblock"],
    version=VERSION,
    license=_license,
    url="https://github.com/mikar/{}".format(_name),
    download_url="https://github.com/mikar/blockify/tarball/v{0}".format(VERSION),
    author="Max Falk",
    author_email="gmdfalk@gmail.com",
    packages=find_packages(),
    package_data={_name: ["data/*"]},
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "{0} = {0}.cli:main".format(_name),
            "{0}-dbus = {0}.dbusclient:main".format(_name),
        ],
        "gui_scripts": [
            "{0}-ui = {0}.gui:main".format(_name),
        ],
    },
    install_requires=[
        "dbus-python"
    ]
)
