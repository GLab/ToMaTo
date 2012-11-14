Accounting data types
=====================

Usage record
------------
A *usage record* represents a data set with usage statistics of a certain
time range. Each usage record has the following fields:

``type``:
  The *type* of a usage record describes the time frame which the record 
  covers. Possible values are ``single`` for a single measurement,
  ``5minutes``, ``hour``, ``day``, ``month`` and ``year`` for aggregated 
  values.
    
``begin`` and ``end``:
  The fields *begin* and *end* describe the covered time of the measurement.
  For a *single* measurement these fields specify the begin and the end of 
  the measurement execution for this single data point. For all other record 
  types these fields specify the time frame of aggregated measurements.
  Both fields are timestamps in the form if seconds since the epoch 
  (1970-01-01 00:00:00).
    
``measurements``:
  The field *measurements* contains the number of single data points that 
  are combined in the record. This field is ``1`` for all *single* records
  and contains the number of aggregated single records for all other types.
    
``usage``:
  This field describes the resource usage during the given time period. For
  *single* records this time period is the period between the measurement and
  the last single measurement. For all other types, the time period is the
  combined time period of the aggregated *single* records.
  The field *usage* is a dict containing the following fields:
    
  ``cputime``:
    This field contains the used CPU time in seconds as a float value. CPU 
    time is automatically measured by the operating system, so the 
    measurement results do not depend in measurement timing. Even bigger
    gaps in measurement do not cause inaccurate values.
    Note that CPU time is calculated per core, so it is possible to consume 
    several seconds of CPU time during one second.
    
  ``memory``:
    This field contains the used memory (RAM) in bytes. Memory consumption is
    measured on certain measurement points and the different data points are
    averaged into aggregated values. 
  
  ``diskspace``:
    This field contains the used disk space in bytes. The measurement is 
    similar to that of the *memory* field.
    
  ``traffic``:
    This field contains the traffic volume in bytes. Like *cputime*, traffic
    is automatically measured by the operating system and the values are
    very accurate because of this.
    
  Note that because of different nature of the resources *cputime* and 
  *traffic* are summed up during aggregation while *memory* and *diskspace*
  are averaged.  


Usage statistics
----------------
The usage statistics data structure contains a set of *usage records*.
Usage statistics objects are dict structures that contain the *types* of the
usage records as keys and a list of usage records with that type as value.
  
Example
-------
::

    {
      "5minutes": [], 
      "hour": [], 
      "month": [], 
      "single": [
        {
          "usage": {
            "traffic": 0.0, 
            "cputime": 0.0, 
            "diskspace": 19285.0, 
            "memory": 0.0
          }, 
          "type": "single", 
          "begin": 1351241166.88561, 
          "measurements": 1, 
          "end": 1351241166.89418
        }, 
        {
          "usage": {
            "traffic": 0.0, 
            "cputime": 0.0, 
            "diskspace": 19285.0, 
            "memory": 0.0
          }, 
          "type": "single", 
          "begin": 1351241106.80326, 
          "measurements": 1, 
          "end": 1351241106.81239
        }, 
        {
          "usage": {
            "traffic": 0.0, 
            "cputime": 0.0, 
            "diskspace": 19285.0, 
            "memory": 0.0
          }, 
          "type": "single", 
          "begin": 1351241226.93197, 
          "measurements": 1, 
          "end": 1351241226.94053
        }, 
        {
          "usage": {
            "traffic": 0.0, 
            "cputime": 0.0, 
            "diskspace": 19285.0, 
            "memory": 0.0
          }, 
          "type": "single", 
          "begin": 1351241286.97878, 
          "measurements": 1, 
          "end": 1351241286.98769
        }
      ], 
      "year": [], 
      "day": []
    }