use std::collections::{VecDeque, HashMap};
use std::hash::BuildHasherDefault;
use std::path::{Path, PathBuf};
use std::fs::{self, File};
use std::io::{self, Write, Read};
use std::sync::{RwLock, Mutex};

use fnv::FnvHasher;

use util::{Time, now, get_duration, now_exact, Binary, last_periods};
use hierarchy::Hierarchy;


static MAGIC: u16 = 28732;
static VERSION: u8 = 1;

#[derive(Clone, Debug, PartialEq)]
pub struct InternalUsage {
    pub memory: f64, // Byte-seconds
    pub disk: f64, // Byte-seconds
    pub traffic: f64, // Bytes
    pub cputime: f64, // Core-Seconds
    pub measurements: u32,
}

const USAGE_SIZE: usize = 36;

impl InternalUsage {
    pub fn new(memory: f64, disk: f64, traffic: f64, cputime: f64, measurements: u32) -> InternalUsage {
        InternalUsage { memory: memory, disk: disk, traffic: traffic, cputime: cputime, measurements: measurements }
    }

    pub fn zero() -> InternalUsage {
        InternalUsage::new(0.0, 0.0, 0.0, 0.0, 0)
    }

    pub fn add(&mut self, other: &InternalUsage) {
        self.memory += other.memory;
        self.disk += other.disk;
        self.measurements += other.measurements;
        self.cputime += other.cputime;
        self.traffic += other.traffic;
    }

    pub fn divide_by(&mut self, f: f64) {
        self.memory /= f;
        self.disk /= f;
        self.cputime /= f;
        self.traffic /= f;
    }

    pub fn encode(&self, buf: &mut [u8]) {
        Binary::write_f64(self.memory, &mut buf[0..]);
        Binary::write_f64(self.disk, &mut buf[8..]);
        Binary::write_f64(self.traffic, &mut buf[16..]);
        Binary::write_f64(self.cputime, &mut buf[24..]);
        Binary::write_u32(self.measurements, &mut buf[32..]);
    }

