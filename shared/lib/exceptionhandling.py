import logging
import error
import traceback
import sys


def wrap_and_handle_current_exception(errorcls_func=None, errorcode=None, re_raise=True, log_exception=True, dump_exception=True, print_exception=True, ignore_todump=False, data=None):
	if data is None:
		data = {}
	type_, exc, trace = sys.exc_info()
	if errorcls_func is None:
		errorcls_func = lambda e: error.InternalError
	if isinstance(exc, error.Error):
		if exc.todump:
			writedown_current_exception(log_exception=log_exception, dump_exception=dump_exception, print_exception=print_exception, exc=exc, ignore_todump=ignore_todump)
		if re_raise:
			raise
	else:
		newexc = errorcls_func(exc).wrap(exc, code=errorcode, data=data)
		writedown_current_exception(log_exception=log_exception, dump_exception=dump_exception and newexc.todump,
		                            print_exception=print_exception, exc=exc, ignore_todump=ignore_todump)
		if re_raise:
			newexc.todump = False
			raise newexc.__class__, newexc, trace

def writedown_current_exception(log_exception=True, dump_exception=True, print_exception=True, exc=None, ignore_todump=False):
	if exc is None:
		_, exc, _ = sys.exc_info()

	if isinstance(exc, error.Error):
		if not exc.todump and not ignore_todump:
			return

	if log_exception:
		logging.logException()
	if dump_exception:
		import dump
		dump.dumpException()
	if print_exception:
		traceback.print_exc()

	if isinstance(exc, error.Error):
		exc.todump = False


def wrap_errors(errorcls_func=None, errorcode=None, log_exception=True, dump_exception=True, print_exception=True):
	"""
	wrapper that wraps exceptions to errors, and manages logging, dumping and printing
	makes sure that errors are only handled once.
	:param errorcls_func: Function that takes the exception, and returns a sublclass of Error.
												Usually, this has to decide whether this is an InternalError or UserError.
												Note that the chosen error class may disable dumping, even though it is set to true.
												This function will not be used when handling subclasses of Error
												By default, all Exceptions will be treated as InternalError
	:param errorcode: when using errorcls_func, this code will be used as Error.code
	:param log_exception: whether or not this exception will be logged (default: True)
	:param dump_exception: whether or not this exception will be dumped (default: True)
	:param print_exception: whether or not this exception will be printed to the console (default: True)
	:return:
	"""
	def w(func):
		def func_wrapper(*args, **kwargs):
			try:
				return func(*args, **kwargs)
			except:
				wrap_and_handle_current_exception(errorcls_func,
				                                  errorcode,
				                                  re_raise=True,
				                                  log_exception=log_exception,
				                                  dump_exception=dump_exception,
				                                  print_exception=print_exception,
				                                  data = {
					                                  "function": func.__name__,
					                                  "args": args,
					                                  "kwargs": kwargs
				                                  })
		func_wrapper.__name__ = func.__name__
		func_wrapper.__doc__ = func.__doc__
		func_wrapper.__module__ = func.__module__
		return func_wrapper
	return w


def on_error_continue(errorcls_func=None, errorcode=None, log_exception=True, dump_exception=True, print_exception=True, return_func=None):
	"""
	Similar to wrap_errors, but does not raise them after handling.
	If an error occurs, the decorated function returns a predefined value.
	:param errorcls_func: Function that takes the exception, and returns a sublclass of Error.
												Usually, this has to decide whether this is an InternalError or UserError.
												Note that the chosen error class may disable dumping, even though it is set to true.
												This function will not be used when handling subclasses of Error
												By default, all Exceptions will be treated as InternalError
	:param log_exception: whether or not this exception will be logged (default: True)
	:param dump_exception: whether or not this exception will be dumped (default: True)
	:param print_exception: whether or not this exception will be printed to the console (default: True)
	:param return_func: what to return on error. function that gets *args and **kwargs from this function, and returns a default value.
	                    This should be a simple function which throws no error.
	                    By default, this always returns None.
	:return:
	"""
	def w(func):
		def func_wrapper(*args, **kwargs):
			try:
				return func(*args, **kwargs)
			except:
				wrap_and_handle_current_exception(errorcls_func,
				                                  errorcode=errorcode,
				                                  re_raise=False,
				                                  log_exception=log_exception,
				                                  dump_exception=dump_exception,
				                                  print_exception=print_exception,
				                                  data = {
					                                  "function": func.__name__,
					                                  "args": args,
					                                  "kwargs": kwargs
				                                  })
				if return_func is None:
					return None
				else:
					return return_func(*args, **kwargs)
		func_wrapper.__name__ = func.__name__
		func_wrapper.__doc__ = func.__doc__
		func_wrapper.__module__ = func.__module__
		return func_wrapper
	return w
