'''


@author: mnl
'''

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('suds.client').setLevel(logging.DEBUG)
    logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)
    
    from suds.client import Client
    url = 'file:///home/mnl/devel/eclipse-se-workspace/CobaUPnP/tests/soap/HelloService.wsdl'
    client = Client(url)
    client.options.cache.setduration(seconds=1)
    client.service.sayHello("Developer")
    pass