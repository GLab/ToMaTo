use super::*;

use tempdir::TempDir;
use test::Bencher;

#[bench]
fn last_periods(b: &mut Bencher) {
    let now = 1459410971;
    b.iter(|| util::last_periods(now));
}

#[bench]
fn record_encode(b: &mut Bencher) {
    let mut rec = data::Record::new(0, 3, 3, 3, 3, 3);
    rec.add(&data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 0);
    rec.add(&data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 300);
    rec.add(&data::InternalUsage::new(1.0, 1.0, 1.0, 1.0, 1), 3900);
    let mut buf = [0; 32768];
    b.iter(|| rec.encode(&mut buf));
}

#[bench]
fn record_decode(b: &mut Bencher) {
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
    b.iter(|| data::Record::decode(&encoded).unwrap());
}

#[bench]
fn data_add(b: &mut Bencher) {
    let now = 1459410971;
    let usage = data::InternalUsage { memory: 10.0, cputime: 223.0, disk: 324.0, traffic: 213.0, measurements: 1 };
    let tmpdir = TempDir::new("").unwrap();
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    data.add_usage(data::RecordType::Element, "test".to_owned(), &usage, now);
    b.iter(|| data.add_usage(data::RecordType::Element, "test".to_owned(), &usage, now));
}

#[bench]
fn data_get_record(b: &mut Bencher) {
    let tmpdir = TempDir::new("").unwrap();
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    data.add_usage(data::RecordType::Element, "test_id".to_owned(), &data::InternalUsage::zero(), util::now());
    b.iter(|| data.get_record(data::RecordType::Element, "test_id".to_owned()).unwrap());
}

#[bench]
fn data_store_record(b: &mut Bencher) {
    let tmpdir = TempDir::new("").unwrap();
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    data.add_usage(data::RecordType::Element, "test_id".to_owned(), &data::InternalUsage::zero(), 0);
    let rec = data.get_record(data::RecordType::Element, "test_id".to_owned()).unwrap();
    b.iter(|| data.store_record(data::RecordType::Element, "test_id", &rec).unwrap());
}

#[bench]
fn data_load_record(b: &mut Bencher) {
    let tmpdir = TempDir::new("").unwrap();
    let data1 = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    data1.add_usage(data::RecordType::Element, "test_id".to_owned(), &data::InternalUsage::zero(), util::now());
    data1.store_all().unwrap();
    let data2 = data::Data::new(tmpdir.path(), Box::new(hierarchy::DummyHierarchy));
    b.iter(|| data2.load_record(data::RecordType::Element, "test_id").unwrap());
}

#[bench]
fn data_api_add_host_element_usage(b: &mut Bencher) {
    let tmpdir = TempDir::new("").unwrap();
    let hierarchy = hierarchy::HierarchyCache::new(Box::new(hierarchy::DummyHierarchy), 1000);
    hierarchy.put(data::RecordType::User, "user1".to_owned(), data::RecordType::Organization, vec!["org1".to_owned()]);
    hierarchy.put(data::RecordType::Topology, "top1".to_owned(), data::RecordType::User, vec!["user1".to_owned()]);
    hierarchy.put(data::RecordType::Element, "elem1".to_owned(), data::RecordType::Topology, vec!["top1".to_owned()]);
    hierarchy.put(data::RecordType::HostElement, "hel1".to_owned(), data::RecordType::Element, vec!["elem1".to_owned()]);
    let data = data::Data::new(tmpdir.path(), Box::new(hierarchy));
    let mut usage = data::Usage::new(1.0, 1.0, 1.0, 1.0, 1);
    let now = util::now();
    b.iter(|| data.api_add_host_element_usage("hel1", &mut usage, now));
}
