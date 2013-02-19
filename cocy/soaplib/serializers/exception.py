
#
# soaplib - Copyright (C) cocy.soaplib contributors.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#
# Adapted to standard etree implementation (mnl at mnl.de)

import cocy.soaplib
from xml import etree
from cocy.soaplib.serializers import Base

_ns_xsi = cocy.soaplib.ns_xsi
_pref_soap_env = cocy.soaplib.prefmap[cocy.soaplib.ns_soap_env]

class Fault(Exception, Base):
    __type_name__ = "Fault"

    def __init__(self, faultcode='Server', faultstring="", detail=""):
        self.faultcode = '%s:%s' % (_pref_soap_env, faultcode)
        self.faultstring = faultstring
        self.detail = detail

    @classmethod
    def to_xml(cls, value, tns, parent_elt, name=None):
        if name is None:
            name = cls.get_type_name()
        element = etree.ElementTree.SubElement(parent_elt, "{%s}%s" % (soaplib.ns_soap_env,name))

        etree.ElementTree.SubElement(element, 'faultcode').text = value.faultcode
        etree.ElementTree.SubElement(element, 'faultstring').text = value.faultstring
        etree.ElementTree.SubElement(element, 'detail').text = value.detail

    @classmethod
    def from_xml(cls, element):
        code = element.find('faultcode').text
        string = element.find('faultstring').text
        detail_element = element.find('detail')
        if detail_element is not None:
            if len(detail_element.getchildren()):
                detail = etree.ElementTree.tostring(detail_element)
            else:
                detail = element.find('detail').text
        else:
            detail = ''
        return Fault(faultcode=code, faultstring=string, detail=detail)

    @classmethod
    def add_to_schema(cls, schema_dict):
        complex_type = etree.ElementTree.Element('complexType')
        complex_type.set('name', cls.get_type_name())
        sequenceNode = etree.ElementTree.SubElement(complex_type, 'sequence')

        element = etree.ElementTree.SubElement(sequenceNode, 'element')
        element.set('name', 'detail')
        element.set('{%s}type' % _ns_xsi, 'xs:string')

        element = etree.ElementTree.SubElement(sequenceNode, 'element')
        element.set('name', 'message')
        element.set('{%s}type' % _ns_xsi, 'xs:string')

        schema_dict.add_complex_type(cls, complex_type)

        top_level_element = etree.ElementTree.Element('element')
        top_level_element.set('name', 'ExceptionFaultType')
        top_level_element.set('{%s}type' % _ns_xsi, cls.get_type_name_ns())

        schema_dict.add_element(cls, top_level_element)
