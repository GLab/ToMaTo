use std::collections::{VecDeque, HashMap};
use std::hash::BuildHasherDefault;
use std::path::{Path, PathBuf};
use std::fs::{self, File};
use std::io::{self, Write, Read};
use std::sync::{RwLock, Mutex};

use fnv::FnvHasher;
use time;

use util::{Time, now, Binary};
use hierarchy::Hierarchy;


static MAGIC: u16 = 28732;
static VERSION: u8 = 0;


pub fn last_periods(now: Time) -> (Time, Time, Time, Time, Time) {
    let mut tm = time::at_utc(time::Timespec::new(now, 0));
    tm.tm_nsec = 0;
    tm.tm_sec = 0;
    tm.tm_min = (tm.tm_min / 5) * 5;
    let five_min = tm.to_timespec().sec;
    tm.tm_min = 0;
    let hour = tm.to_timespec().sec;
    tm.tm_hour = 0;
    let day = tm.to_timespec().sec;
    tm.tm_mday = 1; // 1st of month
    let month = tm.to_timespec().sec;
    tm.tm_mon = 0; // Jan is 0
    let year = tm.to_timespec().sec;
    (five_min, hour, day, month, year)
}

pub fn last_five_min(now: Time) -> Time {
    let mut tm = time::at_utc(time::Timespec::new(now, 0));
    tm.tm_nsec = 0;
    tm.tm_sec = 0;
    tm.tm_min = (tm.tm_min / 5) * 5;
    tm.to_timespec().sec
}

pub fn last_hour(now: Time) -> Time {
    let mut tm = time::at_utc(time::Timespec::new(now, 0));
    tm.tm_nsec = 0;
    tm.tm_sec = 0;
    tm.tm_min = 0;
    tm.to_timespec().sec
}

pub fn last_day(now: Time) -> Time {
    let mut tm = time::at_utc(time::Timespec::new(now, 0));
    tm.tm_nsec = 0;
    tm.tm_sec = 0;
    tm.tm_min = 0;
    tm.tm_hour = 0;
    tm.to_timespec().sec
}

pub fn last_month(now: Time) -> Time {
    let mut tm = time::at_utc(time::Timespec::new(now, 0));
    tm.tm_nsec = 0;
    tm.tm_sec = 0;
    tm.tm_min = 0;
    tm.tm_hour = 0;
    tm.tm_mday = 1; // 1st of month
    tm.to_timespec().sec
}

pub fn last_year(now: Time) -> Time {
    let mut tm = time::at_utc(time::Timespec::new(now, 0));
    tm.tm_nsec = 0;
    tm.tm_sec = 0;
    tm.tm_min = 0;
    tm.tm_hour = 0;
    tm.tm_mday = 1; // 1st of month
    tm.tm_mon = 0; // Jan is 0
    tm.to_timespec().sec
}


#[derive(Clone, Debug, PartialEq)]
pub struct Usage {
    pub memory: f32, // Bytes on average
    pub disk: f32, // Bytes on average
    pub traffic: f32, // Bytes
    pub cputime: f32, // Core-Seconds
    pub measurements: u32
}

const USAGE_SIZE: usize = 20;

impl Usage {
    pub fn new(memory: f32, disk: f32, traffic: f32, cputime: f32, measurements: u32) -> Usage {
        Usage { memory: memory, disk: disk, traffic: traffic, cputime: cputime, measurements: measurements }
    }

    pub fn zero() -> Usage {
        Usage::new(0.0, 0.0, 0.0, 0.0, 0)
    }

    pub fn add(&mut self, other: &Usage) {
        self.memory = self.memory * self.measurements as f32 + other.memory * other.measurements as f32;
        self.disk = self.disk * self.measurements as f32 + other.disk * other.measurements as f32;
        self.measurements += other.measurements;
        self.memory /= self.measurements as f32;
        self.disk /= self.measurements as f32;
        self.cputime += other.cputime;
        self.traffic += other.traffic;
    }

    pub fn divide_by(&mut self, f: f32) {
        self.memory /= f;
        self.disk /= f;
        self.cputime /= f;
        self.traffic /= f;
    }

    pub fn encode(&self, buf: &mut [u8]) {
        Binary::write_f32(self.memory, &mut buf[0..]);
        Binary::write_f32(self.disk, &mut buf[4..]);
        Binary::write_f32(self.traffic, &mut buf[8..]);
        Binary::write_f32(self.cputime, &mut buf[12..]);
        Binary::write_u32(self.measurements, &mut buf[16..]);
    }

