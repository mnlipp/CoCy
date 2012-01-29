"""
..
   This file is part of the CoCy program.
   Copyright (C) 2011 Michael N. Lipp
   
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

.. codeauthor:: mnl
"""
from soaplib.soap import from_soap

def parseSoapRequest(request):
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
        charset = 'utf-8'
            
    payload, soapheader = from_soap(body, charset)
    from soaplib.soap import collapse_swa
    payload = collapse_swa(contentType, payload)

    if payload is not None:
        soapAction = payload.tag

    return soapAction, soapheader, payload
