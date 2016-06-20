use tempdir::TempDir;
use log;

use std::str::FromStr;

use super::*;

fn set_logger() {
    log::set_logger(|max_log_level| {
        max_log_level.set(log::LogLevelFilter::from_str("debug").unwrap());
        Box::new(SimpleLogger)
    }).unwrap();
}

#[test]
fn last_periods() {
    assert_eq!(util::last_periods(0), (0, 0, 0, 0, 0));
    assert_eq!(util::last_periods(1459410971), (1459410900, 1459407600, 1459382400, 1456790400, 1451606400));
}

#[test]
fn internal_usage_new() {
    let usage = data::InternalUsage::new(1.0, 2.0, 3.0, 4.0, 1);
    assert_eq!(usage.memory, 1.0);
    assert_eq!(usage.disk, 2.0);
    assert_eq!(usage.traffic, 3.0);
    assert_eq!(usage.cputime, 4.0);
    assert_eq!(usage.measurements, 1);
}

#[test]
fn usage_new() {
    let usage = data::Usage::new(1.0, 2.0, 3.0, 4.0, 1);
    assert_eq!(usage.memory, 1.0);
    assert_eq!(usage.disk, 2.0);
    assert_eq!(usage.traffic, 3.0);
    assert_eq!(usage.cputime, 4.0);
    assert_eq!(usage.measurements, 1);
}

#[test]
fn usage_zero() {
    assert_eq!(data::Usage::zero(), data::Usage::new(0.0, 0.0, 0.0, 0.0, 0));
}

#[test]
fn internal_usage_zero() {
    assert_eq!(data::InternalUsage::zero(), data::InternalUsage::new(0.0, 0.0, 0.0, 0.0, 0));
}

#[test]
fn internal_usage_add() {
    let mut d = data::InternalUsage::new(1.0, 2.0, 3.0, 4.0, 1);
    d.add(&data::InternalUsage::new(10.0, 20.0, 30.0, 40.0, 2));
    assert_eq!(d, data::InternalUsage::new(11.0, 22.0, 33.0, 44.0, 3));
}

#[test]
fn internal_usage_encode() {
    let mut buf = [0; 36];
    let d = data::InternalUsage::new(1.1, 2.0, 3.0, 0.34, 1);
    d.encode(&mut buf);
    let expected = [63, 241, 153, 153, 153, 153, 153, 154, 64, 0, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0,
        0, 0, 0, 63, 213, 194, 143, 92, 40, 245, 195, 0, 0, 0, 1];
    println!("output was: {:?}", &buf as &[u8]);
    for i in 0..expected.len() {
        assert_eq!(expected[i], buf[i]);
    }
}

#[test]
fn internal_usage_decode() {
    let buf = [63, 241, 153, 153, 153, 153, 153, 154, 64, 0, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0,
        0, 0, 63, 213, 194, 143, 92, 40, 245, 195, 0, 0, 0, 1];
    assert_eq!(data::InternalUsage::decode(&buf), data::InternalUsage::new(1.1, 2.0, 3.0, 0.34, 1));
}

#[test]
fn record_empty() {
    let rec = data::Record::empty(15, 1, 2, 3, 4, 5);
    assert_eq!(rec.timestamp, 15);
    assert_eq!(rec.five_min.len(), 0);
    assert_eq!(rec.hour.len(), 0);
    assert_eq!(rec.day.len(), 0);
    assert_eq!(rec.month.len(), 0);
    assert_eq!(rec.year.len(), 0);
}

#[test]
fn record_new() {
    let rec = data::Record::new(15, 1, 2, 3, 4, 5);
    assert_eq!(rec.timestamp, 15);
    assert_eq!(rec.five_min.len(), 1);
    assert_eq!(rec.hour.len(), 2);
    assert_eq!(rec.day.len(), 3);
    assert_eq!(rec.month.len(), 4);
    assert_eq!(rec.year.len(), 5);
    assert_eq!(rec.month[3], data::InternalUsage::zero());
    assert_eq!(rec.hour[0], data::InternalUsage::zero());
}

