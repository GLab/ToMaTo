use std::collections::HashMap;
use std::io::{Read, Write, Cursor};
use std::io;
use std::borrow::Cow;

use rmp;
use libc::{c_int, size_t};
use openssl::ssl::error::Error as SslStreamError;

use super::errors::{Error, NetworkError, FramingError, MessageErrorCode};
use super::socket::Connection;

#[link(name="snappy")]
extern {
    fn snappy_compress(input: *const u8,
                       input_length: size_t,
                       compressed: *mut u8,
                       compressed_length: *mut size_t) -> c_int;
    fn snappy_uncompress(compressed: *const u8,
                         compressed_length: size_t,
                         uncompressed: *mut u8,
                         uncompressed_length: *mut size_t) -> c_int;
    fn snappy_max_compressed_length(source_length: size_t) -> size_t;
    fn snappy_uncompressed_length(compressed: *const u8,
                                  compressed_length: size_t,
                                  result: *mut size_t) -> c_int;
    /*fn snappy_validate_compressed_buffer(compressed: *const u8,
                                         compressed_length: size_t) -> c_int;*/
}

pub trait Message: Sized {
    fn encode(self) -> rmp::Value;
    fn decode(val: rmp::Value) -> Result<Self, Error>;

    fn to_bytes(self) -> Vec<u8> {
        let mut buf = io::Cursor::new(Vec::new());
        buf.write(&[0x00, 0x00, 0x00, 0x00]).expect("Failed to write dummy header");
        rmp::encode::value::write_value(&mut buf, &self.encode()).expect("Failed to write msgpack value to buffer");
        let mut buf = buf.into_inner();
        let mut size = buf.len() - 4;
        let mut encoding = 0;
        if size >= 100 {
            let mut compressed_size = unsafe { snappy_max_compressed_length(size) };
            let mut compressed = Vec::with_capacity(compressed_size + 4);
            unsafe {
                compressed.set_len(4);
                snappy_compress(buf[4..].as_ptr(), size, compressed[4..].as_mut_ptr(), &mut compressed_size);
                compressed.set_len(compressed_size+4);
            }
            if compressed_size < size {
                encoding = 1;
                buf = compressed;
                size = compressed_size;
            }
        }
        buf[0] = encoding;
        buf[1] = (size >> 16) as u8;
        buf[2] = (size >> 8) as u8;
        buf[3] = size as u8;
        buf
    }

    fn from_bytes(con: &Connection) -> Result<Self, Error> {
        let mut header = [0; 4];
        try!(con.read(&mut header).map_err(|err| match err {
            SslStreamError::ZeroReturn => Error::ConnectionEnded,
            SslStreamError::Stream(ref err) if err.kind() == io::ErrorKind::UnexpectedEof => Error::ConnectionEnded,
            SslStreamError::WantRead(_) | SslStreamError::WantWrite(_) => unreachable!(),
            _ => Error::NetworkError(NetworkError::ReadError)
        }));
        let mut size = ((header[1] as usize) << 16) + ((header[2] as usize) << 8) + (header[3] as usize);
        let mut body = Vec::with_capacity(size);
        unsafe { body.set_len(size) };
        try!(con.read(&mut body).map_err(|err| match err {
            SslStreamError::ZeroReturn => Error::ConnectionEnded,
            SslStreamError::Stream(ref err) if err.kind() == io::ErrorKind::UnexpectedEof => Error::ConnectionEnded,
            SslStreamError::WantRead(_) | SslStreamError::WantWrite(_) => unreachable!(),
            _ => Error::NetworkError(NetworkError::ReadError)
        }));
        match header[0] {
            0 => (),
            1 => {
                if unsafe { snappy_uncompressed_length(body.as_ptr(), body.len(), &mut size) } != 0 {
                    return Err(Error::FramingError(FramingError::InvalidCompressedData));
                }
                if size > 1<<24 {
                    return Err(Error::FramingError(FramingError::MessageTooLarge));
                }
                let mut raw = Vec::with_capacity(size);
                if unsafe { snappy_uncompress(body.as_ptr(), body.len(), raw.as_mut_ptr(), &mut size) } != 0 {
                    return Err(Error::FramingError(FramingError::InvalidCompressedData));
                }
                unsafe { raw.set_len(size) };
                body = raw;
            },
            _ => return Err(Error::FramingError(FramingError::UnknownEncoding))
        }
        let mut buf = Cursor::new(&mut body);
        let val = try!(rmp::decode::value::read_value(&mut buf).map_err(|_| Error::FramingError(FramingError::InvalidFormatedData)));
        Self::decode(val)
    }
}


#[derive(Debug)]
pub struct Request {
    pub id: u64,
    pub method: String,
    pub args: Vec<rmp::Value>,
    pub kwargs: HashMap<Cow<'static, str>, rmp::Value>
}

impl Message for Request {
    fn encode(mut self) -> rmp::Value {
        rmp::Value::Array(vec![
            rmp::Value::Integer(rmp::value::Integer::U64(self.id)),
            rmp::Value::String(self.method),
            rmp::Value::Array(self.args),
            rmp::Value::Map(self.kwargs.drain().map(|(k, v)| (rmp::Value::String(k.into_owned()), v)).collect())
        ])
    }

