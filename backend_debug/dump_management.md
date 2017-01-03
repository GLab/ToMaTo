**Dump Manager Overview**

The process of dump management can be modelled in multiple, consecutive steps:

* create dump
  * throw error
  * catch error
  * dump error

* collect dumps
  * access dump
  * transmit dump
  * store in dumpmanager
  
* view dumps
  * use dump manager in webfrontend or API



Dump creation must be done before a possible crash of the program.
Dump collection is done independent from a possible program crash.

**throw error**

Errors are usually thrown via the shared/lib/error.py module.
Other exceptions may be thrown and will also be collected, but usage of the error module 
is encouraged.

**catch error**

In order to be dumped, errors must be caught and given to the dump library.
This happens in shared/lib/exceptionhandling.py or web/tomato/lib/handleerror.py
Errors are automatically caught by RPC servers before sending a response.

Most meta-information and the group ID is calculated here, or in the Error constructor.

**dump error** and **access dump**

The shared/lib/dump.py module provides interfaces for managing dumps.
When an error is caught, it is passed to the dump module for storing.
When transmitting dumps, the dump module is used to access the list and content of dumps.

**transmit dump**

Collected dumps must be forwarded to the dumpmanager, which is located in backend_debug.
This step is highly dependent of the location of the component throwing the dumps.
To keep things easy, backend_debug transmits dumps like any other backend module.

*web*

The webfrontend uses the API's errordump_store command for storing error dumps.
This is the only way for communication between the webfrontend and backend_debug.

*autopushing backend modules*

Backend modules can be configured to automatically push error dumps.
This is handled by the shared/lib/dumps_autopush.py module.

*not-autopushing backend modules*

Backend modules that don't support autopushing or that are configured not
to automatically pushed are accessed by the dumpmanager via the internal backend API.
This is handled by backend_debug/tomato/dumpmanager/fetching.

*hostmanagers*

The backend_core component offers a backend-internal API call that collects dumps from a host.
The dumpmanager uses this API call to collect dumps from all hosts. The respective call is
directly forwarded to the hostmanager's API.
This is handled by backend_debug/tomato/dumpmanager/fetching.

**store in dumpmanager** and **view dumps**

When received by the dumpmanager, error dumps are grouped by their group_id and then
stored in backend_debug's database.
The backend_api component offers API calls to manage these.
The webfrontend offers a dump manager frontend. 