    pub fn decode(buf: &[u8]) -> InternalUsage {
        let memory = Binary::read_f64(&buf[0..]);
        let disk = Binary::read_f64(&buf[8..]);
        let traffic = Binary::read_f64(&buf[16..]);
        let cputime = Binary::read_f64(&buf[24..]);
        let measurements = Binary::read_u32(&buf[32..]);
        InternalUsage::new(memory, disk, traffic, cputime, measurements)
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct Usage {
    pub memory: f64, // Bytes on average
    pub disk: f64, // Bytes on average
    pub traffic: f64, // Bytes
    pub cputime: f64, // Core-Seconds
    pub measurements: u32,
}

impl Usage {
    pub fn new(memory: f64, disk: f64, traffic: f64, cputime: f64, measurements: u32) -> Usage {
        Usage { memory: memory, disk: disk, traffic: traffic, cputime: cputime, measurements: measurements }
    }

    pub fn zero() -> Usage {
        Usage::new(0.0, 0.0, 0.0, 0.0, 0)
    }

    pub fn divide_by(&mut self, f: f64) {
        self.memory /= f;
        self.disk /= f;
        self.cputime /= f;
        self.traffic /= f;
    }

    pub fn from_internal(usage: &InternalUsage, duration: Time) -> Usage {
        Usage::new(
            usage.memory/duration as f64,
            usage.disk/duration as f64,
            usage.traffic,
            usage.cputime,
            usage.measurements
        )
    }

    pub fn to_internal(&self, duration: Time) -> InternalUsage {
        InternalUsage::new(
            self.memory*duration as f64,
            self.disk*duration as f64,
            self.traffic,
            self.cputime,
            self.measurements
        )
    }
}


#[derive(Clone)]
pub struct Record {
    pub timestamp: Time,
    pub five_min: VecDeque<InternalUsage>,
    pub hour: VecDeque<InternalUsage>,
    pub day: VecDeque<InternalUsage>,
    pub month: VecDeque<InternalUsage>,
    pub year: VecDeque<InternalUsage>
}

impl Record {
    pub fn empty(timestamp: Time, max_five_min: usize, max_hour: usize, max_day: usize, max_month: usize, max_year: usize) -> Record {
        Record {
            timestamp: timestamp,
            five_min: VecDeque::with_capacity(max_five_min),
            hour: VecDeque::with_capacity(max_hour),
            day: VecDeque::with_capacity(max_day),
            month: VecDeque::with_capacity(max_month),
            year: VecDeque::with_capacity(max_year),
        }
    }

    pub fn new(timestamp: Time, max_five_min: usize, max_hour: usize, max_day: usize, max_month: usize, max_year: usize) -> Record {
        let mut rec = Record::empty(timestamp, max_five_min, max_hour, max_day, max_month, max_year);
        for _ in 0..max_five_min {
            rec.five_min.push_back(InternalUsage::zero());
        }
        for _ in 0..max_hour {
            rec.hour.push_back(InternalUsage::zero());
        }
        for _ in 0..max_day {
            rec.day.push_back(InternalUsage::zero());
        }
        for _ in 0..max_month {
            rec.month.push_back(InternalUsage::zero());
        }
        for _ in 0..max_year {
            rec.year.push_back(InternalUsage::zero());
        }
        rec
    }

    pub fn cur(&self) -> &InternalUsage {
        self.five_min.back().expect("No current entry")
    }

    pub fn add(&mut self, usage: &InternalUsage, now: Time) {
        if now / 300 != self.timestamp / 300 {
            let (last_five_min, last_hour, last_day, last_month, last_year) = last_periods(now);
            if self.timestamp < last_five_min {
                debug!("New 5 minute period, shifting usage");
                self.five_min.pop_front();
                self.five_min.push_back(InternalUsage::zero());
            }
            if self.timestamp < last_hour {
                debug!("New hour period, shifting usage");
                self.hour.pop_front();
                self.hour.push_back(InternalUsage::zero());
            }
            if self.timestamp < last_day {
                debug!("New day period, shifting usage");
                self.day.pop_front();
                self.day.push_back(InternalUsage::zero());
            }
            if self.timestamp < last_month {
                debug!("New month period, shifting usage");
                self.month.pop_front();
                self.month.push_back(InternalUsage::zero());
            }
            if self.timestamp < last_year {
                debug!("New year period, shifting usage");
                self.year.pop_front();
                self.year.push_back(InternalUsage::zero());
            }
        }
        if let Some(entr) = self.five_min.back_mut() {
            entr.add(usage)
        }
        if let Some(entr) = self.hour.back_mut() {
            entr.add(usage)
        }
        if let Some(entr) = self.day.back_mut() {
            entr.add(usage)
        }
        if let Some(entr) = self.month.back_mut() {
            entr.add(usage)
        }
        if let Some(entr) = self.year.back_mut() {
            entr.add(usage)
        }
        self.timestamp = now;
    }

    pub fn encode(&self, buf: &mut [u8]) -> usize {
        let mut pos = 0;
        Binary::write_u16(MAGIC, &mut buf[pos..]); pos += 2;
        buf[pos] = VERSION; pos += 1;
        buf[pos] = self.five_min.len() as u8; pos += 1;
        buf[pos] = self.hour.len() as u8; pos += 1;
        buf[pos] = self.day.len() as u8; pos += 1;
        buf[pos] = self.month.len() as u8; pos += 1;
        buf[pos] = self.year.len() as u8; pos += 1;
        Binary::write_i64(self.timestamp, &mut buf[pos..]); pos += 8;
        for usage in &self.five_min {
            usage.encode(&mut buf[pos..]); pos += USAGE_SIZE;
        }
        for usage in &self.hour {
            usage.encode(&mut buf[pos..]); pos += USAGE_SIZE;
        }
        for usage in &self.day {
            usage.encode(&mut buf[pos..]); pos += USAGE_SIZE;
        }
        for usage in &self.month {
            usage.encode(&mut buf[pos..]); pos += USAGE_SIZE;
        }
        for usage in &self.year {
            usage.encode(&mut buf[pos..]); pos += USAGE_SIZE;
        }
        pos
    }

    pub fn decode(buf: &[u8]) -> Result<Record, DecodeError> {
        if buf.len() < 16 {
            return Err(DecodeError::Truncated);
        }
        let mut pos = 0;
        let magic = Binary::read_u16(&buf[pos..]); pos += 2;
        if magic != MAGIC {
            return Err(DecodeError::InvalidMagic);
        }
        let version = buf[pos]; pos += 1;
        if version != VERSION {
            return Err(DecodeError::InvalidVersion);
        }
        let max_five_min = buf[pos] as usize; pos += 1;
        let max_hour = buf[pos] as usize; pos += 1;
        let max_day = buf[pos] as usize; pos += 1;
        let max_month = buf[pos] as usize; pos += 1;
        let max_year = buf[pos] as usize; pos += 1;
        let timestamp = Binary::read_i64(&buf[pos..]); pos += 8;
        if buf.len() < pos + (max_five_min + max_hour + max_day + max_month + max_year) * USAGE_SIZE {
            return Err(DecodeError::Truncated);
        }
        let mut rec = Record::empty(timestamp, max_five_min, max_hour, max_day, max_month, max_year);
        for _ in 0..max_five_min {
            rec.five_min.push_back(InternalUsage::decode(&buf[pos..])); pos += USAGE_SIZE;
        }
        for _ in 0..max_hour {
            rec.hour.push_back(InternalUsage::decode(&buf[pos..])); pos += USAGE_SIZE;
        }
        for _ in 0..max_day {
            rec.day.push_back(InternalUsage::decode(&buf[pos..])); pos += USAGE_SIZE;
        }
        for _ in 0..max_month {
            rec.month.push_back(InternalUsage::decode(&buf[pos..])); pos += USAGE_SIZE;
        }
        for _ in 0..max_year {
            rec.year.push_back(InternalUsage::decode(&buf[pos..])); pos += USAGE_SIZE;
        }
        Ok(rec)
    }
}

#[derive(Debug)]
pub enum DecodeError {
    Truncated,
    InvalidMagic,
    InvalidVersion
}


#[derive(Debug, Ord, Eq, PartialEq, PartialOrd, Hash, Clone, Copy)]
pub enum RecordType {
    HostElement,
    HostConnection,
    Element,
    Connection,
    Topology,
    User,
    Organization
}

impl RecordType {
    pub fn name(&self) -> &'static str {
        match *self {
            RecordType::HostElement => "host_element",
            RecordType::HostConnection => "host_connection",
            RecordType::Element => "element",
            RecordType::Connection => "connection",
            RecordType::Topology => "topology",
            RecordType::User => "user",
            RecordType::Organization => "organization"
        }
    }
}

pub type Hash = BuildHasherDefault<FnvHasher>;

pub type StoreError = io::Error;

#[derive(Debug)]
pub enum LoadError {
    IO(io::Error),
    Decode(DecodeError)
}

impl From<io::Error> for LoadError {
    fn from(err: io::Error) -> Self {
        LoadError::IO(err)
    }
}

impl From<DecodeError> for LoadError {
    fn from(err: DecodeError) -> Self {
        LoadError::Decode(err)
    }
}


pub struct Data {
    path: PathBuf,
    hierarchy: Box<Hierarchy>,
    last_store: Mutex<Time>,
    last_cleanup: Mutex<Time>,
    max_entries: HashMap<RecordType, (usize, usize, usize, usize, usize), Hash>,
    pub records: RwLock<HashMap<(RecordType, String), Mutex<Record>, Hash>>
}

macro_rules! hierarchy {
    ($hierarchy:expr, $ctype:expr, $ptype:expr, $cid:expr) => {
        match $hierarchy.get($ctype, $ptype, $cid) {
            Ok(data) => data,
            Err(_) => {
                error!("Failed to obtain {} of {}/{}", $ptype.name(), $ctype.name(), $cid);
                return
            }
        };
    }
}

impl Data {
    pub fn new<P: AsRef<Path>>(path: P, hierarchy: Box<Hierarchy>) -> Data {
        for type_ in &[RecordType::Connection, RecordType::Element, RecordType::HostConnection,
            RecordType::HostElement, RecordType::Topology, RecordType::User, RecordType::Organization] {
            let path = path.as_ref().to_owned().join(type_.name());
            fs::create_dir_all(&path).expect("Failed to create directories");
        }
        let mut data = Data {
            path: path.as_ref().to_owned(),
            hierarchy: hierarchy,
            max_entries: HashMap::default(),
            records: RwLock::new(HashMap::default()),
            last_store: Mutex::new(now()),
            last_cleanup: Mutex::new(now())
        };
        data.max_entries.insert(RecordType::HostElement, (2, 0, 0, 0, 0));
        data.max_entries.insert(RecordType::HostConnection, (2, 0, 0, 0, 0));
        data.max_entries.insert(RecordType::Element, (25, 75, 50, 15, 0));
        data.max_entries.insert(RecordType::Connection, (25, 75, 50, 15, 0));
        data.max_entries.insert(RecordType::Topology, (25, 75, 50, 15, 5));
        data.max_entries.insert(RecordType::User, (25, 75, 50, 15, 5));
        data.max_entries.insert(RecordType::Organization, (25, 75, 50, 15, 5));
        data
    }

