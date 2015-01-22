try:
	import cProfile as profiling
except ImportError:
	import profile as profiling

import time, sys, pstats, traceback

class ProfilingStatistics(pstats.Stats):
	def __init__(self, stats=None):
		class Dummy: pass
		dummy = Dummy()
		dummy.create_stats = lambda :None
		dummy.stats = stats or {}
		pstats.Stats.__init__(self, dummy)

	@classmethod
	def fromProfile(cls, profile):
		assert isinstance(profile, profiling.Profile)
		return cls(profile.stats)

	@classmethod
	def unmarshal(cls, data):
		stats = {}
		for e in data:
			subs = {}
			for s in e['subs']:
				subs[(s['file'], s['lineno'], s['method'])] = (s['calls'], s['ncalls'], s['time_sub'], s['time_int'])
			stats[(e['file'], e['lineno'], e['method'])] = (e['calls'], e['ncalls'], e['time_sub'], e['time_int'], subs)
		return cls(stats)

	def marshal(self):
		data = []
		for func, stats in self.stats.items():
			subs = []
			for sfunc, sstats in stats[4].items():
				subs.append({'file': sfunc[0], 'lineno': sfunc[1], 'method': sfunc[2], 'calls': sstats[0], 'ncalls':
					sstats[1], 'time_sub': sstats[2], 'time_int': sstats[3]})
			data.append({'file': func[0], 'lineno': func[1], 'method': func[2], 'calls': stats[0], 'ncalls': stats[1],
				'time_sub': stats[2], 'time_int': stats[3], 'subs': subs})
		return data


class ExceptionObj:
	def __init__(self, type, message, stackTrace):
		self.type = type
		self.message = message
		self.stackTrace = stackTrace

	@classmethod
	def current(cls):
		info = sys.exc_info()
		return cls(info[0].__name__, str(info[1]), StackTrace(traceback.extract_tb(info[2])))

	@classmethod
	def unmarshal(cls, data):
		return cls(data['type'], data['message'], StackTrace.unmarshal(data['stacktrace']))

	def marshal(self):
		return {'type': self.type, 'message': self.message, 'stacktrace': self.stackTrace.marshal()}

	def __str__(self):
		return str(self.stackTrace) + '\n' + '%s(%s)' % (self.type, self.message)

	def __repr__(self):
		return "%s(%s)" % (self.type, self.message)


class StackTrace:
	def __init__(self, stackTrace):
		self.stackTrace = stackTrace

	@classmethod
	def current(cls, truncate=True):
		stack = traceback.extract_stack()
		if truncate:
			stack.pop()
		return cls(stack)

	@classmethod
	def unmarshal(cls, data):
		return cls([(tb['file'], tb['lineno'], tb['method'], tb['line']) for tb in data])

	@classmethod
	def all(cls):
		return dict([(threadId, cls(traceback.extract_stack(stack))) for threadId, stack in sys._current_frames().items()])

	def marshal(self):
		return [{'file': tb[0], 'lineno': tb[1], 'method': tb[2], 'line': tb[3]} for tb in self.stackTrace]

	def __str__(self):
		return "Traceback (most recent call last):\n" + ("".join(traceback.format_list(self.stackTrace)))[:-1]


class DebugResult:
	def __init__(self, success, duration, result, exception, statistics):
		self.success = success
		self.duration = duration
		self.result = result
		assert isinstance(exception, ExceptionObj) or success
		self.exception = exception
		assert isinstance(statistics, ProfilingStatistics) or not statistics
		self.statistics = statistics

	@classmethod
	def unmarshal(cls, data):
		return cls(data['success'], data['duration'], data.get('result'),
				   ExceptionObj.unmarshal(data['exception']) if 'exception' in data else None,
					ProfilingStatistics.unmarshal(data['statistics']) if 'statistics' in data else None)

	def marshal(self):
		data = {'success': self.success, 'duration': self.duration}
		if self.success:
			data['result'] = self.result
		else:
			data['exception'] = self.exception.marshal()
		if self.statistics:
			data['statistics'] = self.statistics.marshal()
		return data


def run(func, args=None, kwargs=None, profile=False):
	args = args or []
	kwargs = kwargs or {}
	prof = None
	if profile:
		prof = profiling.Profile()
		prof.enable()
	start = time.time()
	try:
		success, value = True, func(*args, **kwargs)
	except:
		success, value = False, None
	end = time.time()
	if profile:
		prof.create_stats()
		statistics = ProfilingStatistics.fromProfile(prof)
	else:
		statistics = None
	exception = None if success else ExceptionObj.current()
	return DebugResult(success, end-start, value, exception, statistics)