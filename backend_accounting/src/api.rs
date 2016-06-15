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
        series.into_iter().map(|(start, end, usage)| to_value!{
            "start" => start,
            "end" => end,
            "usage" => to_value!{
                "memory" => usage.memory,
                "disk" => usage.disk,
                "cputime" => usage.cputime,
                "traffic" => usage.traffic
            },
            "measurements" => usage.measurements
        }).collect::<Vec<_>>()
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
        //! get_record(type: String, id: String) -> Result<Record, Error>
        //!
        //! Retrieves a full accounting record for the given object
        //!
        //! Parameters:
        //! * type: A string describing the object type, "host_element", "host_connection",
        //!         "element", "connection", "topology", "user", or "organization".
        //! * id: A string specifying the object id.
        //!
        //! Return value:
        //!   A mapping containing the fields "5minutes", "hour", "day", "month", and "year",
        //!   where each field maps to a list of accounting entries.
        //!   Each accounting entry is a mapping containing the following fields:
        //!   - "start", "end": Unix timestamps of the start and end dates of the entry
        //!   - "measurements": The number of measurement points aggregated in the entry.
        //!   - "usage": A mapping of the usage containing the fields "traffic", "cputime",
        //!              "memory", "disk"
        debug!("API call get_record {:?}", params);
        let type_ = param!(params, "type", RecordType);
        let id = param!(params, "id", String);
        match self.0.get_record(type_, id) {
            Some(rec) => Ok(rec),
            None => Err(Error::user("entity_does_not_exist", "no such record", Value::Nil))
        }
    }

    pub fn push_usage(&self, mut params: Params) -> Result<(), Error> {
        //! push_usage(elements: Records, connections: Records) -> Result<(), Error>
        //!
        //! Stores the given usage records
        //!
        //! Parameters:
        //! * elements: A mapping containing lists of usage measurements (values) for host_element ids (keys).
        //!             Each usage measurement is a 5-tuple (timestamp, memory, disk, traffic, cputime).
        //!             The timestamp is a unix timestamp as integer, all other fields are floating point numbers.
        //! * connections: A mapping containing lists of usage measurements (values) for connection_element ids (keys).
        //!
        //! Return value: None
        debug!("API call push_usage {:?}", params);
        type Records = HashMap<String, Vec<(Time, f32, f32, f32, f32)>>;
        let elements = param!(params, "elements", Records);
        let connections = param!(params, "connections", Records);
        for (id, records) in elements {
            for rec in records {
                let time = rec.0;
                let mut usage = Usage::new(rec.1, rec.2, rec.3, rec.4, 1);
                self.0.add_host_element_usage(&id, &mut usage, time);
            }
        }
        for (id, records) in connections {
            for rec in records {
                let time = rec.0;
                let mut usage = Usage::new(rec.1, rec.2, rec.3, rec.4, 1);
                self.0.add_host_connection_usage(&id, &mut usage, time);
            }
        }
        Ok(())
    }

    pub fn ping(&self, _params: Params) -> Result<bool, Error> {
        Ok(true)
    }

    pub fn debug_stats(&self, _params: Params) -> Result<Value, Error> {
        Ok(to_value!{
            "accounting" => to_value!{
            	"record_count" => self.0.records.read().expect("Lock poisoned").len()
            }
        })
    }

    pub fn statistics(&self, _params: Params) -> Result<Value, Error> {
        Ok(to_value!{})
    }

    pub fn server_info(&self, _params: Params) -> Result<Value, Error> {
        Ok(to_value!{})
    }
}

pub struct ApiServer;

impl ApiServer {
    pub fn new<A: ToSocketAddrs>(data: Arc<Data>, addr: A, ssl: openssl::ssl::SslContext) -> Result<ServerCloseGuard, io::Error> {
        let api = Api(data);
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
        server.register_easy::<bool, Error>(
            "ping".to_owned(),
            Box::new(move |params| tmp_api.ping(params)),
            vec![],
            Value::Nil
        );
        let tmp_api = api.clone();
        server.register_easy::<Value, Error>(
            "server_info".to_owned(),
            Box::new(move |params| tmp_api.server_info(params)),
            vec![],
            Value::Nil
        );
        let tmp_api = api.clone();
        server.register_easy::<Value, Error>(
            "statistics".to_owned(),
            Box::new(move |params| tmp_api.statistics(params)),
            vec![],
            Value::Nil
        );
        let tmp_api = api.clone();
        server.register_easy::<Value, Error>(
            "debug_stats".to_owned(),
            Box::new(move |params| tmp_api.debug_stats(params)),
            vec![],
            Value::Nil
        );
        server.register_list_cmd();
        Ok(server)
    }
}
