use std::net::{TcpStream, ToSocketAddrs};
use std::collections::HashMap;
use std::sync::{Arc, Mutex, Condvar};
use std::sync::atomic::{AtomicUsize, Ordering, AtomicBool};
use std::io;
use std::io::Write;
use std::ops::Deref;
use std::thread;
use std::time::Duration;
use std::mem;
use std::borrow::Cow;

use super::errors::{Error, NetworkError};
use super::msgs::{Reply, Request, Message};
use super::socket::Connection;

use rmp;
use net2::TcpStreamExt;
use openssl::ssl::{SslContext, SslStream};
use openssl::ssl::error::SslError;

pub type Callback = Box<FnMut(Result<rmp::Value, Error>) + Send>;

pub struct ClientInner {
    socket: Arc<Connection>,
    replies: Mutex<HashMap<usize, Result<rmp::Value, Error>>>,
    next_id: AtomicUsize,
    event: Condvar,
    running: AtomicBool,
}

#[derive(Clone)]
pub struct Client(Arc<ClientInner>);

impl Deref for Client {
    type Target = ClientInner;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl Client {
    pub fn new<A: ToSocketAddrs>(addr: A, ssl: SslContext) -> Result<ClientCloseGuard, SslError> {
        let tcp_con = try!(TcpStream::connect(addr).map_err(|err| SslError::StreamError(err)));
        let ssl_con = try!(SslStream::connect(&ssl, tcp_con));
        let con = Arc::new(Connection::new(ssl_con));
        let client = Client(Arc::new(ClientInner{
            socket: con.clone(),
            replies: Mutex::new(HashMap::new()),
            next_id: AtomicUsize::new(1),
            event: Condvar::new(),
            running: AtomicBool::new(true)
        }));
        let client2 = client.clone();
        let thread = thread::Builder::new().name("client_connection".to_owned()).spawn(move || client2.run_client(con)).expect("Failed to spawn client thread");
        Ok(ClientCloseGuard{client: client, thread: Some(thread)})
    }

    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::Relaxed)
    }

    pub fn close(&self) -> Result<(), io::Error> {
        if ! self.running.swap(false, Ordering::Relaxed) {
            return Ok(())
        }
        self.socket.close()
    }

    fn run_client(&self, con: Arc<Connection>) {
        info!("Client connected to server at {}", con.peer_addr().expect("Failed to get server address"));
        while self.is_running() {
            match Reply::from_bytes(&con) {
                Ok(reply) => {
                    info!("Received reply: {:?}", reply);
                    let (id, val) = match reply {
                        Reply::Success(id, val) => (id, Ok(val)),
                        Reply::Failure(id, err) => (id, Err(Error::Failure(err))),
                        Reply::NoSuchMethod(id, name) => (id, Err(Error::NoSuchMethod(name))),
                        Reply::RequestError(Some(id), code) => {
                            warn!("Invalid request, id: {}, code: {:?}", id, code);
                            (id, Err(Error::MessageError(code, Some(id))))
                        },
                        Reply::RequestError(None, code) => {
                            error!("Invalid request, id unknown, code: {:?}", code);
                            continue
                        }
                    };
                    self.replies.lock().expect("Lock poisoned").insert(id as usize, val);
                    self.event.notify_all();
                },
                Err(Error::ConnectionEnded) => {
                    info!("Client connection ended");
                    return
                },
                Err(err) => error!("Failed to decode reply: {:?}", err)
            }
        }
    }

    #[inline]
    pub fn send_request(&self, method: String, args: Vec<rmp::Value>, kwargs: HashMap<Cow<'static, str>, rmp::Value>) -> Result<usize, Error> {
        let id = self.next_id.fetch_add(1, Ordering::Relaxed);
        let req = Request{
            id: id as u64,
            method: method,
            args: args,
            kwargs: kwargs
        };
        info!("Sending request: {:?}", req);
        try!(self.socket.write(&req.to_bytes()).map_err(|_| Error::NetworkError(NetworkError::WriteError)));
        Ok(id)
    }

    pub fn fetch_reply(&self, id: usize) -> Option<Result<rmp::Value, Error>> {
        self.replies.lock().expect("Lock poisoned").remove(&id)
    }

    pub fn wait_for_reply(&self, id: usize, timeout: Option<Duration>) -> Result<rmp::Value, Error> {
        loop {
            let mut replies = self.replies.lock().expect("Lock poisoned");
            match replies.remove(&id) {
                Some(val) => return val,
                None => match timeout {
                    Some(timeout) => {
                        let res = self.event.wait_timeout(replies, timeout).expect("Lock poisoned");
                        if res.1.timed_out() {
                            return Err(Error::TimedOut);
                        }
                    },
                    None => {
                        let _ = self.event.wait(replies).expect("Lock poisoned");
                    }
                }
            }
        }
    }

    pub fn call(&self, method: String, args: Vec<rmp::Value>, kwargs: HashMap<Cow<'static, str>, rmp::Value>, timeout: Option<Duration>) -> Result<rmp::Value, Error> {
        let id = try!(self.send_request(method, args, kwargs));
        self.wait_for_reply(id, timeout)
    }

    pub fn call_async(&self, method: String, args: Vec<rmp::Value>, kwargs: HashMap<Cow<'static, str>, rmp::Value>, timeout: Option<Duration>, mut callback: Callback) -> Result<(), Error> {
        let id = try!(self.send_request(method, args, kwargs));
        let self2 = self.clone();
        thread::spawn(move || callback(self2.wait_for_reply(id, timeout)));
        Ok(())
    }
}


pub struct ClientCloseGuard{
    client: Client,
    thread: Option<thread::JoinHandle<()>>
}

impl Deref for ClientCloseGuard {
    type Target = Client;

    fn deref(&self) -> &Self::Target {
        &self.client
    }
}

impl Drop for ClientCloseGuard {
    fn drop(&mut self) {
        self.close().expect("Failed to close client");
        let mut thread = None;
        mem::swap(&mut thread, &mut self.thread);
        thread.unwrap().join().expect("Failed to join thread");
    }
}
