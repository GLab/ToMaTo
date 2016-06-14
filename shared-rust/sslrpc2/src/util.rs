use rmp::Value;
use rmp::value::{Integer, Float};

use std::i64;
use std::collections::HashMap;
use std::hash::Hash;
use std::mem;

pub struct ParseError;

pub trait ParseValue: Sized {
    fn parse(Value) -> Result<Self, ParseError>;
}

impl ParseValue for Value {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        Ok(val)
    }
}

impl ParseValue for () {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        match val {
            Value::Nil => Ok(()),
            _ => Err(ParseError)
        }
    }
}

impl ParseValue for bool {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        match val {
            Value::Boolean(v) => Ok(v),
            _ => Err(ParseError)
        }
    }
}

impl ParseValue for u64 {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        match val {
            Value::Integer(Integer::U64(val)) => Ok(val),
            Value::Integer(Integer::I64(val)) if val >= 0 => Ok(val as u64),
            Value::Float(Float::F64(val)) if val.trunc() == val => Ok(val.trunc() as u64),
            Value::Float(Float::F32(val)) if val.trunc() == val => Ok(val.trunc() as u64),
            _ => Err(ParseError)
        }
    }
}

impl ParseValue for u8 {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        Ok(try!(u64::parse(val)) as u8)
    }
}

impl ParseValue for u16 {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        Ok(try!(u64::parse(val)) as u16)
    }
}

impl ParseValue for u32 {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        Ok(try!(u64::parse(val)) as u32)
    }
}

impl ParseValue for usize {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        Ok(try!(u64::parse(val)) as usize)
    }
}

impl ParseValue for i64 {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        match val {
            Value::Integer(Integer::U64(val)) if val < i64::MAX as u64 => Ok(val as i64),
            Value::Integer(Integer::I64(val)) => Ok(val),
            Value::Float(Float::F64(val)) if val.trunc() == val => Ok(val.trunc() as i64),
            Value::Float(Float::F32(val)) if val.trunc() == val => Ok(val.trunc() as i64),
            _ => Err(ParseError)
        }
    }
}

impl ParseValue for i8 {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        Ok(try!(i64::parse(val)) as i8)
    }
}

impl ParseValue for i16 {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        Ok(try!(i64::parse(val)) as i16)
    }
}

impl ParseValue for i32 {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        Ok(try!(i64::parse(val)) as i32)
    }
}

impl ParseValue for isize {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        Ok(try!(i64::parse(val)) as isize)
    }
}

impl ParseValue for f64 {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        match val {
            Value::Integer(Integer::U64(val)) => Ok(val as f64),
            Value::Integer(Integer::I64(val)) => Ok(val as f64),
            Value::Float(Float::F64(val)) => Ok(val),
            Value::Float(Float::F32(val)) => Ok(val as f64),
            _ => Err(ParseError)
        }
    }
}

impl ParseValue for f32 {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        Ok(try!(f64::parse(val)) as f32)
    }
}

impl ParseValue for String {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        match val {
            Value::String(val) => Ok(val),
            _ => Err(ParseError)
        }
    }
}

impl<T> ParseValue for Vec<T> where T: ParseValue {
    fn parse(val: Value) -> Result<Self, ParseError> {
        match val {
            Value::Array(list) => {
                let mut res = Vec::with_capacity(list.len());
                for item in list {
                    res.push(try!(T::parse(item)));
                }
                Ok(res)
            },
            _ => Err(ParseError)
        }
    }
}

impl<T> ParseValue for Option<T> where T: ParseValue {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        match val {
            Value::Nil => Ok(None),
            val => Ok(Some(try!(T::parse(val))))
        }
    }
}

impl<K, V> ParseValue for HashMap<K, V> where K: ParseValue + Eq + Hash, V: ParseValue {
    #[inline]
    fn parse(val: Value) -> Result<Self, ParseError> {
        match val {
            Value::Map(list) => {
                let mut map = HashMap::new();
                for (k, v) in list {
                    map.insert(try!(K::parse(k)), try!(V::parse(v)));
                }
                Ok(map)
            },
            _ => Err(ParseError)
        }
    }
}

macro_rules! tuple_parse_value {
    ($($id:ident),+) => {
        impl<$($id : ParseValue),*> ParseValue for ($($id),*) {
            fn parse(val: Value) -> Result<Self, ParseError> {
                #![allow(unused_assignments)]
                #![allow(non_snake_case)]
                match val {
                    Value::Array(mut list) => {
                        let mut id = 0;
                        $(
                            let mut $id = Value::Nil;
                            mem::swap(&mut $id, &mut list[id]);
                            id += 1;
                        )*
                        Ok(( $(try!(ParseValue::parse($id))),+ ))
                    },
                    _ => Err(ParseError)
                }
            }
        }
    }
}

