Backend management
==================

The hostmanager allows different backends to use it. 


Component separation
--------------------
All components (i.e. elements and connections) of different backends are 
separated by the hostmanager. Each component will have an owner attribute,
that references the backend that created it. The component will only be
visible and accessible by that backend.


Resource separation
-------------------
All resources (i.e. networks and templates) of different backends are 
separated by the hostmanager. Each resource will have an owner attribute,
that references the backend that created it. The resource will only be
visible and accessible by that backend.


Access control
--------------
The authentication of backends uses SSL keys. Each backend has a key of its own
and uses it to authenticate and encrypt connections to hostmanagers.
On the side of the hostmanager all backend keys must be present as files in 
*PEM format* in a specific directory (``/etc/tomato/client_certs`` in default
config). 


Indexing the backend keys
^^^^^^^^^^^^^^^^^^^^^^^^^
After modifying the SSL keys, the certificate index must be rebuilt. ::

  update-tomato-client-certs

Note that the hostmanager does not have to be restarted after rebuilding the
index.
Also note that the hostmanager will issue the command to rebuild the 
certificate index automatically when it is starting.


Backend identification
^^^^^^^^^^^^^^^^^^^^^^
The identity of a backend is based on the *common name (CN)* in its 
certificate. Different certificates with the same common name field will be
treated as the same backend and share access to components.


Generating a key-pair
^^^^^^^^^^^^^^^^^^^^^
A self-signed key-pair can be created with the following command::

  openssl req -new -x509 -days 1000 -nodes -out key.pem -keyout cert.pem

It is important to create a key without a password if the the key should be
used for a backend.