    pub fn record_path(&self, type_: RecordType, id: &str) -> PathBuf {
        self.path.clone().join(type_.name()).join(id)
    }

    pub fn store_record(&self, type_: RecordType, id: &str, record: &Record) -> Result<(), StoreError> {
        debug!("Storing {}/{}", type_.name(), id);
        let mut f = try!(File::create(self.record_path(type_, id)));
        let mut buf = [0u8; 32768];
        let len = record.encode(&mut buf);
        try!(f.write(&buf[0..len]));
        Ok(())
    }

    pub fn get_record(&self, type_: RecordType, id: String) -> Option<Record> {
        self.records.read().expect("Lock poisoned").get(&(type_, id)).map(|v| v.lock().expect("Lock poisoned").clone())
    }

    pub fn store_all(&self) -> Result<usize, StoreError> {
        let mut stored = 0;
        let start = now_exact();
        let last_store = *self.last_store.lock().expect("Lock poisoned");
        for (&(type_, ref id), record) in self.records.read().expect("Lock poisoned").iter() {
            let record = record.lock().expect("Lock poisoned");
            if record.timestamp >= last_store {
                try!(self.store_record(type_, id, &record));
                stored += 1;
            }
        }
        let end = now_exact();
        if stored > 0 {
            info!("Storing {} entries took {} seconds", stored, get_duration(end-start));
        }
        *self.last_store.lock().expect("Lock poisoned") = end.sec;
        Ok(stored)
    }

