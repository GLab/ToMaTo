#![cfg_attr(feature = "bench", feature(test))]
#[cfg(feature = "bench")] extern crate test;
#[cfg(test)] extern crate tempdir;
#[cfg(test)] mod tests;
#[cfg(feature = "bench")] mod benches;

extern crate time;
extern crate fnv;
#[macro_use] extern crate sslrpc2;

pub mod data;
pub mod util;
pub mod hierarchy;
pub mod api;

//TODO: logging
//TODO: yaml config file
//TODO: fetch hierarchy information
//TODO: periodically store records
//TODO: periodically remove very old ids
//TODO: fix usage integration

use std::thread;
use std::time::Duration;

use sslrpc2::openssl::ssl::{SslContext, SslMethod, SSL_VERIFY_PEER, SSL_VERIFY_FAIL_IF_NO_PEER_CERT};
use sslrpc2::openssl::x509::X509FileType;
use data::Data;
use hierarchy::{DummyHierarchy, HierarchyCache};
use api::ApiServer;

const DEFAULT_CIPHERS: &'static str = "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:ECDHE-RSA-AES128-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA128:DHE-RSA-AES128-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA128:ECDHE-RSA-AES128-SHA384:ECDHE-RSA-AES128-SHA128:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA384:AES128-GCM-SHA128:AES128-SHA128:AES128-SHA128:AES128-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4";

fn main() {
    let mut ssl_context = SslContext::new(SslMethod::Sslv23).unwrap();
    ssl_context.set_cipher_list(DEFAULT_CIPHERS).unwrap();
    ssl_context.set_private_key_file("certs/alice_key.pem", X509FileType::PEM).unwrap();
    ssl_context.set_certificate_chain_file("certs/alice_cert.pem", X509FileType::PEM).unwrap();
    ssl_context.set_CA_file("certs/good_ca_root.pem").unwrap();
    ssl_context.set_verify(SSL_VERIFY_PEER | SSL_VERIFY_FAIL_IF_NO_PEER_CERT, None);
    let data = Data::new("data", Box::new(HierarchyCache::new(Box::new(DummyHierarchy), 3600)));
    data.load_all().expect("Failed to load");
    let _server = ApiServer::new(data, "0.0.0.0:8005", ssl_context).unwrap();
    loop {
        thread::sleep(Duration::from_millis(1000));
    }
}
