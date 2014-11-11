XML-RPC Interface
=================

The interface is an RPC interface, i.e. it offers a set of methods that can be called (with parameters) and that return a return value. The internal data format is XML but this should be transparent. The interface adheres the `XML-RPC <http://www.xml-rpc.com>`_ standard with the following modifications:

* It uses an `extension for null-value encoding <http://ontosys.com/xml-rpc/extensions.php>`_ that is not part of the standard. This extension is part of many implementations since the absence of the feature is seen as a flaw in the standard.
* It uses a special parameter encoding that allows for keyword arguments. If exactly two parameters are given, where the first one is a list and the second one is key/value-map the keyword mode is used. In the keyword mode, the first parameter (the list) is expanded and used as normal positional arguments nad the second argument (the key/value-map) is expanded and used as the keyword arguments.
