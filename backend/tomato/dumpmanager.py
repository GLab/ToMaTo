import time, zlib, threading, thread, base64
from django.db import models
from .lib import anyjson as json

import host
from .lib import attributes, db, keyvaluestore  # @UnresolvedImport
from . import scheduler, config, currentUser
from .lib.error import InternalError, UserError  # @UnresolvedImport


# Zero-th part: database stuff

class ErrorGroup(models.Model):
    group_id = models.CharField(max_length=255, primary_key=True)
    description = models.CharField(max_length=255)
    removed_dumps = models.IntegerField(default=0)
    # dumps: [ErrorDump]

    def update_description(self, description):
        self.description = description
        self.save()

    def shrink(self):
        c = self.dumps.count()
        if c > 10:
            torem = self.dumps.order_by('timestamp')[5:c - 5]
            self.removed_dumps += torem.count()
            self.dumps.filter(pk__in=list(torem.values_list("id", flat=True))).delete()
            self.save()


    def info(self):
        res = {
        'group_id': self.group_id,
        'description': self.description,
        'count': self.removed_dumps,
        'last_timestamp': 0,
        'data_available': False,
        'dump_contents': {}
        }

        select_unique_values = ['software_version', 'source', 'type', 'description']
        for val in select_unique_values:
            res['dump_contents'][val] = []

        for dump in self.dumps.all():
            res['count'] += 1
            dmp = dump.info()
            if dmp['data_available']:
                res['data_available'] = True
            if dmp['timestamp'] > res['last_timestamp']:
                res['last_timestamp'] = dmp['timestamp']
            for val in select_unique_values:
                if not dmp[val] in res['dump_contents'][val]:
                    res['dump_contents'][val].append(dmp[val])

        return res

    def remove(self):
        InternalError.check(list(self.dumps.all()) == [], code=InternalError.INVALID_STATE,
                            message="Group is not empty")
        self.delete()


def create_group(group_id, description=None):
    desc = description or group_id
    if isinstance(desc, dict) and "message" in desc:
        desc = desc["message"]
    if not isinstance(desc, str):
        desc = str(desc)
    if len(desc) > 100:
        desc = desc[:100] + " ..."
    if not desc:
        desc = group_id
    gr = ErrorGroup.objects.create(
        group_id=group_id,
        description=desc
    )
    gr.save()
    return gr


def get_group(group_id):
    try:
        return ErrorGroup.objects.get(group_id=group_id)
    except ErrorGroup.DoesNotExist:
        return None
    #


def getAll_group():
    return ErrorGroup.objects.all()


def remove_group(group_id):
    grp = get_group(group_id)
    if grp is not None:
        grp.remove()
        return True
    return False


class ErrorDump(attributes.Mixin, models.Model):
    source = models.CharField(max_length=255)
    dump_id = models.CharField(max_length=255)
    group = models.ForeignKey(ErrorGroup, related_name="dumps")
    description = db.JSONField()
    attrs = db.JSONField(default={})
    data = attributes.attribute("data", unicode, None)
    data_available = attributes.attribute("data_available", bool, False)
    type = attributes.attribute("origin", unicode, "")
    software_version = attributes.attribute("software_version", dict, "")
    timestamp = models.IntegerField(default=0)

    class Meta:
        unique_together = (("source", "dump_id"))

    def getSource(self):
        return find_source_by_name(self.source)

    def modify_data(self, data, is_compressed=True):
        if data is None:
            self.data = None
            self.data_available = False
            self.save()
            return
        data_toinsert = None
        if is_compressed:
            data_toinsert = data
        else:
            data_toinsert = base64.b64encode(zlib.compress(json.dumps(data), 9))
        self.data = data_toinsert
        self.data_available = True
        self.save()

    def fetch_data_from_source(self):
        d = None
        found_data = False
        try:
            d = self.getSource().dump_fetch_with_data(self.dump_id, True)
            found_data = True
        except InternalError:
            pass
        if found_data:
            self.modify_data(d['data'], True)

    def info(self, include_data=False):
        dump = {
        'source': self.source,
        'dump_id': self.dump_id,
        'group_id': self.group.group_id,
        'group_description': self.group.description,
        'description': self.description,
        'type': self.type,
        'software_version': self.software_version,
        'timestamp': self.timestamp
        }
        if include_data:
            if not self.data_available:
                self.fetch_data_from_source()

        if include_data and self.data_available:
            dump['data'] = json.loads(zlib.decompress(base64.b64decode(self.data)))
        else:
            dump['data_available'] = self.data_available
        return dump

    def remove(self):
        self.delete()


