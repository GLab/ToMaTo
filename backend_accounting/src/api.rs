use std::borrow::Cow;
use std::collections::HashMap;
use std::net::ToSocketAddrs;
use std::sync::Arc;
use std::io;

use sslrpc2::{Server, Params, Value, ToValue, ParseValue, ParseError, ServerCloseGuard, rmp, openssl};

use super::data::{Data, RecordType, Record, Usage};
use super::util::{Time, last_five_min, last_hour, last_day, last_month, last_year};

pub struct Error {
    pub module: Cow<'static, str>,
    pub type_: Cow<'static, str>,
    pub code: Cow<'static, str>,
    pub message: Cow<'static, str>,
    pub data: Value
}

impl Error {
    pub fn new(module: &'static str, type_: &'static str, code: &'static str, message: &'static str, data: Value) -> Error {
        Error { module: Cow::Borrowed(module), type_: Cow::Borrowed(type_), code: Cow::Borrowed(code), message: Cow::Borrowed(message), data: data }
    }

    pub fn user(code: &'static str, message: &'static str, data: Value) -> Error {
        Error::new("backend_accounting", "user", code, message, data)
    }

    pub fn missing_param(param: &'static str) -> Error {
        Error::user("missing_param", "missing parameter", to_value!{"param" => param})
    }

    pub fn invalid_param(param: &'static str) -> Error {
        Error::user("invalid_param", "invalid parameter", to_value!{"param" => param})
    }
}

impl ToValue for Error {
    fn to_value(self) -> Value {
        to_value!{
            "module" => self.module.into_owned(),
            "type" => self.type_.into_owned(),
            "code" => self.code.into_owned(),
            "message" => self.message.into_owned(),
            "data" => self.data
        }
    }
}

impl ParseValue for RecordType {
    fn parse(name: Value) -> Result<Self, ParseError> {
        match name {
            Value::String(name) => match &name as &str {
                "host_element" => Ok(RecordType::HostElement),
                "host_connection" => Ok(RecordType::HostConnection),
                "element" => Ok(RecordType::Element),
                "connection" => Ok(RecordType::Connection),
                "topology" => Ok(RecordType::Topology),
                "user" => Ok(RecordType::User),
                "organization" => Ok(RecordType::Organization),
                _ => Err(ParseError)
            },
            _ => Err(ParseError)
        }
    }
}

macro_rules! convert_series {
    ($series:expr, $durfn:ident, $now:expr) => { {
        let mut series: Vec<(Time, Time, Usage)> = $series.into_iter().map(|u| (0, 0, u)).collect();
        let mut end = $now;
        for ref mut rec in series.iter_mut().rev() {
            let start = $durfn(end);
            rec.0 = start;
            rec.1 = end;
            end = start-1;
        }
        let series: Vec<Value> = series.into_iter().map(|(start, end, usage)| to_value!{
            "start" => start,
            "end" => end,
            "usage" => to_value!{
                "memory" => usage.memory,
                "disk" => usage.disk,
                "cputime" => usage.cputime,
                "traffic" => usage.traffic
            },
            "measurements" => usage.measurements
        }).collect();
        series
    } }
}

impl ToValue for Record {
    fn to_value(self) -> Value {
        to_value!{
            "5minutes" => convert_series!(self.five_min, last_five_min, self.timestamp),
            "hour" => convert_series!(self.hour, last_hour, self.timestamp),
            "day" => convert_series!(self.day, last_day, self.timestamp),
            "month" => convert_series!(self.month, last_month, self.timestamp),
            "year" => convert_series!(self.year, last_year, self.timestamp)
        }
    }
}

macro_rules! param {
    ($params:expr, $name:expr, $type_:ident) => {
        try!($type_::parse(try!($params.take($name)
            .ok_or(Error::user("missing_param", "missing parameter", to_value!{"param" => $name}))))
            .map_err(|_| Error::user("invalid_param", "invalid parameter", to_value!{"param" => $name})))
    }
}

#[derive(Clone)]
pub struct Api(Arc<Data>);

impl Api {
    pub fn get_record(&self, mut params: Params) -> Result<Record, Error> {
        debug!("API call get_record {:?}", params);
        let type_ = param!(params, "type", RecordType);
        let id = param!(params, "id", String);
        match self.0.get_record(type_, id) {
            Some(rec) => Ok(rec),
            None => Err(Error::user("no_such_entity", "no such record", Value::Nil))
        }
    }

    pub fn push_usage(&self, mut params: Params) -> Result<(), Error> {
        debug!("API call push_usage {:?}", params);
        type Records = HashMap<String, Vec<(Time, f32, f32, f32, f32, u32)>>;
        let elements = param!(params, "elements", Records);
        let connections = param!(params, "connections", Records);
        for (id, records) in elements {
            for rec in records {
                let time = rec.0;
                let mut usage = Usage::new(rec.1, rec.2, rec.3, rec.4, rec.5);
                self.0.add_host_element_usage(&id, &mut usage, time);
            }
        }
        for (id, records) in connections {
            for rec in records {
                let time = rec.0;
                let mut usage = Usage::new(rec.1, rec.2, rec.3, rec.4, rec.5);
                self.0.add_host_connection_usage(&id, &mut usage, time);
            }
        }
        Ok(())
    }

    pub fn store_all(&self, params: Params) -> Result<usize, Error> {
        debug!("API call store_all {:?}", params);
        Ok(self.0.store_all().expect("Failed to store"))
    }
}

pub struct ApiServer;

impl ApiServer {
    pub fn new<A: ToSocketAddrs>(data: Data, addr: A, ssl: openssl::ssl::SslContext) -> Result<ServerCloseGuard, io::Error> {
        let api = Api(Arc::new(data));
        let server = try!(Server::new(addr, ssl));
        let tmp_api = api.clone();
        server.register_easy(
            "get_record".to_owned(),
            Box::new(move |params| tmp_api.get_record(params)),
            vec!["type", "id"],
            Value::Nil
        );
        let tmp_api = api.clone();
        server.register_easy(
            "push_usage".to_owned(),
            Box::new(move |params| tmp_api.push_usage(params)),
            vec!["elements", "connections"],
            Value::Nil
        );
        let tmp_api = api.clone();
        server.register_easy(
            "store_all".to_owned(),
            Box::new(move |params| tmp_api.store_all(params)),
            vec![],
            Value::Nil
        );
        server.register_list_cmd();
        Ok(server)
    }
}
