Integrated Fileserver
=====================
The backend has an integrated fileserver that allows ToMaTo users to upload and
download data files like disk images, packet capture files directly from/to the
hostmanager without indirection via the backend.


Access
------
The fileserver uses the HTTP protocol on a port set in the config file. The 
public address of the host and the fileserver port can obtained using the
API call :py:func:`hostmanager.tomato.api.host.host_info`.


.. automodule:: hostmanager.tomato.lib.cmd.fileserver