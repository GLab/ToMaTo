# this is a dummy to allow the hostmanager to start.

class Config:
	DUMPS_ENABLED = "enabled"
	DUMPS_DIRECTORY = "directory"
	DUMPS_LIFETIME = "lifetime"
	DUMPS_AUTO_PUSH = "auto-push"

class settings:

	@staticmethod
	def get_tomato_module_name():
		return "hostmanager"

	@staticmethod
	def get_dump_config():
		from .. import config
		return {
			"enabled":  True,
			"directory": config.DUMP_DIR,
			"lifetime": config.DUMP_LIFETIME,
			"auto-push": False
		}

	@staticmethod
	def get_db_settings():
		"""
		get database settings
		:return: dict containing 'database' (name), 'host' and 'port'
		:rtype: dict
		"""
		return {
			'database': "tomato_host",
			'host': "localhost",
			'port': 27017
		}
