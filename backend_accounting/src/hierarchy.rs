use std::collections::HashMap;
use std::hash::BuildHasherDefault;
use std::sync::RwLock;

use fnv::FnvHasher;

use data::RecordType;
use util::{Time, now};

pub type Hash = BuildHasherDefault<FnvHasher>;

pub enum HierarchyError {
    NoSuchEntity,
    NoSuchRelation
}

pub trait Hierarchy: Send + Sync {
    fn get(&self, child_type: RecordType, parent_type: RecordType, child_id: &str) -> Result<Vec<String>, HierarchyError>;
}

pub struct HierarchyCache {
    timeout: Time,
    inner: Box<Hierarchy>,
    cache: HashMap<(RecordType, RecordType), RwLock<HashMap<String, (Vec<String>, Time), Hash>>, Hash>
}

impl HierarchyCache {
    pub fn new(inner: Box<Hierarchy>, timeout: Time) -> Self {
        let mut obj = HierarchyCache {
            timeout: timeout,
            inner: inner,
            cache: HashMap::default()
        };
        for &(child, parent) in &[
            (RecordType::HostElement, RecordType::Element), (RecordType::HostElement, RecordType::Connection),
            (RecordType::HostConnection, RecordType::Connection),
            (RecordType::Element, RecordType::Topology), (RecordType::Connection, RecordType::Topology),
            (RecordType::Topology, RecordType::User), (RecordType::User, RecordType::Organization)
        ] {
            obj.cache.insert((child, parent), RwLock::new(HashMap::default()));
        }
        obj
    }

    pub fn put(&self, child_type: RecordType, child_id: String, parent_type: RecordType, parent_ids: Vec<String>) {
        let group = self.cache.get(&(child_type, parent_type)).expect("No such relation");
        group.write().expect("Lock poisoned").insert(child_id, (parent_ids, now()));
    }
}

impl Hierarchy for HierarchyCache {
    fn get(&self, child_type: RecordType, parent_type: RecordType, child_id: &str) -> Result<Vec<String>, HierarchyError> {
        let now = now();
        let group = match self.cache.get(&(child_type, parent_type)) {
            Some(group) => group,
            None => return Err(HierarchyError::NoSuchRelation)
        };
        {
            let group = group.read().expect("Lock poisoned");
            if let Some(&(ref data, time)) = group.get(child_id) {
                if time + self.timeout > now {
                    return Ok(data.clone());
                }
            }
        }
        let fresh = try!(self.inner.get(child_type, parent_type, child_id));
        let mut group = group.write().expect("Lock poisoned");
        group.insert(child_id.to_owned(), (fresh.clone(), now));
        Ok(fresh)
    }
}

pub struct DummyHierarchy;

impl Hierarchy for DummyHierarchy {
    fn get(&self, _: RecordType, _: RecordType, _: &str) -> Result<Vec<String>, HierarchyError> {
        Ok(Vec::new())
    }
}
