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

===================================
Advertising with the CoCy framework
===================================

The purpose of CoCy is to advertise devices and services on a network.
These advertised devices and services are from now on collectively referred
to as *providers*.

.. autoclass:: cocy.providers.Provider 
   :members: provider_manifest, _on_provider_query

The :class:`Manifest` is simply a collection of informative items that
are made available when the provider is advertised.

.. autoclass:: cocy.providers.Manifest

.. sidebar:: Making operations available

   Generic network service protocols allow arbitrary operations to be made
   available on the network. Advanced frameworks for those protocols may
   support a method to be marked as "published" and it becomes available
   to the client.

   CoCy, by contrast, aims at providing remote access using predefined 
   protocols or profiles. Therefore the set of operations made available
   cannot be defined by the component to be published. Rather, the 
   component has to supply 
   a predefined set of operations. 
   
Inheriting from :class:`Provider` causes the component to be advertised
on the network. In order to be useful, a provider must additionally support
operations, such as querying state or invoking actions.

The list of classes shown below 
represents all the types of providers that CoCy currently supports. They
have been defined as independent as possible from the network protocols.

.. autoclass:: cocy.providers.BinarySwitch