    fn decode(val: rmp::Value) -> Result<Self, Error> {
        let mut vec = match val {
            rmp::Value::Array(vec) => vec,
            _ => return Err(Error::MessageError(MessageErrorCode::InvalidBaseType, None))
        };
        if vec.len() != 4 {
            return Err(Error::MessageError(MessageErrorCode::InvalidBaseSize, None))
        }
        let kwargs = vec.remove(3);
        let args = vec.remove(2);
        let method = vec.remove(1);
        let id = vec.remove(0);
        let id = match id {
            rmp::Value::Integer(rmp::value::Integer::U64(id)) => id,
            _ => return Err(Error::MessageError(MessageErrorCode::InvalidIdType, None))
        };
        let method = match method {
            rmp::Value::String(method) => method,
            _ => return Err(Error::MessageError(MessageErrorCode::InvalidMethodType, Some(id)))
        };
        let args = match args {
            rmp::Value::Array(args) => args,
            _ => return Err(Error::MessageError(MessageErrorCode::InvalidArgsType, Some(id)))
        };
        let kwargs = match kwargs {
            rmp::Value::Map(pairs) => {
                let mut kwargs = HashMap::new();
                for (k, v) in pairs {
                    let k = match k {
                        rmp::Value::String(k) => k,
                        _ => return Err(Error::MessageError(MessageErrorCode::InvalidKwArgsKeyType, Some(id)))
                    };
                    kwargs.insert(Cow::Owned(k), v);
                }
                kwargs
            },
            _ => return Err(Error::MessageError(MessageErrorCode::InvalidKwArgsType, Some(id)))
        };
        Ok(Request{id: id, method: method, args: args, kwargs: kwargs})
    }
}

#[derive(Debug)]
pub enum Reply {
    Success(u64, rmp::Value), // Type 0
    Failure(u64, rmp::Value), // Type 1
    NoSuchMethod(u64, String), // Type 2
    RequestError(Option<u64>, MessageErrorCode) // Type 3
}

impl Message for Reply {
    fn encode(self) -> rmp::Value {
        match self {
            Reply::Success(id, val) => rmp::Value::Array(vec![
                rmp::Value::Integer(rmp::value::Integer::U64(id)),
                rmp::Value::Integer(rmp::value::Integer::U64(0)),
                val
            ]),
            Reply::Failure(id, val) => rmp::Value::Array(vec![
                rmp::Value::Integer(rmp::value::Integer::U64(id)),
                rmp::Value::Integer(rmp::value::Integer::U64(1)),
                val
            ]),
            Reply::NoSuchMethod(id, name) => rmp::Value::Array(vec![
                rmp::Value::Integer(rmp::value::Integer::U64(id)),
                rmp::Value::Integer(rmp::value::Integer::U64(2)),
                rmp::Value::String(name)
            ]),
            Reply::RequestError(id, kind) => rmp::Value::Array(vec![
                match id {
                    None => rmp::Value::Nil,
                    Some(id) => rmp::Value::Integer(rmp::value::Integer::U64(id))
                },
                rmp::Value::Integer(rmp::value::Integer::U64(3)),
                rmp::Value::Integer(rmp::value::Integer::U64(kind.to_code())),
            ]),
        }
    }

    fn decode(val: rmp::Value) -> Result<Reply, Error> {
        let mut vec = match val {
            rmp::Value::Array(vec) => vec,
            _ => return Err(Error::MessageError(MessageErrorCode::InvalidBaseType, None))
        };
        if vec.len() != 3 {
            return Err(Error::MessageError(MessageErrorCode::InvalidBaseSize, None))
        }
        let val = vec.remove(2);
        let type_ = vec.remove(1);
        let id = vec.remove(0);
        let id = match id {
            rmp::Value::Integer(rmp::value::Integer::U64(id)) => Some(id),
            rmp::Value::Nil => None,
            _ => return Err(Error::MessageError(MessageErrorCode::InvalidIdType, None))
        };
        let type_ = match type_ {
            rmp::Value::Integer(rmp::value::Integer::U64(type_)) => type_,
            _ => return Err(Error::MessageError(MessageErrorCode::InvalidReplyTypeType, id))
        };
        Ok(match type_ {
            0 => match id {
                Some(id) => Reply::Success(id, val),
                None => return Err(Error::MessageError(MessageErrorCode::InvalidIdType, id))
            },
            1 => match id {
                Some(id) => Reply::Failure(id, val),
                None => return Err(Error::MessageError(MessageErrorCode::InvalidIdType, id))
            },
            2 => match val {
                rmp::Value::String(name) => match id {
                    Some(id) => Reply::NoSuchMethod(id, name),
                    None => return Err(Error::MessageError(MessageErrorCode::InvalidIdType, id))
                },
                _ => return Err(Error::MessageError(MessageErrorCode::InvalidMethodType, id))
            },
            3 => match val {
                rmp::Value::Integer(rmp::value::Integer::U64(code)) => Reply::RequestError(id, MessageErrorCode::from_code(code)),
                _ => return Err(Error::MessageError(MessageErrorCode::InvalidErrorType, id))
            },
            _ => return Err(Error::MessageError(MessageErrorCode::UnknownReplyType, id))
        })
    }
}
