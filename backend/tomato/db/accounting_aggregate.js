function() {
  var now = options.now;
  var types = options.types;
  var keep_records = options.keep_records;
  var max_age = options.max_age;

  var combineRecords = function(records) {
    var measurements = 0;
    var usage = {m: 0, d: 0, t: 0, c: 0};
    for (var i=0; i < records.length; i++) {
      var r = records[i];
      measurements += r.m;
      usage.m += r.u.m * r.m;
      usage.d += r.u.d * r.m;
      usage.t += r.u.t;
      usage.c += r.u.c;
    }
    if (measurements > 0) {
      usage.d /= measurements;
      usage.m /= measurements;
    }
    return [usage, measurements];
  };

  var prevPoint = function(point, type) {
    var date = new Date(point*1000);
    switch (type) {
      case "5minutes":
        date.setUTCMinutes(date.getUTCMinutes()-5);
        break;
      case "hour":
        date.setUTCHours(date.getUTCHours()-1);
        break;
      case "day":
        date.setUTCDate(date.getUTCDate()-1);
        break;
      case "month":
        date.setUTCMonth(date.getUTCMonth()-1);
        break;
      case "year":
        date.setUTCFullYear(date.getUTCFullYear()-1);
        break;
    }
    return date.getTime()/1000;
  };

  var nextPoint = function(point, type) {
    var date = new Date(point*1000);
    switch (type) {
      case "5minutes":
        date.setUTCMinutes(date.getUTCMinutes()+5);
        break;
      case "hour":
        date.setUTCHours(date.getUTCHours()+1);
        break;
      case "day":
        date.setUTCDate(date.getUTCDate()+1);
        break;
      case "month":
        date.setUTCMonth(date.getUTCMonth()+1);
        break;
      case "year":
        date.setUTCFullYear(date.getUTCFullYear()+1);
        break;
    }
    return date.getTime()/1000;
  };

  var lastPoint = function(type) {
    var date = new Date(now*1000);
    date.setUTCMilliseconds(0);
    date.setUTCSeconds(0);
    switch (type) {
      case "5minutes":
        date.setUTCMinutes(Math.floor(date.getUTCMinutes()/5)*5);
        break;
      case "year":
        date.setUTCMonth(1);
      case "month":
        date.setUTCDate(1);
      case "day":
        date.setUTCHours(0);
      case "hour":
        date.setUTCMinutes(0);
    }
    return date.getTime()/1000;
  };

  var stats = {};
  db.usage_statistics.find().forEach(function(obj){ stats[obj._id]=obj; });

  var updateFrom = function(dst, srcs) {
    if (srcs.length == 0) return false;
    dst = stats[dst];
    for (var i=0; i<srcs.length; i++) {
      srcs[i] = stats[srcs[i]];
    }
    var changed = false;
    var minAll = lastPoint("5minutes") - 1800;
    var lastAll = lastPoint("5minutes");
    var latest = 0;
    for (var i=0; i<srcs.length; i++) {
      var l = srcs[i]["5minutes"];
      lastAll = Math.min(lastAll, (l && l.length > 0) ? l[l.length-1].e : minAll);
      latest = Math.max(latest, (l && l.length > 0) ? l[l.length-1].e : 0);
    }
    if (latest <= minAll) return false;
    lastAll = Math.max(lastAll, minAll);
    var list = dst["5minutes"];
    if (! list) list = [];
    var begin = list.length > 0 ? list[list.length-1].e : minAll;
    var end = nextPoint(begin, "5minutes");
    while (end <= lastAll) {
      var records = [];
      for (var i=0; i<srcs.length; i++) {
        var src = srcs[i]["5minutes"];
        if (! src) continue;
        for (var j=0; j<src.length; j++) {
          if (src[j].e == end) records.push(src[j]);
        }
      }
      if (records.length == 0) {
        begin = end;
        end = nextPoint(end, "5minutes");
        continue;
      }
      var t = combineRecords(records);
      var usage = t[0];
      var measurements = t[1];
      list.push({b: begin, e: end, m: measurements, u: usage});
      changed = true;
      begin = end;
      end = nextPoint(end, "5minutes");
    }
    if (changed) {
      dst["5minutes"] = list;
      db.usage_statistics.save(dst);
    }
    return changed;
  };

  var prepare = function(collection) {
    var data = {ids: [], dst: {}, srcs: {}};
    collection.find().forEach(function(obj) {
      data.ids.push(obj._id);
      data.srcs[obj._id] = [];
      data.dst[obj._id] = obj.total_usage;
    });
    return data;
  };

  var updateAll = function(data) {
    var count = 0;
    for (var i = 0; i < data.ids.length; i++) {
      var id = data.ids[i];
      if (updateFrom(data.dst[id], data.srcs[id])) count++;
    }
    return count;
  };

  var count = {};

  var elements = prepare(db.element);
  var connections = prepare(db.connection);
  var hosts = prepare(db.host);
  var topologies = prepare(db.topology);
  var users = prepare(db.user);
  var organizations = prepare(db.organization);

  db.host_element.find().forEach(function(obj) {
    if (obj.topology_element && elements.srcs[obj.topology_element]) elements.srcs[obj.topology_element].push(obj.usage_statistics);
    if (obj.topology_connection && connections.srcs[obj.topology_connection]) connections.srcs[obj.topology_connection].push(obj.usage_statistics);
    if (hosts.srcs[obj.host]) hosts.srcs[obj.host].push(obj.usage_statistics);
  });
  db.connection_element.find().forEach(function(obj) {
    if (obj.topology_element && elements.srcs[obj.topology_element]) elements.srcs[obj.topology_element].push(obj.usage_statistics);
    if (obj.topology_connection && connections.srcs[obj.topology_connection]) connections.srcs[obj.topology_connection].push(obj.usage_statistics);
    if (hosts.srcs[obj.host]) hosts.srcs[obj.host].push(obj.usage_statistics);
  });
  db.element.find().forEach(function(obj) {
    if (topologies.srcs[obj.topology]) topologies.srcs[obj.topology].push(obj.total_usage);
  });
  db.topology.find().forEach(function(obj) {
    for (var i=0; i<obj.permissions.length; i++) {
      var perm = obj.permissions[i];
      if (perm.role == 'owner' && users.srcs[perm.user]) users.srcs[perm.user].push(obj.total_usage);
    }
  });
  db.user.find().forEach(function(obj) {
    if (organizations.srcs[obj.organization]) organizations.srcs[obj.organization].push(obj.total_usage);
  });

  count["elements"] = updateAll(elements);
  count["connections"] = updateAll(connections);
  count["hosts"] = updateAll(hosts);
  count["topologies"] = updateAll(topologies);
  count["users"] = updateAll(users);
  count["organizations"] = updateAll(organizations);

  return count;
}