    pub fn cleanup_all(&self, max_age: Time) -> Result<usize, StoreError> {
        info!("Cleanup begin");
        // Phase 1: determine which records are pretty old
        let mut to_check = Vec::new();
        let limit = now() - max_age;
        for (&(type_, ref id), record) in self.records.read().expect("Lock poisoned").iter() {
            let record = record.lock().expect("Lock poisoned");
            if record.timestamp < limit {
                to_check.push((type_, id.clone()));
            }
        }
        // Phase 2: query hierarchy for existence (important: hold no locks)
        let mut to_remove = Vec::with_capacity(to_check.len());
        for (type_, id) in to_check {
            match self.hierarchy.exists(type_, &id) {
                Err(err) => {
                    error!("Unable to check for existence of {}/{}: {:?}", type_.name(), id, err);
                    break
                },
                Ok(true) => continue,
                Ok(false) => to_remove.push((type_, id))
            }
        }
        // Phase 3: actually delete entries that don't exist
        let removed = to_remove.len();
        let mut records = self.records.write().expect("Lock poisoned");
        for key in to_remove {
            debug!("Removing record {}/{}", key.0.name(), key.1);
            records.remove(&key);
            try!(fs::remove_file(self.record_path(key.0, &key.1)));
        }
        *self.last_cleanup.lock().expect("Lock poisoned") = now();
        info!("Cleanup removed {} records", removed);
        Ok(removed)
    }

