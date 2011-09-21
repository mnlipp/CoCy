"""
.. codeauthor:: mnl
"""
from cocy.providers import BinarySwitch, Manifest

class BinaryLight(BinarySwitch):
    '''
    classdocs
    '''

    manifest = Manifest("A Light")

    def __init__(self):
        super(BinaryLight, self).__init__(self.manifest)