#[test]
fn record_add() {
    let mut rec = data::Record::new(0, 3, 3, 3, 3, 3);
    rec.add(&data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 1);
    assert_eq!(rec.five_min[2], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
    assert_eq!(rec.five_min[1], data::InternalUsage::zero());
    assert_eq!(rec.hour[2], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
    rec.add(&data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 2);
    assert_eq!(rec.five_min[2], data::InternalUsage::new(2.0, 2.0, 2.0, 2.0, 2));
    assert_eq!(rec.five_min[1], data::InternalUsage::zero());
    assert_eq!(rec.hour[2], data::InternalUsage::new(2.0, 2.0, 2.0, 2.0, 2));
    rec.add(&data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 302);
    assert_eq!(rec.five_min[2], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
    assert_eq!(rec.five_min[1], data::InternalUsage::new(2.0, 2.0, 2.0, 2.0, 2));
    assert_eq!(rec.hour[2], data::InternalUsage::new(3.0, 3.0, 3.0, 3.0, 3));
}

#[test]
fn record_encode() {
    let mut rec = data::Record::new(0, 3, 3, 3, 3, 3);
    rec.add(&data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 0);
    rec.add(&data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 300);
    rec.add(&data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 3900);
    assert_eq!(rec.five_min[0], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
    assert_eq!(rec.five_min[1], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
    assert_eq!(rec.five_min[2], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
    assert_eq!(rec.hour[1], data::InternalUsage::new(2.0, 2.0, 2.0, 2.0, 2));
    assert_eq!(rec.hour[2], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
    let mut buf = [0; 32768];
    let expected = [112, 60, 1, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 15, 60, 63, 240, 0, 0, 0, 0, 0, 0,
        63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 63,
        240, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0,
        63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 0,
        0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 2, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0,
        0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 8, 0,
        0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0,
        0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0,
        0, 64, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3];
    assert_eq!(expected.len(), 16+36*3*5);
    assert_eq!(rec.encode(&mut buf), expected.len());
    println!("output was: {:?}", &buf[0..expected.len()]);
    for i in 0..expected.len() {
        assert_eq!(expected[i], buf[i]);
    }
}

#[test]
fn record_decode() {
    let encoded = [112, 60, 1, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 15, 60, 63, 240, 0, 0, 0, 0, 0, 0,
        63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 63,
        240, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0,
        63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 0,
        0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 2, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 63, 240, 0, 0, 0, 0,
        0, 0, 63, 240, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 8, 0,
        0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0,
        0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0, 0, 64, 8, 0, 0, 0, 0, 0,
        0, 64, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3];
    let rec = data::Record::decode(&encoded).unwrap();
    assert_eq!(rec.five_min[0], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
    assert_eq!(rec.five_min[1], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
    assert_eq!(rec.five_min[2], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
    assert_eq!(rec.hour[1], data::InternalUsage::new(2.0, 2.0, 2.0, 2.0, 2));
    assert_eq!(rec.hour[2], data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1));
}

#[test]
fn data_new() {
    let tmpdir = TempDir::new("").unwrap();
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    assert_eq!(data.records.read().unwrap().len(), 0);
}

#[test]
fn data_get_record() {
    let tmpdir = TempDir::new("").unwrap();
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    assert!(data.get_record(data::RecordType::Element, "test_id".to_owned()).is_none());
    data.add_usage(data::RecordType::Element, "test_id".to_owned(), &data::InternalUsage::zero(), util::now());
    assert!(data.get_record(data::RecordType::Element, "test_id".to_owned()).is_some());
}

#[test]
fn data_record_path() {
    let tmpdir = TempDir::new("").unwrap();
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    assert_eq!(data.record_path(data::RecordType::Topology, "test_id"), tmpdir.path().to_owned().join("topology").join("test_id"));
}

#[test]
fn data_store_record() {
    let tmpdir = TempDir::new("").unwrap();
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    data.add_usage(data::RecordType::Element, "test_id".to_owned(), &data::InternalUsage::zero(), 0);
    let rec = data.get_record(data::RecordType::Element, "test_id".to_owned()).unwrap();
    assert!(!data.record_path(data::RecordType::Element, "test_id").exists());
    data.store_record(data::RecordType::Element, "test_id", &rec).unwrap();
    assert!(data.record_path(data::RecordType::Element, "test_id").exists());
}

#[test]
fn data_store_all() {
    let tmpdir = TempDir::new("").unwrap();
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    data.add_usage(data::RecordType::Element, "test_id_1".to_owned(), &data::InternalUsage::zero(), util::now());
    data.add_usage(data::RecordType::Element, "test_id_2".to_owned(), &data::InternalUsage::zero(), util::now());
    assert_eq!(data.store_all().unwrap(), 2);
    assert!(data.record_path(data::RecordType::Element, "test_id_1").exists());
    assert!(data.record_path(data::RecordType::Element, "test_id_2").exists());
    data.add_usage(data::RecordType::Element, "test_id_1".to_owned(), &data::InternalUsage::zero(), util::now());
    data.add_usage(data::RecordType::Element, "test_id_3".to_owned(), &data::InternalUsage::zero(), util::now());
    assert!(data.store_all().unwrap() >= 2);
    assert!(data.record_path(data::RecordType::Element, "test_id_1").exists());
    assert!(data.record_path(data::RecordType::Element, "test_id_3").exists());
}

#[test]
fn data_load_record() {
    let tmpdir = TempDir::new("").unwrap();
    let data1 = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    data1.add_usage(data::RecordType::Element, "test_id".to_owned(), &data::InternalUsage::zero(), util::now());
    data1.store_all().unwrap();
    let data2 = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    data2.load_record(data::RecordType::Element, "test_id").unwrap();
}

#[test]
fn data_load_all() {
    let tmpdir = TempDir::new("").unwrap();
    let data1 = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    data1.add_usage(data::RecordType::Element, "test_id".to_owned(), &data::InternalUsage::zero(), util::now());
    data1.store_all().unwrap();
    let data2 = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    data2.load_all().unwrap();
    assert!(data2.get_record(data::RecordType::Element, "test_id".to_owned()).is_some());
}

#[test]
fn data_add_organization_usage() {
    set_logger();
    let tmpdir = TempDir::new("").unwrap();
    let hierarchy = hierarchy::HierarchyCache::new(Box::new(hierarchy::DummyHierarchy), 1000);
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy));
    data.add_organization_usage("org1", &mut data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 1);
    assert_eq!(data.get_record(data::RecordType::Organization, "org1".to_owned()).unwrap().cur().memory, 1.0);
}

#[test]
fn data_add_user_usage() {
    let tmpdir = TempDir::new("").unwrap();
    let hierarchy = hierarchy::HierarchyCache::new(Box::new(hierarchy::DummyHierarchy), 1000);
    hierarchy.put(data::RecordType::User, "user1".to_owned(), data::RecordType::Organization, vec!["org1".to_owned()]);
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy));
    data.add_user_usage("user1", &mut data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 1);
    assert_eq!(data.get_record(data::RecordType::User, "user1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Organization, "org1".to_owned()).unwrap().cur().memory, 1.0);
}

#[test]
fn data_add_topology_usage() {
    let tmpdir = TempDir::new("").unwrap();
    let hierarchy = hierarchy::HierarchyCache::new(Box::new(hierarchy::DummyHierarchy), 1000);
    hierarchy.put(data::RecordType::User, "user1".to_owned(), data::RecordType::Organization, vec!["org1".to_owned()]);
    hierarchy.put(data::RecordType::User, "user2".to_owned(), data::RecordType::Organization, vec!["org1".to_owned()]);
    hierarchy.put(data::RecordType::Topology, "top1".to_owned(), data::RecordType::User, vec!["user1".to_owned(), "user2".to_owned()]);
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy));
    data.add_topology_usage("top1", &mut data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 1);
    assert_eq!(data.get_record(data::RecordType::Topology, "top1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::User, "user1".to_owned()).unwrap().cur().memory, 0.5);
    assert_eq!(data.get_record(data::RecordType::User, "user2".to_owned()).unwrap().cur().memory, 0.5);
    assert_eq!(data.get_record(data::RecordType::Organization, "org1".to_owned()).unwrap().cur().memory, 1.0);
}

#[test]
fn data_add_element_usage() {
    let tmpdir = TempDir::new("").unwrap();
    let hierarchy = hierarchy::HierarchyCache::new(Box::new(hierarchy::DummyHierarchy), 1000);
    hierarchy.put(data::RecordType::User, "user1".to_owned(), data::RecordType::Organization, vec!["org1".to_owned()]);
    hierarchy.put(data::RecordType::Topology, "top1".to_owned(), data::RecordType::User, vec!["user1".to_owned()]);
    hierarchy.put(data::RecordType::Element, "elem1".to_owned(), data::RecordType::Topology, vec!["top1".to_owned()]);
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy));
    data.add_element_usage("elem1", &mut data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 1);
    assert_eq!(data.get_record(data::RecordType::Element, "elem1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Topology, "top1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::User, "user1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Organization, "org1".to_owned()).unwrap().cur().memory, 1.0);
}

#[test]
fn data_add_connection_usage() {
    let tmpdir = TempDir::new("").unwrap();
    let hierarchy = hierarchy::HierarchyCache::new(Box::new(hierarchy::DummyHierarchy), 1000);
    hierarchy.put(data::RecordType::User, "user1".to_owned(), data::RecordType::Organization, vec!["org1".to_owned()]);
    hierarchy.put(data::RecordType::Topology, "top1".to_owned(), data::RecordType::User, vec!["user1".to_owned()]);
    hierarchy.put(data::RecordType::Connection, "con1".to_owned(), data::RecordType::Topology, vec!["top1".to_owned()]);
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy));
    data.add_connection_usage("con1", &mut data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 1);
    assert_eq!(data.get_record(data::RecordType::Connection, "con1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Topology, "top1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::User, "user1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Organization, "org1".to_owned()).unwrap().cur().memory, 1.0);
}

#[test]
fn data_add_host_element_usage() {
    let tmpdir = TempDir::new("").unwrap();
    let hierarchy = hierarchy::HierarchyCache::new(Box::new(hierarchy::DummyHierarchy), 1000);
    hierarchy.put(data::RecordType::User, "user1".to_owned(), data::RecordType::Organization, vec!["org1".to_owned()]);
    hierarchy.put(data::RecordType::Topology, "top1".to_owned(), data::RecordType::User, vec!["user1".to_owned()]);
    hierarchy.put(data::RecordType::Connection, "con1".to_owned(), data::RecordType::Topology, vec!["top1".to_owned()]);
    hierarchy.put(data::RecordType::Element, "elem1".to_owned(), data::RecordType::Topology, vec!["top1".to_owned()]);
    hierarchy.put(data::RecordType::HostElement, "hel1".to_owned(), data::RecordType::Element, vec!["elem1".to_owned()]);
    hierarchy.put(data::RecordType::HostElement, "hel2".to_owned(), data::RecordType::Connection, vec!["con1".to_owned()]);
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy));
    data.add_host_element_usage("hel1", &mut data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 1);
    data.add_host_element_usage("hel2", &mut data::InternalUsage::new(2.0, 2.0, 2.0, 2.0, 1), 1);
    assert_eq!(data.get_record(data::RecordType::Element, "elem1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Connection, "con1".to_owned()).unwrap().cur().memory, 2.0);
    assert_eq!(data.get_record(data::RecordType::Topology, "top1".to_owned()).unwrap().cur().memory, 3.0);
    assert_eq!(data.get_record(data::RecordType::User, "user1".to_owned()).unwrap().cur().memory, 3.0);
    assert_eq!(data.get_record(data::RecordType::Organization, "org1".to_owned()).unwrap().cur().memory, 3.0);
}

#[test]
fn data_add_host_connection_usage() {
    let tmpdir = TempDir::new("").unwrap();
    let hierarchy = hierarchy::HierarchyCache::new(Box::new(hierarchy::DummyHierarchy), 1000);
    hierarchy.put(data::RecordType::User, "user1".to_owned(), data::RecordType::Organization, vec!["org1".to_owned()]);
    hierarchy.put(data::RecordType::Topology, "top1".to_owned(), data::RecordType::User, vec!["user1".to_owned()]);
    hierarchy.put(data::RecordType::Connection, "con1".to_owned(), data::RecordType::Topology, vec!["top1".to_owned()]);
    hierarchy.put(data::RecordType::HostConnection, "hcon1".to_owned(), data::RecordType::Connection, vec!["con1".to_owned()]);
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy));
    data.add_host_connection_usage("hcon1", &mut data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 1);
    assert_eq!(data.get_record(data::RecordType::Connection, "con1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Topology, "top1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::User, "user1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Organization, "org1".to_owned()).unwrap().cur().memory, 1.0);
}

#[test]
fn data_api_add_host_element_usage() {
    let tmpdir = TempDir::new("").unwrap();
    let hierarchy = hierarchy::HierarchyCache::new(Box::new(hierarchy::DummyHierarchy), 1000);
    hierarchy.put(data::RecordType::User, "user1".to_owned(), data::RecordType::Organization, vec!["org1".to_owned()]);
    hierarchy.put(data::RecordType::Topology, "top1".to_owned(), data::RecordType::User, vec!["user1".to_owned()]);
    hierarchy.put(data::RecordType::Connection, "con1".to_owned(), data::RecordType::Topology, vec!["top1".to_owned()]);
    hierarchy.put(data::RecordType::Element, "elem1".to_owned(), data::RecordType::Topology, vec!["top1".to_owned()]);
    hierarchy.put(data::RecordType::HostElement, "hel1".to_owned(), data::RecordType::Element, vec!["elem1".to_owned()]);
    hierarchy.put(data::RecordType::HostElement, "hel2".to_owned(), data::RecordType::Connection, vec!["con1".to_owned()]);
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy));
    data.api_add_host_element_usage("hel1", &mut data::Usage::new(1.0, 1.0, 1.0, 1.0, 1), 0);
    data.api_add_host_element_usage("hel2", &mut data::Usage::new(2.0, 2.0, 2.0, 2.0, 1), 0);
    data.api_add_host_element_usage("hel1", &mut data::Usage::new(1.0, 1.0, 1.0, 1.0, 1), 1);
    data.api_add_host_element_usage("hel2", &mut data::Usage::new(2.0, 2.0, 2.0, 2.0, 1), 1);
    assert_eq!(data.get_record(data::RecordType::Element, "elem1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Connection, "con1".to_owned()).unwrap().cur().memory, 2.0);
    assert_eq!(data.get_record(data::RecordType::Topology, "top1".to_owned()).unwrap().cur().memory, 3.0);
    assert_eq!(data.get_record(data::RecordType::User, "user1".to_owned()).unwrap().cur().memory, 3.0);
    assert_eq!(data.get_record(data::RecordType::Organization, "org1".to_owned()).unwrap().cur().memory, 3.0);
}

#[test]
fn data_api_add_host_connection_usage() {
    let tmpdir = TempDir::new("").unwrap();
    let hierarchy = hierarchy::HierarchyCache::new(Box::new(hierarchy::DummyHierarchy), 1000);
    hierarchy.put(data::RecordType::User, "user1".to_owned(), data::RecordType::Organization, vec!["org1".to_owned()]);
    hierarchy.put(data::RecordType::Topology, "top1".to_owned(), data::RecordType::User, vec!["user1".to_owned()]);
    hierarchy.put(data::RecordType::Connection, "con1".to_owned(), data::RecordType::Topology, vec!["top1".to_owned()]);
    hierarchy.put(data::RecordType::HostConnection, "hcon1".to_owned(), data::RecordType::Connection, vec!["con1".to_owned()]);
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy));
    data.api_add_host_connection_usage("hcon1", &mut data::Usage::new(1.0, 1.0, 1.0, 1.0, 1), 0);
    data.api_add_host_connection_usage("hcon1", &mut data::Usage::new(1.0, 1.0, 1.0, 1.0, 1), 1);
    assert_eq!(data.get_record(data::RecordType::Connection, "con1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Topology, "top1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::User, "user1".to_owned()).unwrap().cur().memory, 1.0);
    assert_eq!(data.get_record(data::RecordType::Organization, "org1".to_owned()).unwrap().cur().memory, 1.0);
}
