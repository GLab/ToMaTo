from topology_role import Role

class Flags:
	Debug = "debug"
	ErrorNotify = "error_notify"
	NoTopologyCreate = "no_topology_create"
	OverQuota = "over_quota"
	NewAccount = "new_account"
	RestrictedProfiles = "restricted_profiles"
	RestrictedTemplates ="restricted_templates"
	RestrictedNetworks ="restricted_networks"
	NoMails = "nomails"
	GlobalAdmin = "global_admin" #alle rechte fuer alle vergeben
	GlobalHostManager = "global_host_manager"
	GlobalToplOwner = "global_topl_owner"
	GlobalToplManager = "global_topl_manager"
	GlobalToplUser = "global_topl_user"
	GlobalHostContact = "global_host_contact"
	GlobalAdminContact = "global_admin_contact"
	OrgaAdmin = "orga_admin" #nicht "global-" rechte vergeben fuer eigene user (auch nicht debug)
	OrgaHostManager = "orga_host_manager" # eigene orga, hosts und sites verwalten
	OrgaToplOwner = "orga_topl_owner"
	OrgaToplManager = "orga_topl_manager"
	OrgaToplUser = "orga_topl_user"
	OrgaHostContact = "orga_host_contact"
	OrgaAdminContact = "orga_admin_contact"

	@staticmethod
	def get_max_topology_flags(flags):
		"""
		select the maximum permissions for topologies for global and organization-internal
		:param list(str) flags: user flags
		:return: maximum global permission, maximum orga-internal permission
		:rtype: tuple(bool)
		"""
		max_global = "null"
		max_orga = "null"
		for flag in [Flags.GlobalToplUser, Flags.GlobalToplManager, Flags.GlobalToplOwner]:
			if flag in flags:
				max_global = flag
		for flag in [Flags.OrgaToplUser, Flags.OrgaToplManager, Flags.OrgaToplOwner]:
			if flag in flags:
				max_orga = flag
		return Role.from_user_flag(max_global), Role.from_user_flag(max_orga)

	@staticmethod
	def to_topology_role(flag):
		"""
		convert a Topology permission flag (e.g., OrgaToplUser) to a topology Role
		:param str flag: flag
		:return: corresponding Role
		:rtype: str
		"""
		if flag in (Flags.GlobalToplOwner, Flags.OrgaToplOwner):
			return Role.owner
		if flag in (Flags.GlobalToplManager, Flags.OrgaToplManager):
			return Role.manager
		if flag in (Flags.GlobalToplUser, Flags.OrgaToplUser):
			return Role.user
		return Role.null

flags = {
	Flags.Debug: "Debug: See everything",
	Flags.ErrorNotify: "ErrorNotify: receive emails for new kinds of errors",
	Flags.NoTopologyCreate: "NoTopologyCreate: Restriction on topology_create",
	Flags.OverQuota: "OverQuota: Restriction on actions start, prepare and upload_grant",
	Flags.NewAccount: "NewAccount: Account is new, just a tag",
	Flags.RestrictedProfiles: "RestrictedProfiles: Can use restricted profiles",
	Flags.RestrictedTemplates:"RestrictedTemplates: Can use restricted templates",
	Flags.RestrictedNetworks:"RestrictedNetworks: Can use restricted Networks",
	Flags.NoMails: "NoMails: Can not receive mails at all",
	Flags.GlobalAdmin: "GlobalAdmin: Modify all accounts",
	Flags.GlobalHostManager: "GlobalHostsManager: Can manage all hosts and sites",
	Flags.GlobalToplOwner: "GlobalToplOwner: Owner for every topology",
	Flags.GlobalToplManager: "GlobalToplManager: Manager for every topology",
	Flags.GlobalToplUser: "GlobalToplUser: User for every topology",
	Flags.GlobalHostContact: "GlobalHostContact: User receives mails about host problems",
	Flags.GlobalAdminContact: "GlobalAdminContact: User receives mails to administrators",
	Flags.OrgaAdmin: "OrgaAdmin: Modify all accounts of a specific organization",
	Flags.OrgaHostManager: "OrgaHostsManager: Can manage all hosts and sites of a specific organization",
	Flags.OrgaToplOwner: "OrgaToplOwner: Owner for every topology of a specific organization",
	Flags.OrgaToplManager: "OrgaToplManager: Manager for every topology of a specific organization",
	Flags.OrgaToplUser: "OrgaToplUser: User for every topology of a specific organization",
	Flags.OrgaHostContact: "OrgaHostContact: User receives mails about host problems of a specific organization",
	Flags.OrgaAdminContact: "OrgaAdminContact: User receives mails to a specific organization"
}

categories = [
			{'title': 'manager_user_global',
			 'onscreentitle': 'Global User Management',
			 'flags': [
						Flags.GlobalAdmin,
						Flags.GlobalToplOwner,
						Flags.GlobalToplManager,
						Flags.GlobalToplUser,
						Flags.GlobalAdminContact
						]},
			{'title': 'manager_user_orga',
			 'onscreentitle': 'Organization-Internal User Management',
			 'flags': [
						Flags.OrgaAdmin,
						Flags.OrgaToplOwner,
						Flags.OrgaToplManager,
						Flags.OrgaToplUser,
						Flags.OrgaAdminContact
						]},
			{'title': 'manager_host_global',
			 'onscreentitle': 'Global Host Management',
			 'flags': [
						Flags.GlobalHostManager,
						Flags.GlobalHostContact
						]},
			{'title': 'manager_host_orga',
			 'onscreentitle': 'Organization-Internal Host Management',
			 'flags': [
						Flags.OrgaHostManager,
						Flags.OrgaHostContact
						]},
			{'title': 'error_management',
			 'onscreentitle': 'Error Management',
			 'flags': [
						Flags.Debug,
						Flags.ErrorNotify
						]},
			{'title': 'user',
			 'onscreentitle': 'User Settings',
			 'flags': [
						Flags.NoTopologyCreate,
						Flags.OverQuota,
						Flags.RestrictedProfiles,
						Flags.RestrictedTemplates,
						Flags.RestrictedNetworks,
						Flags.NewAccount,
						Flags.NoMails
						]}
			]


orga_admin_changeable = [Flags.NoTopologyCreate, Flags.OverQuota, Flags.NewAccount,
						Flags.RestrictedProfiles, Flags.RestrictedTemplates, Flags.RestrictedNetworks, Flags.NoMails, Flags.OrgaAdmin, Flags.OrgaHostManager,
						Flags.OrgaToplOwner, Flags.OrgaToplManager, Flags.OrgaToplUser,
						Flags.OrgaHostContact, Flags.OrgaAdminContact]
global_pi_flags = [Flags.GlobalAdmin, Flags.GlobalToplOwner, Flags.GlobalAdminContact]
global_tech_flags = [Flags.GlobalHostManager, Flags.GlobalHostContact]
orga_pi_flags = [Flags.OrgaAdmin, Flags.OrgaToplOwner, Flags.OrgaAdminContact]
orga_tech_flags = [Flags.OrgaHostManager, Flags.OrgaHostContact]