    pub fn load_record(&self, type_: RecordType, id: &str) -> Result<Record, LoadError> {
        debug!("Loading {}/{}", type_.name(), id);
        let mut f = try!(File::open(self.record_path(type_, id)));
        let mut buf = Vec::new();
        try!(f.read_to_end(&mut buf));
        Record::decode(&buf).map_err(LoadError::from)
    }

    pub fn load_all(&self) -> Result<(), LoadError> {
        for type_ in &[RecordType::Connection, RecordType::Element, RecordType::HostConnection,
            RecordType::HostElement, RecordType::Topology, RecordType::User, RecordType::Organization] {
            let path = self.path.clone().join(type_.name());
            let files = try!(fs::read_dir(&path));
            let mut records = self.records.write().expect("Lock poisoned");
            for file in files {
                let id = try!(file).file_name().to_string_lossy().into_owned();
                let record = try!(self.load_record(*type_, &id));
                records.insert((*type_, id), Mutex::new(record));
            }
        }
        Ok(())
    }

    pub fn add_usage(&self, type_: RecordType, id: String, usage: &InternalUsage, timestamp: Time) {
        debug!("Adding usage to {}/{}: {:?}@{}", type_.name(), id, usage, timestamp);
        let key = (type_, id);
        {
            let records = self.records.read().expect("Lock poisoned");
            if let Some(record) = records.get(&key) {
                record.lock().expect("Lock poisoned").add(usage, timestamp);
                return
            }
        }
        debug!("Creating new record for {}/{}", type_.name(), key.1);
        let &(max_five_min, max_hour, max_day, max_month, max_year) = self.max_entries.get(&type_).expect(&format!("No limits set for record type {:?}", type_));
        let mut records = self.records.write().expect("Lock poisoned");
        let mut record = Record::new(timestamp, max_five_min, max_hour, max_day, max_month, max_year);
        record.add(usage, timestamp);
        records.insert(key, Mutex::new(record));
    }

    pub fn get_time_diff(&self, type_: RecordType, id: String, timestamp: Time) -> Time {
        let key = (type_, id);
        let records = self.records.read().expect("Lock poisoned");
        if let Some(record) = records.get(&key) {
            timestamp - record.lock().expect("Lock poisoned").timestamp
        } else {
            0
        }
    }

    pub fn add_organization_usage(&self, id: &str, usage: &mut InternalUsage, timestamp: Time) {
        self.add_usage(RecordType::Organization, id.to_owned(), usage, timestamp);
    }

    pub fn add_user_usage(&self, id: &str, usage: &mut InternalUsage, timestamp: Time) {
        let mut organizations = hierarchy!(self.hierarchy, RecordType::User, RecordType::Organization, &id);
        self.add_usage(RecordType::User, id.to_owned(), usage, timestamp);
        if organizations.is_empty() {
            warn!("No organization for user/{}", id);
            return;
        }
        self.add_organization_usage(&organizations.pop().unwrap(), usage, timestamp);
    }

