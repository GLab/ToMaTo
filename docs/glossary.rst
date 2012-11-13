.. _glossary:

Glossary
========

.. glossary::
   :sorted:

   Host
      A host is a physical machine (computer or server) that hosts parts of *topologies*.
      Each host is managed by one *host manager*.
      
   Backend
      The backend is one of the parts of ToMaTo. It is the central part that manages all 
      *resources*, *hosts*, *topologies* and users. In a ToMaTo-setup the backend is the only
      part that can only exist once. The backend uses the capabilities of one or more *hosts* to 
      offer *topologies* to its users through one or more *frontends*.

   Host manager (or Hostmanager)
      The host manager is one of the parts of ToMaTo. It has exclusive control over one *host* and
      offers its capabilities to one or more *backends*.

   Frontend
      ToMaTo frontends are a part of ToMaTo. Frontends connect to the *backend* and give users
      access to its capabilties by using the *backend API* and the users credentials. Several 
      frontends exist (e.g. web-frontend and CLI) and can access a *backend* in parallel.

   CLI
      The command-line interface is a simple way to control both the *backend* and the 
      *hostmanager*. It is one of the *frontends*.

   API
      API is short for "Application programming interface". Both the *backend* and the 
      *hostmanager* provide APIs with which they can be used.
      
   Entity
      An entity is a very general term for something that is controlled by either the *hostmanager*
      or the *backend*. This includes *elements*, *connections*, *topologies*, *users*, *resources*
      and much more.

   Topology
      A topology is a virtual network containing topology *components* (i.e. *elements* and 
      *connections*). For the user, a topology is a virtual world where he can run his experiment.

   Component
      A component is either an *element* or a *connection*.

   Element
      An element refers to virtual objects that the user can control. This includes end systems
      like virtual machine and scripts as well as networking components like switches, hubs or 
      routers. Each element can have several attributes and child elements (VMs have network
      interfaces as child elements) and one *connection*.

   Connection
      A connection is a relation between exactly two *elements*. The connnection can have 
      attributes of its own.
      
   Template
      Templates are pre-installed disk images for virtual machine *elements*. Depending on the VM
      technology different templates with different operating systems and software exist. For 
      *Repy* the template is the actual script that should be executed.
      
   Profile
      Profiles define the resource boundaries for virtual machine *elements*. Depending on the VM
      technology, profiles define different attributes like RAM limit, disk space and number of 
      CPUs.
      
   Resource
      Resources are a generic *entity* type for things that are present at *hosts* and can be used
      by *elements*. This includes *templates*, external networks but also available port numbers.
      
   KVM
      KVM devices are heavy-weight virtual machines that emulate a whole computer with generic 
      hardware. Most things that are possible on physical computers is also possible on KVM. 
      Most operating systems run on KVM.
   
   OpenVZ
      OpenVZ devices are light-weight virtual machines that translate kernel calls to kernel calls
      of the host kernel. OpenVZ offers complete usermode access to the virtual machines and a
      limited kernel-mode access.
   
   Repy
      Programmable devices are essentially scripts that can work with networking packages. These
      scripts can be written in a Python dialect called Repy and can read and write raw Ethernet
      packets to/from their network interfaces. Programmable devices are very light-weight as they
      are just small Python scripts.
      
   Dict
      Dicts are key-value mappings in the python programming language. In a dict, each key has 
      a value assigned to it. When used in an *API*, the keys are limited to strings and the
      keys are limited to serializable objects (numbers, strings, booleans, None, lists, dicts).
      