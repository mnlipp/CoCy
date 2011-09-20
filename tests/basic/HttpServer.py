'''


@author: mnl
'''

from circuits import Debugger
from circuits.web import Server, Controller
from circuits.core.handlers import handler
from circuits.core.manager import Manager
from circuitsx.web.dispatchers.soap import SOAP

class SayHello(Controller):
    
    channel = "/SayHello"

    def index(self):
        self.response.headers['Content-Type'] = 'text/xml'
        body = self.request.body.read()
        from soaplib.soap import from_soap
        payload, header = from_soap(body, 'ascii')
        return "Du"

class SubDir(Controller):
    
    channel = "/hallo"
    
    def du(self):
        request = self.request
        return "Du"

    def da(self):
        return "da"

class Root(Controller):

    def index(self):
        return "Hello World!"

if __name__ == '__main__':
    manager = Manager()
    server = Server(("localhost", 8000), ssl=False, certfile="cert.pem") 
    server.register(manager);
    Debugger().register(manager)
    Root().register(manager)
    SubDir().register(manager)
    SayHello().register(manager)
    #SOAP().register(manager)
    from circuits.tools import graph
    print graph(manager)
    # (server + Debugger() + Root() + SubDir() + SayHello()).run()
    manager.run()
    pass