def create_dump(dump, source, nosave=False):
    d = ErrorDump.objects.create(
        source=source.dump_source_name(),
        dump_id=dump['dump_id'],
        group_id=dump['group_id']
    )
    d.timestamp = dump['timestamp']
    d.description = dump['description']
    d.type = dump['type']
    d.software_version = dump['software_version']
    if not nosave:
        d.save()
    return d


def get_dump(source_name, dump_id):
    try:
        return ErrorDump.objects.get(source=source_name, dump_id=dump_id)
    except ErrorDump.DoesNotExist:
        return None


def getAll_dumps():
    return ErrorDump.objects.all()


def remove_dump(source_name, dump_id):
    dmp = get_dump(source_name, dump_id)
    if dmp is not None:
        dmp.remove()
        return True
    return False


# First part: fetching dumps from all the sources.



#this class should not be instantiated. There are two subclasses available: one that can connect to a host, and one that connects to this backend.
class DumpSource:
    #dump_last_fetch = None

    #to be implemented in subclass
    #fetches all dumps from the source, which were thrown after *after*.
    #after is a float and will be used unchanged.
    #if this throws an exception, the fetching is assumed to have been unsuccessful.
    def dump_fetch_list(self, after):
        return None

    def dump_get_last_fetch(self):
        return None

    #to be implemented in subclass
    #fetches all data about the given dump.
    #if this throws an exception, the fetching is assumed to have been unsuccessful.
    def dump_fetch_with_data(self, dump_id, keep_compressed=True):
        return None

    #to be implemented in a subclass
    #if the source has its clock before the backend, and an error is thrown in exactly this difference,
    #the dump would be skipped.
    #Thus, use the known clock offset to fetch dumps that might have occurred in this phase (i.e., right after the last fetch)
    #returns a float. should be ==0 if the source's clock is ahead, and >0 if the source's clock is behind
    def dump_clock_offset(self):
        return None

    #to be implemented in a subclass
    #returns a string to uniquely identify the source
    def dump_source_name(self):
        return None

    #override for HostDumpSource. Return true if the given host is this one
    def dump_matches_host(self, host_obj):
        return False

    #override in subclass
    def dump_set_last_fetch(self, last_fetch):
        return

    def dump_getUpdates(self):
        this_fetch_time = time.time() - self.dump_clock_offset()
        try:
            fetch_results = self.dump_fetch_list(self.dump_get_last_fetch())
            if len(
                    fetch_results) > 0:  #if the list is empty, no need to set this. However, if the list is empty for incorrect reasons (i.e., errors),
                #we may still be able to get the dumps when the error is resolved.
                self.dump_set_last_fetch(this_fetch_time)
            return fetch_results
        except Exception, exc:
            InternalError(code=InternalError.UNKNOWN, message="Failed to retrieve dumps: %s" % exc,
                          data={"source": repr(self)}).dump()
            return []


#fetches from this backend
class BackendDumpSource(DumpSource):
    keyvaluestore_key = "dumpmanager:lastBackendFetch"

    def dump_fetch_list(self, after):
        import dump

        return dump.getAll(after=after, list_only=False, include_data=False, compress_data=True)

    def dump_fetch_with_data(self, dump_id, keep_compressed=True):
        import dump

        d = dump.get(dump_id, include_data=True, compress_data=True)
        if not keep_compressed:
            d['data'] = json.loads(zlib.decompress(base64.b64decode(d['data'])))
        return d

    def dump_clock_offset(self):
        return 0

    def dump_source_name(self):
        return "backend"

    def dump_set_last_fetch(self, last_fetch):
        keyvaluestore.set(self.keyvaluestore_key, last_fetch)

    def dump_get_last_fetch(self):
        return keyvaluestore.get(self.keyvaluestore_key, 0)


backend_dumpsource = BackendDumpSource()


def getDumpSources():
    sources = [backend_dumpsource]
    hosts = host.getAll()
    for h in hosts:
        if h.enabled:
            sources.append(h)
    return sources

#only one thread may write to the dump table at a time.
lock_db = threading.RLock()


def find_source_by_name(source_name):
    for s in getDumpSources():
        if s.dump_source_name() == source_name:
            return s
    return None