    pub fn decode(buf: &[u8]) -> Usage {
        let memory = Binary::read_f32(&buf[0..]);
        let disk = Binary::read_f32(&buf[4..]);
        let traffic = Binary::read_f32(&buf[8..]);
        let cputime = Binary::read_f32(&buf[12..]);
        let measurements = Binary::read_u32(&buf[16..]);
        Usage::new(memory, disk, traffic, cputime, measurements)
    }
}

#[derive(Clone)]
pub struct Record {
    pub timestamp: Time,
    pub five_min: VecDeque<Usage>,
    pub hour: VecDeque<Usage>,
    pub day: VecDeque<Usage>,
    pub month: VecDeque<Usage>,
    pub year: VecDeque<Usage>
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
            rec.five_min.push_back(Usage::zero());
        }
        for _ in 0..max_hour {
            rec.hour.push_back(Usage::zero());
        }
        for _ in 0..max_day {
            rec.day.push_back(Usage::zero());
        }
        for _ in 0..max_month {
            rec.month.push_back(Usage::zero());
        }
        for _ in 0..max_year {
            rec.year.push_back(Usage::zero());
        }
        rec
    }

    pub fn cur(&self) -> &Usage {
        self.five_min.back().expect("No current entry")
    }

    pub fn add(&mut self, usage: &Usage, now: Time) {
        if now / 300 != self.timestamp / 300 {
            let (last_five_min, last_hour, last_day, last_month, last_year) = last_periods(now);
            if self.timestamp < last_five_min {
                self.five_min.pop_front();
                self.five_min.push_back(Usage::zero());
            }
            if self.timestamp < last_hour {
                self.hour.pop_front();
                self.hour.push_back(Usage::zero());
            }
            if self.timestamp < last_day {
                self.day.pop_front();
                self.day.push_back(Usage::zero());
            }
            if self.timestamp < last_month {
                self.month.pop_front();
                self.month.push_back(Usage::zero());
            }
            if self.timestamp < last_year {
                self.year.pop_front();
                self.year.push_back(Usage::zero());
            }
        }
        match self.five_min.back_mut() {
            Some(entr) => entr.add(usage),
            None => ()
        }
        match self.hour.back_mut() {
            Some(entr) => entr.add(usage),
            None => ()
        }
        match self.day.back_mut() {
            Some(entr) => entr.add(usage),
            None => ()
        }
        match self.month.back_mut() {
            Some(entr) => entr.add(usage),
            None => ()
        }
        match self.year.back_mut() {
            Some(entr) => entr.add(usage),
            None => ()
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
            rec.five_min.push_back(Usage::decode(&buf[pos..])); pos += USAGE_SIZE;
        }
        for _ in 0..max_hour {
            rec.hour.push_back(Usage::decode(&buf[pos..])); pos += USAGE_SIZE;
        }
        for _ in 0..max_day {
            rec.day.push_back(Usage::decode(&buf[pos..])); pos += USAGE_SIZE;
        }
        for _ in 0..max_month {
            rec.month.push_back(Usage::decode(&buf[pos..])); pos += USAGE_SIZE;
        }
        for _ in 0..max_year {
            rec.year.push_back(Usage::decode(&buf[pos..])); pos += USAGE_SIZE;
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
        match self {
            &RecordType::HostElement => "host_element",
            &RecordType::HostConnection => "host_connection",
            &RecordType::Element => "element",
            &RecordType::Connection => "connection",
            &RecordType::Topology => "topology",
            &RecordType::User => "user",
            &RecordType::Organization => "organization"
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
    max_entries: HashMap<RecordType, (usize, usize, usize, usize, usize), Hash>,
    pub records: RwLock<HashMap<(RecordType, String), Mutex<Record>, Hash>>
}

macro_rules! hierarchy {
    ($hierarchy:expr, $ctype:expr, $ptype:expr, $cid:expr) => {
        match $hierarchy.get($ctype, $ptype, $cid) {
            Ok(data) => data,
            Err(_) => return
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
            last_store: Mutex::new(now())
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
        let last_store = self.last_store.lock().expect("Lock poisoned").clone();
        for (&(type_, ref id), record) in self.records.read().expect("Lock poisoned").iter() {
            let record = record.lock().expect("Lock poisoned");
            if record.timestamp >= last_store {
                try!(self.store_record(type_, id, &record));
                stored += 1;
            }
        }
        *self.last_store.lock().expect("Lock poisoned") = now();
        Ok(stored)
    }

    pub fn load_record(&self, type_: RecordType, id: &str) -> Result<Record, LoadError> {
        let mut f = try!(File::open(self.record_path(type_, id)));
        let mut buf = Vec::new();
        try!(f.read_to_end(&mut buf));
        Record::decode(&buf).map_err(|err| LoadError::from(err))
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
                records.insert((type_.clone(), id), Mutex::new(record));
            }
        }
        Ok(())
    }

    pub fn add_usage(&self, type_: RecordType, id: String, usage: &Usage, timestamp: Time) {
        let key = (type_, id);
        {
            let records = self.records.read().expect("Lock poisoned");
            if let Some(record) = records.get(&key) {
                record.lock().expect("Lock poisoned").add(usage, timestamp);
                return
            }
        }
        let &(max_five_min, max_hour, max_day, max_month, max_year) = self.max_entries.get(&type_).expect(&format!("No limits set for record type {:?}", type_));
        let mut records = self.records.write().expect("Lock poisoned");
        let mut record = Record::new(timestamp, max_five_min, max_hour, max_day, max_month, max_year);
        record.add(&usage, timestamp);
        records.insert(key, Mutex::new(record));
    }

    pub fn add_organization_usage(&self, id: &str, usage: &mut Usage, timestamp: Time) {
        self.add_usage(RecordType::Organization, id.to_owned(), usage, timestamp);
    }

    pub fn add_user_usage(&self, id: &str, usage: &mut Usage, timestamp: Time) {
        let mut organizations = hierarchy!(self.hierarchy, RecordType::User, RecordType::Organization, &id);
        self.add_usage(RecordType::User, id.to_owned(), usage, timestamp);
        if organizations.len() == 0 {
            return;
        }
        self.add_organization_usage(&organizations.pop().unwrap(), usage, timestamp);
    }

    pub fn add_topology_usage(&self, id: &str, usage: &mut Usage, timestamp: Time) {
        let users = hierarchy!(self.hierarchy, RecordType::Topology, RecordType::User, &id);
        self.add_usage(RecordType::Topology, id.to_owned(), usage, timestamp);
        if users.len() > 1 {
            usage.divide_by(users.len() as f32);
        }
        for user in users {
            self.add_user_usage(&user, usage, timestamp);
        }
    }

    pub fn add_element_usage(&self, id: &str, usage: &mut Usage, timestamp: Time) {
        let mut topologies = hierarchy!(self.hierarchy, RecordType::Element, RecordType::Topology, &id);
        self.add_usage(RecordType::Element, id.to_owned(), usage, timestamp);
        if topologies.len() == 0 {
            return;
        }
        self.add_topology_usage(&topologies.pop().unwrap(), usage, timestamp);
    }

    pub fn add_connection_usage(&self, id: &str, usage: &mut Usage, timestamp: Time) {
        let mut topologies = hierarchy!(self.hierarchy, RecordType::Connection, RecordType::Topology, &id);
        self.add_usage(RecordType::Connection, id.to_owned(), usage, timestamp);
        if topologies.len() == 0 {
            return;
        }
        self.add_topology_usage(&topologies.pop().unwrap(), usage, timestamp);
    }

    pub fn add_host_element_usage(&self, id: &str, usage: &mut Usage, timestamp: Time) {
        let elements = hierarchy!(self.hierarchy, RecordType::HostElement, RecordType::Element, &id);
        let connections = hierarchy!(self.hierarchy, RecordType::HostElement, RecordType::Connection, &id);
        self.add_usage(RecordType::HostElement, id.to_owned(), usage, timestamp);
        if elements.len() + connections.len() == 0 {
            return;
        }
        for el in elements {
            self.add_element_usage(&el, usage, timestamp);
        }
        for con in connections {
            self.add_connection_usage(&con, usage, timestamp);
        }
    }

    pub fn add_host_connection_usage(&self, id: &str, usage: &mut Usage, timestamp: Time) {
        let mut connections = hierarchy!(self.hierarchy, RecordType::HostConnection, RecordType::Connection, &id);
        self.add_usage(RecordType::HostConnection, id.to_owned(), usage, timestamp);
        if connections.len() == 0 {
            return;
        }
        self.add_connection_usage(&connections.pop().unwrap(), usage, timestamp);
    }
}