tuple_parse_value!(T1, T2);
tuple_parse_value!(T1, T2, T3);
tuple_parse_value!(T1, T2, T3, T4);
tuple_parse_value!(T1, T2, T3, T4, T5);
tuple_parse_value!(T1, T2, T3, T4, T5, T6);
tuple_parse_value!(T1, T2, T3, T4, T5, T6, T7);
tuple_parse_value!(T1, T2, T3, T4, T5, T6, T7, T8);



pub trait ToValue {
    fn to_value(self) -> Value;
}

impl ToValue for Value {
    #[inline]
    fn to_value(self) -> Value {
        self
    }
}

impl ToValue for () {
    #[inline]
    fn to_value(self) -> Value {
        Value::Nil
    }
}

impl ToValue for bool {
    #[inline]
    fn to_value(self) -> Value {
        Value::Boolean(self)
    }
}

impl ToValue for u64 {
    #[inline]
    fn to_value(self) -> Value {
        Value::Integer(Integer::U64(self))
    }
}

impl ToValue for u8 {
    #[inline]
    fn to_value(self) -> Value {
        u64::to_value(self as u64)
    }
}

impl ToValue for u16 {
    #[inline]
    fn to_value(self) -> Value {
        u64::to_value(self as u64)
    }
}

impl ToValue for u32 {
    #[inline]
    fn to_value(self) -> Value {
        u64::to_value(self as u64)
    }
}

impl ToValue for usize {
    #[inline]
    fn to_value(self) -> Value {
        u64::to_value(self as u64)
    }
}

impl ToValue for i64 {
    #[inline]
    fn to_value(self) -> Value {
        Value::Integer(Integer::I64(self))
    }
}

impl ToValue for i8 {
    #[inline]
    fn to_value(self) -> Value {
        i64::to_value(self as i64)
    }
}

impl ToValue for i16 {
    #[inline]
    fn to_value(self) -> Value {
        i64::to_value(self as i64)
    }
}

impl ToValue for i32 {
    #[inline]
    fn to_value(self) -> Value {
        i64::to_value(self as i64)
    }
}

impl ToValue for isize {
    #[inline]
    fn to_value(self) -> Value {
        i64::to_value(self as i64)
    }
}

impl ToValue for f32 {
    #[inline]
    fn to_value(self) -> Value {
        Value::Float(Float::F32(self))
    }
}

impl ToValue for f64 {
    #[inline]
    fn to_value(self) -> Value {
        Value::Float(Float::F64(self))
    }
}

impl ToValue for String {
    #[inline]
    fn to_value(self) -> Value {
        Value::String(self)
    }
}

impl ToValue for &'static str {
    #[inline]
    fn to_value(self) -> Value {
        Value::String(self.to_owned())
    }
}

impl<T> ToValue for Option<T> where T: ToValue {
    #[inline]
    fn to_value(self) -> Value {
        match self {
            Some(t) => t.to_value(),
            None => Value::Nil
        }
    }
}

impl<T> ToValue for Vec<T> where T: ToValue {
    fn to_value(self) -> Value {
        Value::Array(self.into_iter().map(|v| v.to_value()).collect())
    }
}

impl<K, V> ToValue for HashMap<K,V> where K: ToValue + Eq + Hash, V: ToValue {
    fn to_value(self) -> Value {
        Value::Map(self.into_iter().map(|(k, v)| (k.to_value(), v.to_value())).collect())
    }
}

macro_rules! tuple_to_value {
    ($($id:ident),+) => {
        impl<$($id : ToValue),*> ToValue for ($($id),*) {
            fn to_value(self) -> Value {
                #![allow(non_snake_case)]
                let ( $($id),+ ) = self;
                Value::Array(vec![$($id.to_value()),*])
            }
        }
    }
}

tuple_to_value!(T1, T2);
tuple_to_value!(T1, T2, T3);
tuple_to_value!(T1, T2, T3, T4);
tuple_to_value!(T1, T2, T3, T4, T5);
tuple_to_value!(T1, T2, T3, T4, T5, T6);
tuple_to_value!(T1, T2, T3, T4, T5, T6, T7);
tuple_to_value!(T1, T2, T3, T4, T5, T6, T7, T8);

#[macro_export]
macro_rules! to_value {
    ($val:expr) => {
        $val.to_value();
    };
    {$($name:expr => $val:expr),*} => {
        rmp::Value::Map(vec![
            $( ($name.to_value(), $val.to_value()), )*
        ])
    };
    [$($val:expr),*] => {
        rmp::Value::Array(vec![
            $( $val.to_value(), )*
        ])
    }
}
