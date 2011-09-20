"""
.. codeauthor:: mnl
"""
from cocy.core.components import Manifest, BinarySwitch

class BinaryLight(BinarySwitch):
    '''
    classdocs
    '''

    manifest = Manifest("A Light")

    def __init__(self):
        super(BinaryLight, self).__init__(self.manifest)