def insert_dump(dump, source, nosave=False):
    with lock_db:
        source_name = source.dump_source_name()
        must_fetch_data = False

        #check whether a dump from the source with given dump_id exists. if so, don't do anything
        if get_dump(source_name, dump['dump_id']) is not None:
            return

        # check whether the group ID already exists. If not, create it,
        # remember to fetch dump data in the end, and email developer users
        if get_group(dump['group_id']) is None:
            from auth import mailFlaggedUsers, Flags

            must_fetch_data = True
            create_group(dump['group_id'], dump['description'])
            mailFlaggedUsers(Flags.ErrorNotify, "[ToMaTo Devs] New Error Group",
                             "A new group of error has been found, with ID %s. It has first been observed on %s." % (
                             dump['group_id'], source.dump_source_name()))

        #insert the dump.
        dump_db = create_dump(dump, source, nosave=nosave)

        #if needed, load data
        if must_fetch_data:
            dump_db.fetch_data_from_source()


def update_source(source):
    try:
        new_entries = source.dump_getUpdates()
        for e in new_entries:
            insert_dump(e, source, nosave=True)
    finally:
        for group in getAll_group():
            with lock_db:
                group.shrink()


def update_all(async=True):
    def cycle_all():
        for s in getDumpSources():  #a removed host while iterating is caught by this, since dumpSource.getUpdates() will return [] in this case
            if async:
                thread.start_new_thread(update_source,
                                        (s,))  #host might need longer to respond. no reason not to parallelize this
            else:
                update_all(s)
            if async:
                time.sleep(1)  #do not connect to all hosts at the same time. There is no need to rush.

    if async:
        thread.start_new_thread(cycle_all, ())
    else:
        cycle_all()
    return len(getDumpSources())


def init():
    scheduler.scheduleRepeated(config.DUMP_COLLECTION_INTERVAL, update_all, immediate=True)


# Second Part: Access to known dumps for API

def checkPermissions():
    from auth import Flags

    user = currentUser()
    UserError.check(user, code=UserError.NOT_LOGGED_IN, message="Unauthorized")
    UserError.check(user.hasFlag(Flags.Debug), code=UserError.DENIED, message="Not enough permissions")
    return True


def api_errorgroup_list(show_empty=False):
    if checkPermissions():
        with lock_db:
            res = []
            for grp in getAll_group():
                if show_empty or (grp.dumps.count() > 0):
                    res.append(grp.info())
            return res


def api_errorgroup_modify(group_id, attrs):
    if checkPermissions():
        with lock_db:
            for i in attrs.keys():
                UserError.check(i == "description", code=UserError.UNSUPPORTED_ATTRIBUTE,
                                message="Unsupported attribute for error group", data={"attribute": i})
            grp = get_group(group_id)
            UserError.check(grp is not None, code=UserError.ENTITY_DOES_NOT_EXIST, message="error group does not exist",
                            data={"group_id": group_id})
            grp.update_description(attrs['description'])


def api_errorgroup_info(group_id, include_dumps=False):
    if checkPermissions():
        with lock_db:
            group = get_group(group_id)
            UserError.check(group is not None, code=UserError.ENTITY_DOES_NOT_EXIST,
                            message="error group does not exist", data={"group_id": group_id})
            res = group.info()
            if include_dumps:
                res['dumps'] = []
                for i in group.dumps.all():
                    res['dumps'].append(i.info())
            return res


def api_errorgroup_remove(group_id):
    if checkPermissions():
        with lock_db:
            res = remove_group(group_id)
            UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="error group does not exist",
                            data={"group_id": group_id})


def api_errordump_list(group_id=None, source=None, data_available=None):
    if checkPermissions():
        with lock_db:
            dumps = getAll_dumps()
            res = []
            for d in dumps:
                di = d.info(include_data=False)

                append_to_res = True
                if not group_id is None and di['group_id'] != group_id:
                    append_to_res = False
                if not source is None and di['source'] != source:
                    append_to_res = False
                if not data_available is None and di['data_available'] != data_available:
                    append_to_res = False

                if append_to_res:
                    res.append(di)
            return res


def api_errordump_info(source, dump_id, include_data=False):
    if checkPermissions():
        with lock_db:
            res = get_dump(source, dump_id).info(include_data=include_data)
            UserError.check(res is not None, code=UserError.ENTITY_DOES_NOT_EXIST, message="error dump does not exist",
                            data={"dump_id": dump_id, "source": source})
            return res


def api_errordump_remove(source, dump_id):
    if checkPermissions():
        with lock_db:
            res = remove_dump(source, dump_id)
            UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="error dump does not exist",
                            data={"dump_id": dump_id, "source": source})


def api_force_refresh():
    if checkPermissions():
        return update_all(async=False)
