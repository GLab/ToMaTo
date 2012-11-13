Device Templates
================


Template distribution
---------------------
The device templates are distributed using the bittorrent protocol. This way the templates can be 
distributed among the hosts without a noteworthy central component. 

For the bittorrent disctribution the backend and all hosts run a bittorrent client that 
automatically downloads and uploads the contents of torrent files in a certain directory.
The backend also runs a so called bittorrent tracker, i.e. a central registry for the bittrorrent
protocol that keeps track of all available peers for a torrent file.

The backend periodically checks that all templates are known to all hosts and are up-to-date. 
Otherwise the backend will create resource entries for the missing templates containing the torrent
information. Since the torrent information has a size of several KiB (depending on the content 
size) the host will include an MD5 hash in its information and the backend will only update the
torrent information when it does not match the hash.

The host will periodically check the file size of the templates and compare them to the information
given in the torrent file to determine if the download has finished.



Template setup
--------------
To make them easier for users, templates should follow some common priciples.

1. Templates should be **secure by default**. This means that by default templates should only run 
   services that are essential to the function of the template. For Linux templates that means 
   that the SSH server will be deactivated by default and has to be activated manually by the 
   user.

2. Templates should **only contain needed modifications**. This means that a template should match 
   the default version of the operating system except where adaptations are needed. This should 
   help users that are already familiar with the operating system to use a template of that OS.

3. Templates should **be as small as possible**. This means that templates will be compressed to 
   save space and only include useful software. For some operating systems this might mean to 
   remove some drivers and software that will never be used, to save space.

4. Templates should be **international but work in Germany**. The language for all templates should 
   be set to american english but the keyboard layout should be set to german. 

5. Templates should be **self-explaining and helpful**. That means that templates should contain 
   some documentation on their special features and how to use them.

6. Templates should **not assume internet access**. Without internet access the templates should 
   still work unless they explicitly require an external service in the internet.

7. Templates should **use DHCP**. All existing interfaces should be configured using DHCP. 
   Hostname, DNS and time servers should also be used if included in the DHCP offer.

8. Templates should **require no login for local users and use a default password**. This means 
   that local users (via VNC) should be loggen in directly without entering a username or password.
   If a password is needed for some actions, the password should be the same for all templates.
   Note that templates still must be secured against the network and require passwords for 
   non-local login.

9. Templates should **include useful tools**. Not all devices will have internet access so 
   templates should already include the most useful tools that users want installed. There is a 
   clear trade-off between keeping a template small and including useful tools.

10. Templates should be **updated regularely**. This is important in two cases:

    a) If the device has internet access, it is important that the template is up-to-date so that 
       is initially secure. After device preparation, the user will have the responsibility to keep
       the system updated but it should be secure to start with.

    b) If the device does not have internet access, it is important that the template is not 
       outdated because the user can not easily update it. 


Template generation
-------------------
Scripts that can help to create and clean up templates can be found in the repository in the 
directory ``contrib``. The scripts ``create_kvm_template.sh`` and ``create_openvz_template.sh`` can
be used to create templates for debian-based systems in a semi-automatic way. The script 
``prepare_vm.sh`` can be used to adapt a running system to be a proper template.


Torrent creation
****************
Torrent files for templates can be created using the command ::

    btmakemetafile TRACKERURL FILENAME
    
where TRACKERURL is the URL of the tracker and FILENAME is the name of the template file.
The result will be a torrent file, that is named like the template file with ``.torrent`` appended.

.. note::
   
   The ToMaTo backend includes a tracker that can be used for template torrents. Its URL can be determined by
   the backend API call :py:func:`backend.tomato.api.host.server_info`.