Hostmanager Installation
========================

The hostmanager offers the virtualization technology found on the host to backends.
For simple installation of the hostmanager, it has been packaged for Debian systems.


Installation on Debian systems 
------------------------------

All of the following commands must be issued as **root**.

1. Adding the repository

  ToMaTo has its own repository for debian packages that needs to be added in order
  to install its packages. ::

    echo 'deb http://dswd.github.com/ToMaTo/repository/deb stable main' > /etc/apt/sources.list.d/tomato.list
  

2. Accepting the repository key

  Since all packages are signed with keys, the repository key must be accepted once, 
  otherwise the Debian package manager will complain on every update that the package
  is unauthorized. ::
  
    wget http://dswd.github.com/ToMaTo/repository/key.gpg -O - | apt-key add -


3. Updating the package lists

  ::

    apt-get update


4. Installing the Hostmanager package 

  ::

    apt-get install tomato-hostmanager

  During the configuration phase of this package, dialogs will appear and propmt for
  information. All of these prompts can be answered by pressing *enter*.



Installation on Proxmox systems
-------------------------------
The target platform for the hostmanager is `Proxmox VE <http://pve.proxmox.com>`_ 
so there exists a meta-package specifically for Proxmox systems, that installs all
additional software that is needed to use the full potential of Proxmox systems.

To install the hostmanager on Proxmox systems, the **steps 1 to 4 from above** have to be
executed. Additionally the package ``tomato-host-proxmox`` has to be installed::

  apt-get install tomato-host-proxmox



After the installation
----------------------
Some steps are needed to finalize the installation:

 * Installation of additional packages so that more :doc:`elements/index` and 
   :doc:`connections/index` become available. (For Proxmox hosts, the package
   ``tomato-host-promxmox`` installs all needed software.
 * :doc:`configuration`
 * :doc:`backends`