    pub fn add_topology_usage(&self, id: &str, usage: &mut InternalUsage, timestamp: Time) {
        let users = hierarchy!(self.hierarchy, RecordType::Topology, RecordType::User, &id);
        self.add_usage(RecordType::Topology, id.to_owned(), usage, timestamp);
        if users.len() > 1 {
            debug!("Topology {} has multiple owners, dividing usage by {}", id, users.len());
            usage.divide_by(users.len() as f64);
        }
        if users.is_empty() {
            warn!("No user for topology/{}", id);
        }
        for user in users {
            self.add_user_usage(&user, usage, timestamp);
        }
    }

    pub fn add_element_usage(&self, id: &str, usage: &mut InternalUsage, timestamp: Time) {
        let mut topologies = hierarchy!(self.hierarchy, RecordType::Element, RecordType::Topology, &id);
        self.add_usage(RecordType::Element, id.to_owned(), usage, timestamp);
        if topologies.is_empty() {
            warn!("No topology for element/{}", id);
            return;
        }
        self.add_topology_usage(&topologies.pop().unwrap(), usage, timestamp);
    }

    pub fn add_connection_usage(&self, id: &str, usage: &mut InternalUsage, timestamp: Time) {
        let mut topologies = hierarchy!(self.hierarchy, RecordType::Connection, RecordType::Topology, &id);
        self.add_usage(RecordType::Connection, id.to_owned(), usage, timestamp);
        if topologies.is_empty() {
            warn!("No topology for connection/{}", id);
            return;
        }
        self.add_topology_usage(&topologies.pop().unwrap(), usage, timestamp);
    }

    pub fn add_host_element_usage(&self, id: &str, usage: &mut InternalUsage, timestamp: Time) {
        let elements = hierarchy!(self.hierarchy, RecordType::HostElement, RecordType::Element, &id);
        let connections = hierarchy!(self.hierarchy, RecordType::HostElement, RecordType::Connection, &id);
        self.add_usage(RecordType::HostElement, id.to_owned(), usage, timestamp);
        if elements.is_empty() && connections.is_empty() {
            warn!("No element/connection for host_element/{}", id);
            return;
        }
        if elements.len() + connections.len() > 1 {
            warn!("Multiple elements/connections for host_element/{}", id);
            return;
        }
        for el in elements {
            self.add_element_usage(&el, usage, timestamp);
        }
        for con in connections {
            self.add_connection_usage(&con, usage, timestamp);
        }
    }

    pub fn add_host_connection_usage(&self, id: &str, usage: &mut InternalUsage, timestamp: Time) {
        let mut connections = hierarchy!(self.hierarchy, RecordType::HostConnection, RecordType::Connection, &id);
        self.add_usage(RecordType::HostConnection, id.to_owned(), usage, timestamp);
        if connections.is_empty() {
            warn!("No connection for host_connection/{}", id);
            return;
        }
        self.add_connection_usage(&connections.pop().unwrap(), usage, timestamp);
    }

    pub fn housekeep(&self, store_interval: Time, cleanup_interval: Time, max_record_age: Time) {
        if *self.last_store.lock().expect("Lock poisoned") + store_interval <= now() {
            self.store_all().expect("Store failed");
        }
        if *self.last_cleanup.lock().expect("Lock poisoned") + cleanup_interval <= now() {
            self.cleanup_all(max_record_age).expect("Store failed");
        }
    }

    pub fn api_add_host_element_usage(&self, id: &str, usage: &mut Usage, timestamp: Time) {
        let mut usage = usage.to_internal(self.get_time_diff(RecordType::HostElement, id.to_owned(), timestamp));
        self.add_host_element_usage(id, &mut usage, timestamp)
    }

    pub fn api_add_host_connection_usage(&self, id: &str, usage: &mut Usage, timestamp: Time) {
        let mut usage = usage.to_internal(self.get_time_diff(RecordType::HostConnection, id.to_owned(), timestamp));
        self.add_host_connection_usage(id, &mut usage, timestamp)
    }
}
