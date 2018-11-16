import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "cocy",
    version = "0.3",
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
              'cocy.soaplib',
              'cocy.soaplib.serializers',
              'cocy.soaplib.test',
              'cocy.soaplib.util',
              'sampleapps',
              'sampleapps.binary_light',
              'sampleapps.media_renderer'],
    package_data={'cocy.portlets': ['templates/*.properties',
                                    'templates/*.pyhtml',
                                    'templates/themes/default/*'],
                  'cocy.upnp': ['services/*.xml',
                                'templates/*']},
   install_requires = ['circuits == 3.2', 'Tenjin', 'rbtranslations', 'circuits-bricks == 0.4.4'],
)