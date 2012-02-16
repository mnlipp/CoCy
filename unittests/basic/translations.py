"""
.. codeauthor: mnl
"""
import unittest
import os
from util.translations import Translations

class Test(unittest.TestCase):


    def testParse(self):
        inp_file = os.path.abspath \
            (os.path.join(os.path.dirname(__file__), "trans.properties"))
        with open(inp_file) as fp:
            res = Translations(fp)
        self.assertEqual(res._translations["very"], "# tricky")
        self.assertEqual(res._translations[" long key "], " long value ")
        self.assertEqual(res._translations["who"], "are you?")
        self.assertEqual(res._translations["Hello"], "there")



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testParse']
    unittest.main()