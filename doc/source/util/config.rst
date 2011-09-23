=====================
Configuration Support
=====================

A common task when programming an application is storing configuration
values. Python already comes with the package :mod:`ConfigParser` that
stores configurations in the ini-file format.

The component ``Configuration`` uses that package to provide configuration
information as appropriate for an event based system.

.. autoclass:: util.config.Configuration

The events used by the ``Configuration`` component are listed below.

.. autoclass:: util.config.ConfigurationEvent


