# Changelog

This file should be used to track all changes to ToMaTo in a similar way to [VpnCloud](https://github.com/dswd/vpncloud.rs/blob/master/CHANGELOG.md)
Entries should be prefixed with some tags:
- Status tags: `added`, `fixed`, `changed`, `removed`
- Component tags: `backend_api`, `backend_accounting`, `backend_core`, `backend_debug`, `backend_users`, `web`, `cli`, `hostmanager`, `misc`, `config`
Entries should be sorted by component and status with important entries and entries with multiple components being on top and **bold**.


### PLANNED UNTIL NEXT RELEASE

### UNRELEASED (NOT RUNNING ON SERVERS)

- [config, changed] In dumpmanager config section, api_store_secret_key must now be set.
- [backend_api, backend_debug, changed] Now allowing dump storing via API

### UNRELEASED (RUNNING ON SERVERS)

- [backend_api, fixed] Fixed __statistics__ API call
- [backend_api, fixed] Fixed authorization for download actions on elements
- [backend_api, changed] Removed configuration info calls
- [backend_core, fixed] Fixed topology removal
- [backend_core, fixed] Fixed an unnecessary dumped error that spammed dump management
- [backend_core, changed] Topology site setting is now applied on element prepare instead of element creation
- [backend_core, fixed] Now allowing deployment of elements on hosts where template is known but not yet fetched
- [web, changed] Added a hint for the packet filter syntax in connection settings
- [web, changed] Better debug dropdown menu for debug users
- [web, fixed] Average host load and availability on sites and organizations is now calculated correctly
- [web, fixed] Inter-site and intra-site statistics pages now work properly
- [cli, fixed] Updated template migration script to support URL-based templates

### Version 4.0 (Released 2016-07-18)
- **[backend, changed] Split backend into multiple services: backend_core, backend_accounting, backend_users and backend_debug under one central backend_api**
- **[backend_core, changed] Default switch type is now VpnCloud**
- **[backend_accounting, changed] Reimplemented accounting in Rust to be more efficient**
- **[hostmanager, backend_core, changed] Reimplemented template synchronization to be more reliable**
- **[any, added] Added lots of test cases to cover more scenarios**
- [backend_core, backend_users, web, added] New mandatory central config file and config parser.
- [backend_core, backend_users, web, changed] Complete rewrite of tomato-ctl.py
- [any, changed] Changed docker mount points of tomato code
- [any, added] Added reload capability for docker containers
- [backend_core, changed] Backend_core no longer uses two separate ssl keys
- [any, changed] Not using cache when building docker images so that most current packages get installed 
- [web, fixed] Fixed small menu display issue for vpncloud switches
- [web, fixed] Fixed small menu display issue for vpncloud switches
- [web, fixed] Fixed problem with default executable archives
- [web, changed] Regrouped editor options and soving some options in user object
- [backend_*, changed] Using \_\_slots\_\_ for generic classes, attributes and schemas and tasks to save space and increase performance
- [backend_*, changed] Dumping more errors
- [backend_*, removed] Removed useless dump environment infos
- [backend_*, fixed] Fixed profiling when server does not terminate
- [backend_debug, fixed] Fixed problem with dumping stack variables when dumping errors
- [backend_debug, fixed] Fixed problem with non-existing error groups
- [backend_core, fixed] Gracefully handling errors on topology timeout
- [backend_core, fixed] Gracefully handling errors on host component synchronization
- [backend_core, fixed] Fixed problem when stopping external networks with inconsistent states
- [backend_core, fixed] Fixed problem when generating vpncloud networkids
- [backend_core, fixed] Fixed problem with changing permissions
- [backend_core, fixed] Fixed problem with dumpmanager collecting errors
- [hostmanager, fixed] Fixed problem with vpncloud dropping ARP packets
- [misc, fixed] Fixed data link in tutorial
- [misc, removed] Abandoned CloudShark

