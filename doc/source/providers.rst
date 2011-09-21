===================================
Advertising with the CoCy framework
===================================

The purpose of CoCy is to advertise devices and services on a network.
These advertised devices and services are from now on collectively referred
to as *providers*.

.. autoclass:: cocy.providers.Provider 
   :members:

The :class:`Manifest` is simply a collection of informative items that
are made available when the provider is advertised.

.. autoclass:: cocy.providers.Manifest

Inheriting from :class:`Provider` would be sufficient to simply advertise 
a provider. This, however, doesn't make much sense. A provider
is only of interest if there is something that
can be done with it, such as querying state or invoking actions.

Generic network service protocols allow arbitrary operations to be made
available on the network. Advanced frameworks for those protocols may
support a method to be marked as "published" and it becomes available
to the client.

CoCy, by contrast, aims at providing remote access using predefined 
protocols or profiles. Therefore the set of operations made available
cannot be defined by the component to be published. Rather, the 
component has to supply 
a predefined set of operations. The list of classes shown below 
represents all the types of providers that CoCy currently supports. They
have been defined as independent as possible from the network protocols.

.. autoclass:: cocy.providers.BinarySwitch
