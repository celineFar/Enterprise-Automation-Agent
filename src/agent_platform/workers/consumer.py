"""Worker consumer boundary.

Consumers added here receive narrow repository, adapter, or handler contracts through
their constructors. They must not import or accept the process application container;
the worker entry point resolves their dependencies at startup.
"""
