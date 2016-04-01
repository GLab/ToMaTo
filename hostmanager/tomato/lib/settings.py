# this is a dummy to allow the hostmanager to start.

class settings:

	@staticmethod
	def get_tomato_module_name():
		return "Hostmanager"

	@staticmethod
	def get_dump_config():
		from .. import config
		return {
			"enabled":  True,
			"directory": config.DUMP_DIR,
			"lifetime": config.DUMP_LIFETIME
		}

class Config:
	DUMPS_DIRECTORY = "directory"
	DUMPS_LIFETIME = "lifetime"