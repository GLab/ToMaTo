#![cfg_attr(feature = "bench", feature(test))]
#[cfg(feature = "bench")] extern crate test;
#[cfg(test)] extern crate tempdir;
#[cfg(test)] mod tests;
#[cfg(feature = "bench")] mod benches;

extern crate time;
extern crate fnv;
extern crate yaml_rust;
extern crate signal;
extern crate nix;
extern crate libc;
#[macro_use] extern crate sslrpc2;
#[macro_use] extern crate log;

pub mod data;
pub mod util;
pub mod hierarchy;
pub mod api;

//TODO: snappy compression?
//TODO: f64?
//TODO: save on terminate

use std::thread;
use std::time::Duration;
use std::fs::File;
use std::path::Path;
use std::env;
use std::io::Read;
use std::str::FromStr;
use std::sync::Arc;

use sslrpc2::openssl::ssl::{SslContext, SslMethod, SSL_VERIFY_PEER, SSL_VERIFY_FAIL_IF_NO_PEER_CERT};
use sslrpc2::openssl::x509::X509FileType;
use data::Data;
use hierarchy::{HierarchyCache, RemoteHierarchy};
use api::ApiServer;
use util::Time;
use yaml_rust::YamlLoader;
use nix::sys::signal::{SIGTERM, SIGQUIT, SIGINT};
use signal::trap::Trap;
use time::SteadyTime;

const DEFAULT_CIPHERS: &'static str = "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:ECDHE-RSA-AES128-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA128:DHE-RSA-AES128-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA128:ECDHE-RSA-AES128-SHA384:ECDHE-RSA-AES128-SHA128:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA384:AES128-GCM-SHA128:AES128-SHA128:AES128-SHA128:AES128-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4";

#[derive(Debug)]
struct Config {
    ssl_ciphers: String,
    ssl_key_file: String,
    ssl_cert_file: String,
    ssl_ca_file: String,
    data_path: String,
    hierarchy_cache_timeout: Time,
    store_interval: Time,
    cleanup_interval: Time,
    max_record_age: Time,
    listen_address: String,
    log_level: log::LogLevelFilter,
    user_service_address: String,
    core_service_address: String,
    service_timeout: Time,
}

impl Config {
    fn load(path: &Path) -> Self {
        let mut text = String::default();
        File::open(path).expect("Failed to open config file").read_to_string(&mut text).expect("Failed to read config");
        let docs = YamlLoader::load_from_str(&text).expect("Failed to parse YAML config");
        let doc = &docs[0];
        Config {
            ssl_ciphers: doc["ssl"]["ciphers"].as_str().unwrap_or(DEFAULT_CIPHERS).to_owned(),
            ssl_key_file: doc["ssl"]["key_file"].as_str().expect("SSL key file unset").to_owned(),
            ssl_cert_file: doc["ssl"]["cert_file"].as_str().expect("SSL cert file unset").to_owned(),
            ssl_ca_file: doc["ssl"]["ca_file"].as_str().expect("SSL ca file unset").to_owned(),
            data_path: doc["data_path"].as_str().expect("Data path unset").to_owned(),
            hierarchy_cache_timeout: doc["hierarchy_cache_timeout"].as_i64().unwrap_or(3600),
            store_interval: doc["store_interval"].as_i64().unwrap_or(60),
            cleanup_interval: doc["cleanup_interval"].as_i64().unwrap_or(3600),
            max_record_age: doc["max_record_age"].as_i64().unwrap_or(24*3600*14),
            listen_address: doc["listen_address"].as_str().expect("Listen address unset").to_owned(),
            log_level: log::LogLevelFilter::from_str(doc["log_level"].as_str().unwrap_or("info")).expect("Invalid log level"),
            user_service_address: doc["service_addresses"]["backend_users"].as_str().expect("User service address unset").to_owned(),
            core_service_address: doc["service_addresses"]["backend_core"].as_str().expect("Core service address unset").to_owned(),
            service_timeout: doc["service_timeout"].as_i64().unwrap_or(30),
        }
    }
}

struct SimpleLogger;

impl log::Log for SimpleLogger {
    #[inline(always)]
    fn enabled(&self, metadata: &log::LogMetadata) -> bool {
        metadata.target().starts_with(module_path!())
    }

    #[inline(always)]
    fn log(&self, record: &log::LogRecord) {
        if self.enabled(record.metadata()) {
            println!("{} - {}", record.level(), record.args());
        }
    }
}

fn main() {
    let config = Config::load(Path::new(&env::args().nth(1).expect("Config file must be given as parameter")));
    log::set_logger(|max_log_level| {
        max_log_level.set(config.log_level);
        Box::new(SimpleLogger)
    }).unwrap();
    debug!("Config: {:?}", config);
    let mut ssl_context = SslContext::new(SslMethod::Sslv23).unwrap();
    ssl_context.set_cipher_list(&config.ssl_ciphers).unwrap();
    ssl_context.set_private_key_file(config.ssl_key_file, X509FileType::PEM).unwrap();
    ssl_context.set_certificate_chain_file(config.ssl_cert_file, X509FileType::PEM).unwrap();
    ssl_context.set_CA_file(config.ssl_ca_file).unwrap();
    ssl_context.set_verify(SSL_VERIFY_PEER | SSL_VERIFY_FAIL_IF_NO_PEER_CERT, None);
    let remote_hierarchy = RemoteHierarchy::new(ssl_context.clone(), config.core_service_address, config.user_service_address, config.service_timeout).expect("Failed to connect to remote services");
    let hierarchy_cache = HierarchyCache::new(Box::new(remote_hierarchy), config.hierarchy_cache_timeout);
    let data = Data::new(config.data_path, Box::new(hierarchy_cache));
    info!("Loading data from filesystem...");
    data.load_all().expect("Failed to load");
    let data = Arc::new(data);
    let _server = ApiServer::new(data.clone(), &config.listen_address as &str, ssl_context).unwrap();
    info!("done. Server listening on {}", config.listen_address);
    let trap = Trap::trap(&[SIGINT, SIGTERM, SIGQUIT]);
    let dummy_time = SteadyTime::now();
    loop {
        thread::sleep(Duration::from_millis(1000));
        if trap.wait(dummy_time).is_some() {
            break;
        }
        data.housekeep(config.store_interval, config.cleanup_interval, config.max_record_age);
    }
}
