import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

import cocy

setup(
    name = "cocy",
    version = cocy.__version__,
    author = "Michael N. Lipp",
    author_email = "mnl@mnl.de",
    description = ("A components library for UPnP."),
    license = "GPL",
    keywords = "circuits UPnP",
    url = "http://packages.python.org/cocy",
    long_description=read('pypi-overview.rst'),
    data_files=[('', ['pypi-overview.rst'])],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    packages=['cocy',
              'cocy.core',
              'cocy.portlets',
              'cocy.upnp',
              'cocy.upnp.adapters',
              'tests'],
    package_data={'cocy.portlets': ['templates/*.properties',
                                    'templates/*.pyhtml',
                                    'templates/themes/default/*'],
                  'cocy.upnp': ['services/*.xml',
                                'templates/*']},
    install_requires = ['rbtranslations', 'circuits-bricks'],
)