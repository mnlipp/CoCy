'''


@author: mnl
'''

class C(object):
    attr = 0
    d = {}
    
    def f(self):
        self.attr = self.attr + 1
        self.d['hallo'] = 'du'

if __name__ == '__main__':
    c = C()
    c.f()
    print C.attr
    print C.d
    print c.attr
    print c.d
    