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
from cocy.soaplib.soap import from_soap
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, QName
import cocy.soaplib

def splitQTag (tag):
    tag_ns, tag_name = tag.split("}", 1)
    tag_ns = tag_ns[1:]
    return (tag_ns, tag_name)

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
    from cocy.soaplib.soap import collapse_swa
    payload = collapse_swa(contentType, payload)

    if payload is not None:
        soapAction = payload.tag

    return soapAction, soapheader, payload


def buildSoapResponse(response, body):
    # construct the soap response, and serialize it
    envelope = Element('{%s}Envelope' % cocy.soaplib.ns_soap_env)
    # body
    soap_body = SubElement(envelope, '{%s}Body' % cocy.soaplib.ns_soap_env)
    soap_body.append(body)

    response.headers["Content-Type"] = "text/xml; charset=utf-8"
    return "<?xml version='1.0' encoding='utf-8'?>" + \
        ElementTree.tostring(envelope, encoding="utf-8")


def set_ns_prefixes(elem, prefix_map):

    # build uri map and add to root element
    uri_map = {}
    for prefix, uri in prefix_map.items():
        uri_map[uri] = prefix
        elem.set("xmlns" + "" if not prefix else (":" + prefix), uri)

    # fixup all elements in the tree
    memo = {}
    for elem in elem.getiterator():
        _fixup_element_prefixes(elem, uri_map, memo)
        

def _fixup_element_prefixes(elem, uri_map, memo):
    def fixup(name):
        try:
            return memo[name]
        except KeyError:
            if isinstance(name, QName):
                name = str(name)
            if name[0] != "{":
                return
            uri, tag = name[1:].split("}")
            if uri in uri_map:
                new_name = (uri_map[uri] + ":") if uri_map[uri] else "" + tag
                memo[name] = new_name
                return new_name
    # fix element name
    name = fixup(elem.tag)
    if name:
        elem.tag = name
    # fix attribute names
    for key, value in elem.items():
        name = fixup(key)
        if name:
            elem.set(name, value)
            del elem.attrib[key]
            
    
def duration_to_secs(duration):
    secPart = duration.split(".")[0]
    hms = secPart.split(":")
    return 3600 * int(hms[0]) + 60 * int(hms[1]) + int(hms[2])

def secs_to_duration(secs):
    return "%d:%02d:%02d" % (int(secs / 3600), 
                             int(int(secs) % 3600 / 60),
                             int(secs) % 60)
                