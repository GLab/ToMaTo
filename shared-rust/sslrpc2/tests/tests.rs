extern crate sslrpc2;
extern crate rmp;
extern crate openssl;

use sslrpc2::*;

use std::thread;
use std::time::Duration;
use std::collections::HashMap;
use std::sync::Arc;
use std::net::{TcpListener, TcpStream};
use std::os::unix::io::AsRawFd;

use openssl::ssl::{SslContext, SslMethod, SslStream, SSL_VERIFY_PEER, SSL_VERIFY_FAIL_IF_NO_PEER_CERT};
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

#[allow(dead_code)]
fn context_charly() -> SslContext {
    let mut context = SslContext::new(SslMethod::Sslv23).unwrap();
    context.set_cipher_list(CIPHERS).unwrap();
    context.set_private_key_file("../certs/charly_key.pem", X509FileType::PEM).unwrap();
    context.set_certificate_chain_file("../certs/charly_cert.pem", X509FileType::PEM).unwrap();
    context.set_CA_file("../certs/bad_ca_root.pem").unwrap();
    context.set_verify(SSL_VERIFY_PEER | SSL_VERIFY_FAIL_IF_NO_PEER_CERT, None);
    context
}


fn wait(args: Vec<rmp::Value>, kwargs: HashMap<String, rmp::Value>) -> Result<rmp::Value, rmp::Value> {
    if args.len() != 1 && kwargs.len() != 0 {
        return Err(rmp::Value::String("Syntax error".to_owned()));
    }
    if let rmp::Value::Integer(rmp::value::Integer::U64(time)) = args[0] {
        thread::sleep(Duration::from_millis(time));
        Ok(rmp::Value::Nil)
    } else {
        Err(rmp::Value::String("Invalid timeout".to_owned()))
    }
}

fn echo(mut args: Vec<rmp::Value>, kwargs: HashMap<String, rmp::Value>) -> Result<rmp::Value, rmp::Value> {
    if args.len() != 1 && kwargs.len() != 0 {
        return Err(rmp::Value::String("Syntax error".to_owned()));
    }
    Ok(args.remove(0))
}

fn current_fd() -> usize {
    TcpListener::bind("127.0.0.1:0").unwrap().as_raw_fd() as usize
}


#[test]
fn simple_call() {
    init();
    let server = Server::new("127.0.0.1:0", context_alice()).unwrap();
    server.register("test".to_owned(), Arc::new(|_args, _kwargs| Ok(rmp::Value::Nil)));
    let client = Client::new(server.get_address().unwrap(), context_bob()).unwrap();
    assert_eq!(client.call("test".to_owned(), vec![], HashMap::new(), None), Ok(rmp::Value::Nil));
}

#[test]
fn list_cmd() {
    init();
    let server = Server::new("127.0.0.1:0", context_alice()).unwrap();
    server.register("test".to_owned(), Arc::new(|_args, _kwargs| Ok(rmp::Value::Nil)));
    server.register_list_cmd();
    let client = Client::new(server.get_address().unwrap(), context_bob()).unwrap();
    let res = client.call("$list$".to_owned(), vec![], HashMap::new(), None);
    if let Ok(rmp::Value::Array(list)) = res {
        assert!(list.contains(&rmp::Value::String("test".to_owned())));
        assert!(list.contains(&rmp::Value::String("$list$".to_owned())));
    } else {
        assert!(false);
    }
}

#[test]
fn compressed_call() {
    init();
    let msg = "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789".to_owned();
    assert_eq!(msg.len(), 100);
    let server = Server::new("127.0.0.1:0", context_alice()).unwrap();
    server.register("echo".to_owned(), Arc::new(echo));
    let client = Client::new(server.get_address().unwrap(), context_bob()).unwrap();
    assert_eq!(client.call("echo".to_owned(), vec![rmp::Value::String(msg.clone())], HashMap::new(), None), Ok(rmp::Value::String(msg)));
}

#[test]
fn parallel_call() {
    init();
    let server = Server::new("0.0.0.0:0", context_alice()).unwrap();
    server.register("wait".to_owned(), Arc::new(wait));
    let client = Client::new(server.get_address().unwrap(), context_bob()).unwrap();
    let id1 = client.send_request("wait".to_owned(), vec![rmp::Value::Integer(rmp::value::Integer::U64(200))], HashMap::new()).unwrap();
    let id2 = client.send_request("wait".to_owned(), vec![rmp::Value::Integer(rmp::value::Integer::U64(100))], HashMap::new()).unwrap();
    assert!(!client.wait_for_reply(id1, Some(Duration::from_millis(0))).is_ok());
    assert!(!client.wait_for_reply(id2, Some(Duration::from_millis(0))).is_ok());
    thread::sleep(Duration::from_millis(150));
    assert!(!client.wait_for_reply(id1, Some(Duration::from_millis(0))).is_ok());
    assert!(client.wait_for_reply(id2, Some(Duration::from_millis(0))).is_ok());
    thread::sleep(Duration::from_millis(100));
    assert!(client.wait_for_reply(id1, Some(Duration::from_millis(0))).is_ok());
}

#[test]
fn ssl() {
    let server_context = context_alice();
    let server_socket = TcpListener::bind("127.0.0.1:0").unwrap();
    let addr = server_socket.local_addr().unwrap();
    thread::spawn(move || {
        let (tcp_con, _addr) = server_socket.accept().unwrap();
        let ssl_con = SslStream::accept(&server_context, tcp_con).unwrap();
        let con = Connection::new(ssl_con);
        let mut buf = [0; 10];
        con.read(&mut buf).unwrap();
        con.write(&buf).unwrap();
    });
    let client_context = context_bob();
    let tcp_con = TcpStream::connect(addr).unwrap();
    let ssl_con = SslStream::connect(&client_context, tcp_con).unwrap();
    let con = Connection::new(ssl_con);
    let mut buf = [0; 10];
    con.write(&buf).unwrap();
    con.read(&mut buf).unwrap();
}

#[test]
fn fds() {
    let start = current_fd();
    simple_call();
    thread::sleep(Duration::from_millis(1000));
    assert_eq!(start, current_fd());
}
