"""
..
   This file is part of the circuits bricks component library.
   Copyright (C) 2012 Michael N. Lipp
   
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

.. moduleauthor:: mnl
"""
from circuits.core.components import BaseComponent
from circuits.core.events import Event
from circuits.core.handlers import handler

from soaplib.soap import from_soap

class soap_operation(Event):
    """Soap Operation Event"""

class SOAP(BaseComponent):
    '''
    classdocs
    '''

    channel = "web"

    def __init__(self, path=None, channel="*", encoding="utf-8"):
        super(SOAP, self).__init__()

        self.path = path
        self.channel = channel
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
