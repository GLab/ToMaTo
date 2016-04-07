#![feature(test)]

extern crate test;
extern crate sslrpc2;
extern crate rmp;
extern crate openssl;

use test::Bencher;

use sslrpc2::*;

use std::collections::HashMap;
use std::sync::Arc;

use openssl::ssl::{SslContext, SslMethod, SSL_VERIFY_PEER, SSL_VERIFY_FAIL_IF_NO_PEER_CERT};
use openssl::x509::X509FileType;

const CIPHERS: &'static str = "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:ECDHE-RSA-AES128-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA128:DHE-RSA-AES128-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA128:ECDHE-RSA-AES128-SHA384:ECDHE-RSA-AES128-SHA128:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA384:AES128-GCM-SHA128:AES128-SHA128:AES128-SHA128:AES128-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4";
//let CIPHERS = "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";

fn context_alice() -> SslContext {
    let mut context = SslContext::new(SslMethod::Sslv23).unwrap();
    //context.set_ecdh_auto(true).unwrap();
    context.set_cipher_list(CIPHERS).unwrap();
    context.set_private_key_file("../certs/alice_key.pem", X509FileType::PEM).unwrap();
    context.set_certificate_chain_file("../certs/alice_cert.pem", X509FileType::PEM).unwrap();
    context.set_CA_file("../certs/good_ca_root.pem").unwrap();
    context.set_verify(SSL_VERIFY_PEER | SSL_VERIFY_FAIL_IF_NO_PEER_CERT, None);
    context
}

fn context_bob() -> SslContext {
    let mut context = SslContext::new(SslMethod::Sslv23).unwrap();
    context.set_cipher_list(CIPHERS).unwrap();
    context.set_private_key_file("../certs/bob_key.pem", X509FileType::PEM).unwrap();
    context.set_certificate_chain_file("../certs/bob_cert.pem", X509FileType::PEM).unwrap();
    context.set_CA_file("../certs/good_ca_root.pem").unwrap();
    context.set_verify(SSL_VERIFY_PEER | SSL_VERIFY_FAIL_IF_NO_PEER_CERT, None);
    context
}

fn echo(mut args: Vec<rmp::Value>, kwargs: HashMap<String, rmp::Value>) -> Result<rmp::Value, rmp::Value> {
    if args.len() != 1 && kwargs.len() != 0 {
        return Err(rmp::Value::String("Syntax error".to_owned()));
    }
    Ok(args.remove(0))
}

#[bench]
fn full_call(b: &mut Bencher) {
    init();
    let server = Server::new("127.0.0.1:0", context_alice()).unwrap();
    server.register("echo".to_owned(), Arc::new(echo));
    let context = context_bob();
    b.iter(|| {
        let client = Client::new(server.get_address().unwrap(), context.clone()).unwrap();
        assert_eq!(client.call("echo".to_owned(), vec![rmp::Value::Nil], HashMap::new(), None), Ok(rmp::Value::Nil))
    });
}

#[bench]
fn simple_call(b: &mut Bencher) {
    init();
    let server = Server::new("127.0.0.1:0", context_alice()).unwrap();
    server.register("echo".to_owned(), Arc::new(echo));
    let client = Client::new(server.get_address().unwrap(), context_bob()).unwrap();
    b.iter(|| {
        assert_eq!(client.call("echo".to_owned(), vec![rmp::Value::Nil], HashMap::new(), None), Ok(rmp::Value::Nil))
    });
}

#[bench]
fn compressed_call(b: &mut Bencher) {
    init();
    let server = Server::new("127.0.0.1:0", context_alice()).unwrap();
    server.register("echo".to_owned(), Arc::new(echo));
    let client = Client::new(server.get_address().unwrap(), context_bob()).unwrap();
    let msg = "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789".to_owned();
    b.iter(|| {
        assert_eq!(client.call("echo".to_owned(), vec![rmp::Value::String(msg.clone())], HashMap::new(), None), Ok(rmp::Value::String(msg.clone())))
    });
}
