use std::collections::HashMap;
use std::net::{TcpListener, ToSocketAddrs, TcpStream, SocketAddr, Shutdown};
use std::io;
use std::io::Write;
use std::thread;
use std::sync::{Arc, RwLock, Mutex};
use std::sync::atomic::{Ordering, AtomicBool};
use std::ops::Deref;
use std::mem;
use std::os::unix::io::AsRawFd;
use std::borrow::Cow;

use rmp;
use openssl::ssl::{SslContext, SslStream};

use super::msgs::*;
use super::errors::Error;
use super::socket::Connection;
use super::wrapper;
use super::util::ToValue;

pub type Method = Arc<Fn(Vec<rmp::Value>, HashMap<Cow<'static, str>, rmp::Value>) -> Result<rmp::Value, rmp::Value> + Sync + Send>;


pub struct ServerInner {
    ssl: SslContext,
    socket: TcpListener,
    methods: RwLock<HashMap<String, (Method, rmp::Value)>>,
    running: AtomicBool,
    call_threads: Mutex<HashMap<u64, Option<thread::JoinHandle<()>>>>,
    con_threads: Mutex<HashMap<u64, Option<thread::JoinHandle<()>>>>
}

#[derive(Clone)]
pub struct Server(Arc<ServerInner>);

impl Deref for Server {
    type Target = ServerInner;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl Server {
    pub fn new<A: ToSocketAddrs>(addr: A, ssl: SslContext) -> Result<ServerCloseGuard, io::Error> {
        let server = Server(Arc::new(ServerInner {
            ssl: ssl,
            socket: try!(TcpListener::bind(addr)),
            methods: RwLock::new(HashMap::new()),
            running: AtomicBool::new(true),
            call_threads: Mutex::new(HashMap::new()),
            con_threads: Mutex::new(HashMap::new())
        }));
        let copy = server.clone();
        let thread = thread::Builder::new().name("server_socket".to_owned()).spawn(move || copy.run_server()).expect("Failed to spawn thread");
        Ok(ServerCloseGuard{server: server, thread: Some(thread)})
    }

    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::Relaxed)
    }

    pub fn close(&self) -> Result<(), io::Error> {
        if ! self.running.swap(false, Ordering::Relaxed) {
            return Ok(())
        }
        // TODO: Remove this workaround once a proper API is available
        let socket = unsafe { mem::transmute::<&TcpListener, &TcpStream>(&self.socket) };
        socket.shutdown(Shutdown::Both)
    }

    #[inline]
    pub fn get_address(&self) -> Result<SocketAddr, io::Error> {
        self.socket.local_addr()
    }

    #[inline]
    pub fn register(&self, name: String, method: Method, info: rmp::Value) {
        self.methods.write().expect("Lock poisoned").insert(name, (method, info));
    }

    #[inline]
    pub fn register_easy<R: ToValue + 'static, E: ToValue + 'static>(&self, name: String, method: wrapper::Method<R, E>, arg_names: Vec<&'static str>, info: rmp::Value) {
        let method = wrapper::wrap(method, arg_names);
        self.methods.write().expect("Lock poisoned").insert(name, (method, info));
    }

    pub fn register_list_cmd(&self) {
        let self2 = self.clone();
        let method = Arc::new(move |_args, _kwargs| {
            Ok(rmp::Value::Array(self2.methods.read().expect("Lock poisoned").keys().map(|n| rmp::Value::String(n.to_owned())).collect()))
        });
        let info = rmp::Value::Map(vec![]);
        self.register("$list$".to_owned(), method, info);
    }

    #[inline]
    pub fn unregister(&self, name: &str) {
        self.methods.write().expect("Lock poisoned").remove(name);
    }

    fn run_server(&self) {
        info!("Server running on {}", self.get_address().expect("Failed to retrieve address"));
        for sock in self.socket.incoming() {
            match sock {
                Ok(sock) => {
                    let self2 = self.clone();
                    let id = sock.as_raw_fd() as u64;
                    let thread = thread::Builder::new().name("server_connection".to_owned()).spawn(move || {
                        self2.run_connection(sock);
                        self2.con_threads.lock().expect("Lock poisoned").remove(&id);
                    }).expect("Failed to spawn thread");
                    self.con_threads.lock().expect("Lock poisoned").insert(id, Some(thread));
                },
                Err(err) => {
                    if self.is_running() {
                        error!("Failed to accept connection: {}", err);
                    }
                    return
                }
            }
        }
    }

    fn run_connection(&self, sock: TcpStream) {
        info!("Incoming connection from {}", sock.peer_addr().expect("Failed to retrieve client address"));
        let con = match SslStream::accept(&self.ssl, sock) {
            Ok(con) => Arc::new(Connection::new(con)),
            Err(err) => {
                error!("Failed to establish SSL connection: {}", err);
                return;
            }
        };
        while self.is_running() {
            let req = match Request::from_bytes(&con) {
                Ok(req) => req,
                Err(Error::ConnectionEnded) => {
                    info!("Server connection ended");
                    return
                },
                Err(Error::NetworkError(msg)) => {
                    error!("Failed to read request: {:?}", msg);
                    return
                },
                Err(Error::FramingError(msg)) => {
                    error!("Failed to read request: {:?}", msg);
                    return
                },
                Err(Error::MessageError(kind, id)) => {
                    warn!("Invalid request from {}: {:?}", con.peer_addr().expect("Failed to retrieve client address"), kind);
                    match con.write(&Reply::RequestError(id, kind).to_bytes()) {
                        Ok(_) => continue,
                        Err(err) => {
                            error!("Failed to write reply: {}", err);
                            return
                        }
                    }
                },
                _ => unreachable!()
            };
            let id = req.id;
            let self2 = self.clone();
            let con2 = con.clone();
            let thread = thread::Builder::new().name("server_call".to_owned()).spawn(move || {
                let id = req.id;
                self2.run_message(con2, req);
                self2.call_threads.lock().expect("Lock poisoned").remove(&id);
            }).expect("Failed to spawn thread");
            self.call_threads.lock().expect("Lock poisoned").insert(id, Some(thread));
        }
    }

    fn run_message(&self, con: Arc<Connection>, req: Request) {
        info!("Received request: {:?}", req);
        let method = {
            let methods = self.methods.read().expect("Lock poinsoned");
            methods.get(&req.method).map(|&(ref m, ref _info)| m.clone())
        };
        let reply = match method {
            Some(meth) => match meth(req.args, req.kwargs) {
                Ok(result) => Reply::Success(req.id, result),
                Err(error) => Reply::Failure(req.id, error)
            },
            None => Reply::NoSuchMethod(req.id, req.method)
        };
        info!("Sending reply: {:?}", reply);
        match con.write(&reply.to_bytes()) {
            Ok(_) => (),
            Err(err) => {
                error!("Failed to write reply: {}", err);
                return
            }
        }
    }
}

pub struct ServerCloseGuard {
    server: Server,
    thread: Option<thread::JoinHandle<()>>
}

impl Deref for ServerCloseGuard {
    type Target = Server;

    fn deref(&self) -> &Self::Target {
        &self.server
    }
}

impl Drop for ServerCloseGuard {
    fn drop(&mut self) {
        self.close().expect("Failed to close server");
        self.methods.write().expect("Lock poisoned").clear();
        let mut threads = Vec::new();
        let mut thread;
        for (_k, v) in self.con_threads.lock().expect("Lock poisoned").iter_mut() {
            thread = None;
            mem::swap(v, &mut thread);
            threads.push(thread);
        }
        for (_k, v) in self.call_threads.lock().expect("Lock poisoned").iter_mut() {
            thread = None;
            mem::swap(v, &mut thread);
            threads.push(thread);
        }
        thread = None;
        mem::swap(&mut self.thread, &mut thread);
        threads.push(thread);
        for t in threads {
            t.unwrap().join().expect("Failed to join thread");
        }
    }
}
