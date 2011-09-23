"""
.. codeauthor:: mnl
"""
from cocy.providers import BinarySwitch, Manifest, Provider

class BinaryLight(Provider, BinarySwitch):
    '''
    classdocs
    '''

    manifest = Manifest("Binary light sample light", "A Light")

    def __init__(self):
        super(BinaryLight, self).__init__(self.manifest)

