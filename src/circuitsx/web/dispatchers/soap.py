'''


.. codeauthor:: mnl

This module implements a SOAP dispatcher that translates incoming calls to
SoapOperation events. This module depends on soaplib.
'''
from circuits.core.components import BaseComponent
from circuits.core.events import Event
from circuits.core.handlers import handler

from soaplib.soap import from_soap

class SOAPOperation(Event):
    """Soap Operation Event"""

class SOAP(BaseComponent):
    '''
    classdocs
    '''

    channel = "web"

    def __init__(self, path=None, target="*", encoding="utf-8"):
        super(SOAP, self).__init__()

        self.path = path
        self.target = target
        self.encoding = encoding

    @handler("request", filter=True, priority=0.1)
    def _on_request(self, request, response):
        if self.path is not None and self.path != request.path.rstrip("/"):
            return

        try:
            # Test if this is a SOAP request. SOAP 1.1 specifies special
            # header, SOAP 1.2 special Content-Type
            soapAction = request.headers["SOAPAction"];
            import cgi
            contentType = cgi.parse_header(request.headers["Content-Type"]);
            if (not soapAction and contentType[0] != "application/soap+xml"):
                return
            # Get body data of request
            body = request.body.read()
            # Use soaplib to separate header and payload
            charset = contentType[1].get('charset',None)
            if charset is None:
                charset = 'ascii'
            
            payload, soapheader = from_soap(body, charset)
            from soaplib.soap import collapse_swa
            payload = collapse_swa(contentType, payload)

            if payload is not None:
                soapAction = payload.tag

            for node in payload:
                print node

            response.headers["Content-Type"] = "text/xml"

            #value = self.push(SoapOperation(*params), c, t)
            #value.response = response
            #value.onSet = ("value_changed", self)
        except Exception as e:
            # TODO: 
            r = self._error(1, "%s: %s" % (type(e), e))
            return r
        else:
            return True
