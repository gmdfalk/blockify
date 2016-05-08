from os.path import dirname, join
from blockify.util import VERSION

from setuptools import setup, find_packages


def read(filename):
    text = ""
    try:
        with open(join(dirname(__file__), filename)) as f:
            text = f.read()
    except Exception as e:
        text = "{0}: {1}".format(e, filename)

    return text


_name = "blockify"
_license = "MIT"
_description = read("README.md")

setup(
    name=_name,
    description="Mute spotify advertisements.",
    long_description=_description,
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
    }
)
