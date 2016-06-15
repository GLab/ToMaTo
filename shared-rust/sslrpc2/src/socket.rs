use std::net::{TcpStream, SocketAddr, Shutdown};
use std::os::unix::io::{AsRawFd, RawFd, FromRawFd};
use std::sync::Mutex;
use std::io;
use std::thread;
use std::fs::File;

use epoll;
use openssl::ssl::SslStream;
use openssl::ssl::error::Error as SslStreamError;

pub struct Connection {
    epoll_read: RawFd,
    epoll_write: RawFd,
    stream: Mutex<SslStream<TcpStream>>,
    write_lock: Mutex<()>,
    read_lock: Mutex<()>,
}

impl Connection {
    pub fn new(mut con: SslStream<TcpStream>) -> Self {
        con.get_mut().set_nonblocking(true).expect("Failed to set nonblocking");
        con.get_mut().set_nodelay(true).expect("Failed to set nodelay");
        let fd = con.as_raw_fd();
        let epoll_read = epoll::create1(0).expect("Failed to create epoll handle");
        let epoll_write = epoll::create1(0).expect("Failed to create epoll handle");
        let mut event_read = epoll::EpollEvent{events: epoll::util::event_type::EPOLLIN, data: 0};
        epoll::ctl(epoll_read, epoll::util::ctl_op::ADD, fd, &mut event_read).expect("Epoll ctl failed");
        let mut event_write = epoll::EpollEvent{events: epoll::util::event_type::EPOLLOUT, data: 0};
        epoll::ctl(epoll_write, epoll::util::ctl_op::ADD, fd, &mut event_write).expect("Epoll ctl failed");
        if epoll_read > 100 {
            panic!("Unclosed fds!!!");
        }
        Connection {
            epoll_read: epoll_read,
            epoll_write: epoll_write,
            stream: Mutex::new(con),
            read_lock: Mutex::new(()),
            write_lock: Mutex::new(())
        }
    }

    pub fn peer_addr(&self) -> Option<SocketAddr> {
        self.stream.lock().expect("Lock poisoned").get_ref().peer_addr().ok()
    }

    pub fn close(&self) -> Result<(), io::Error> {
        debug!("Closing connection: {:?}", thread::current().name());
        self.stream.lock().expect("Lock poisoned").get_ref().shutdown(Shutdown::Both)
    }

    pub fn write(&self, data: &[u8]) -> Result<(), SslStreamError> {
        trace!("Write start: {:?}", thread::current().name());
        let _lock = self.write_lock.lock().expect("Lock poisoned");
        let mut events = [epoll::EpollEvent{events: 0, data: 0}; 1];
        let mut written = 0;
        loop {
            trace!("Before lock on write: {:?}", thread::current().name());
            let res = {
                let mut lock = self.stream.lock().expect("Lock poisoned");
                lock.ssl_write(&data[written..])
            };
            trace!("After lock on write: {:?}", thread::current().name());
            match res {
                Ok(size) => {
                    written += size;
                    if written >= data.len() {
                        debug!("Write success: {:?}", thread::current().name());
                        return Ok(());
                    }
                    if size == 0 {
                        return Err(SslStreamError::ZeroReturn);
                    }
                }
                Err(SslStreamError::WantRead(_)) => {
                    trace!("Waiting on read: {:?}", thread::current().name());
                    epoll::wait(self.epoll_read, &mut events, 1000).expect("Epoll wait failed");
                },
                Err(SslStreamError::WantWrite(_)) => {
                    trace!("Waiting on write: {:?}", thread::current().name());
                    epoll::wait(self.epoll_write, &mut events, 1000).expect("Epoll wait failed");
                },
                Err(other) => {
                    debug!("Write failed: {:?}", thread::current().name());
                    return Err(other)
                }
            }
        }
    }

    pub fn read(&self, buffer: &mut[u8]) -> Result<(), SslStreamError> {
        trace!("Read begin: {:?}", thread::current().name());
        let _lock = self.read_lock.lock().expect("Lock poisoned");
        let mut events = [epoll::EpollEvent{events: 0, data: 0}; 1];
        let mut read = 0;
        loop {
            trace!("Before lock on read: {:?}", thread::current().name());
            let res = {
                let mut lock = self.stream.lock().expect("Lock poisoned");
                lock.ssl_read(&mut buffer[read..])
            };
            trace!("After lock on read: {:?}", thread::current().name());
            match res {
                Ok(size) => {
                    read += size;
                    if read >= buffer.len() {
                        trace!("Read success: {:?}", thread::current().name());
                        return Ok(());
                    }
                    if size == 0 {
                        return Err(SslStreamError::ZeroReturn);
                    }
                },
                Err(SslStreamError::WantRead(_)) => {
                    epoll::wait(self.epoll_read, &mut events, 1000).expect("Epoll wait failed");
                },
                Err(SslStreamError::WantWrite(_)) => {
                    epoll::wait(self.epoll_write, &mut events, 1000).expect("Epoll wait failed");
                },
                Err(other) => {
                    debug!("Read failed 3: {:?}, {:?}", thread::current().name(), other);
                    return Err(other)
                }
            }
        }
    }
}

impl Drop for Connection {
    fn drop(&mut self) {
        unsafe {
            File::from_raw_fd(self.epoll_read);
            File::from_raw_fd(self.epoll_write);
        }
    }
}
