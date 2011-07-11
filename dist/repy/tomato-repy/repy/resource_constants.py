"""
   Author: Justin Cappos

   Start Date: 8 Dec 2010   (Derived from nanny_resource_limits.py)

   Description:

   This class defines contants that specify information about resources.
   This includes the names of the different resources and their types.

"""





# These are resources that drain / replenish over time
renewable_resources = ['cpu', 'filewrite', 'fileread', 'netsend', 'netrecv',
	'loopsend', 'looprecv', 'lograte', 'random']

# These are resources where the quantity of use may vary by use 
quantity_resources = ["cpu", "memory", "diskused", "filewrite", "fileread", 
	'loopsend', 'looprecv', "netsend", "netrecv", "lograte", 'random']

# These are resources where the number of items is the quantity (events because
# each event is "equal", insockets because a listening socket is a listening 
# socket)
fungible_item_resources = ['events', 'filesopened', 'insockets', 'outsockets']

# resources where there is no quantity.   There is only one messport 12345 and
# a vessel either has it or the vessel doesn't.   The resource messport 12345
# isn't fungible because it's not equal to having port 54321.   A vessel may
# have more than one of the resulting individual resources and so are
# stored in a list.
individual_item_resources = ['messport', 'connport']

# Include resources that are fungible vs those that are individual...
item_resources = fungible_item_resources + individual_item_resources


# all resource names
known_resources = quantity_resources + item_resources 

# Whenever a resource file is attached to a vessel, an exception should
# be thrown if these resources are not present.  If any of these are left
# unassigned, mysterious node manager errors will arise -Brent
must_assign_resources = ["cpu", "memory", "diskused"]

