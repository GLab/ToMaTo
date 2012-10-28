Backend management
==================

The hostmanager allows different backends to use it. 


Component seperation
--------------------
All components (i.e. elements and conections) of different backends are 
seperated by the hostmanager. Each component will have an owner attribute,
that references the backend that created it. The component will only be
visible and accessible by that backend.


Access control
--------------
The authetication of backends uses SSL keys. Each backend has a key of its own
and uses it to authenticate and encrypt connections to hostmanagers.
On the side of the hostmanager all backend keys must be present as files in 
*PEM format* in a specific directory (``/etc/tomato/client_certs`` in default
config). 


Indexing the backend keys
^^^^^^^^^^^^^^^^^^^^^^^^^
After modifying the SSL keys, the certificate index must be rebuilt. ::

  c_rehash /etc/tomato/client_certs

If a different directory has been set in the configuration file, it must be 
used here instead.

Note that the hostmanager does not have to be restarted after rebuilding the
index.
Also note that the hostmanager will issue the command to rebuild the 
certificate index automatically when it is starting.


Backend identification
^^^^^^^^^^^^^^^^^^^^^^
The identity of a backend is based on the *common name (CN)* in its 
certificate. Different certificates with the same common name field will be
treated as the same backend and share access to components.


Admin backend
^^^^^^^^^^^^^
Since resources are shared among all backends on a host, the hostmanager
requires administrative access to modify the resources. To establish this, 
certificates with a special common name (``admin`` as default) are granted
administrative access.


Generating a key-pair
^^^^^^^^^^^^^^^^^^^^^
A self-signed key-pair can be created with the following command::

  openssl req -new -x509 -days 1000 -nodes -out key.pem -keyout cert.pem

It is important to create a key without a password if the the key should be
used for a backend.