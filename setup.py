from os.path import dirname, join

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read(filename):
    with open(join(dirname(__file__), filename)) as f:
        return f.read()


_name = "blockify"
_license = "MIT"


setup(
    name=_name,
    description="Mute spotify advertisements.",
    long_description=read("README.md"),
    version="1.0",
    license=_license,
    url="https://github.com/mikar/{}".format(_name),
    author="Max Demian",
    author_email="mikar@gmx.de",
    packages=[_name, _name + "/data"],
    package_data={_name + "/data": ["*.png", "blockify_list"]},
    install_package_data=True,
    entry_points={
                  "console_scripts": [
                      "{0} = {0}.{0}:cli_entry".format(_name),
                  ],
                  "gui_scripts": [
                      "{0}-ui = {0}.{0}_ui:main".format(_name),
                  ],
              }
)
