#[macro_use] extern crate log;
extern crate env_logger;
pub extern crate rmp;
extern crate net2;
extern crate libc;
extern crate epoll;
pub extern crate openssl;
extern crate fnv;

#[macro_use] mod util;
mod errors;
mod socket;
mod msgs;
mod server;
mod client;
mod wrapper;

pub use server::{Server, Method, ServerCloseGuard};
pub use client::{Client, ClientCloseGuard};
pub use errors::Error;
pub use socket::Connection;
pub use rmp::Value;
pub use rmp::value::Integer;
pub use rmp::value::Float;
pub use util::{ToValue, ParseError, ParseValue};
pub use msgs::{Args, KwArgs};
pub use wrapper::Params;

use std::sync::{Once, ONCE_INIT};

static LOGGER_INIT: Once = ONCE_INIT;

pub fn init() {
    LOGGER_INIT.call_once(|| {
        env_logger::init().unwrap();
    });
}
