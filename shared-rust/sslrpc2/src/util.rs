use rmp;

use std::i64;
use std::collections::HashMap;
use std::hash::Hash;
use std::mem;

pub struct ParseError;

pub trait ParseValue: Sized {
    fn parse(rmp::Value) -> Result<Self, ParseError>;
}

impl ParseValue for () {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        match val {
            rmp::Value::Nil => Ok(()),
            _ => Err(ParseError)
        }
    }
}

impl ParseValue for bool {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        match val {
            rmp::Value::Boolean(v) => Ok(v),
            _ => Err(ParseError)
        }
    }
}

impl ParseValue for u64 {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        match val {
            rmp::Value::Integer(rmp::value::Integer::U64(val)) => Ok(val),
            rmp::Value::Integer(rmp::value::Integer::I64(val)) if val >= 0 => Ok(val as u64),
            rmp::Value::Float(rmp::value::Float::F64(val)) if val.trunc() == val => Ok(val.trunc() as u64),
            rmp::Value::Float(rmp::value::Float::F32(val)) if val.trunc() == val => Ok(val.trunc() as u64),
            _ => Err(ParseError)
        }
    }
}

impl ParseValue for u8 {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        Ok(try!(u64::parse(val)) as u8)
    }
}

impl ParseValue for u16 {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        Ok(try!(u64::parse(val)) as u16)
    }
}

impl ParseValue for u32 {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        Ok(try!(u64::parse(val)) as u32)
    }
}

impl ParseValue for usize {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        Ok(try!(u64::parse(val)) as usize)
    }
}

impl ParseValue for i64 {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        match val {
            rmp::Value::Integer(rmp::value::Integer::U64(val)) if val < i64::MAX as u64 => Ok(val as i64),
            rmp::Value::Integer(rmp::value::Integer::I64(val)) => Ok(val),
            rmp::Value::Float(rmp::value::Float::F64(val)) if val.trunc() == val => Ok(val.trunc() as i64),
            rmp::Value::Float(rmp::value::Float::F32(val)) if val.trunc() == val => Ok(val.trunc() as i64),
            _ => Err(ParseError)
        }
    }
}

impl ParseValue for i8 {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        Ok(try!(i64::parse(val)) as i8)
    }
}

impl ParseValue for i16 {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        Ok(try!(i64::parse(val)) as i16)
    }
}

impl ParseValue for i32 {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        Ok(try!(i64::parse(val)) as i32)
    }
}

impl ParseValue for isize {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        Ok(try!(i64::parse(val)) as isize)
    }
}

impl ParseValue for f64 {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        match val {
            rmp::Value::Integer(rmp::value::Integer::U64(val)) => Ok(val as f64),
            rmp::Value::Integer(rmp::value::Integer::I64(val)) => Ok(val as f64),
            rmp::Value::Float(rmp::value::Float::F64(val)) => Ok(val),
            rmp::Value::Float(rmp::value::Float::F32(val)) => Ok(val as f64),
            _ => Err(ParseError)
        }
    }
}

impl ParseValue for f32 {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        Ok(try!(f64::parse(val)) as f32)
    }
}

impl ParseValue for String {
    #[inline(always)]
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        match val {
            rmp::Value::String(val) => Ok(val),
            _ => Err(ParseError)
        }
    }
}

impl<T> ParseValue for Vec<T> where T: ParseValue {
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        match val {
            rmp::Value::Array(list) => {
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
    fn parse(val: rmp::Value) -> Result<Self, ParseError> {
        match val {
            rmp::Value::Nil => Ok(None),
            val => Ok(Some(try!(T::parse(val))))
        }
    }
}

macro_rules! tuple_parse_value {
    ($($id:ident),+) => {
        impl<$($id : ParseValue),*> ParseValue for ($($id),*) {
            fn parse(val: rmp::Value) -> Result<Self, ParseError> {
                #![allow(unused_assignments)]
                #![allow(non_snake_case)]
                match val {
                    rmp::Value::Array(mut list) => {
                        let mut id = 0;
                        $(
                            let mut $id = rmp::Value::Nil;
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
    fn to_value(self) -> rmp::Value;
}

impl ToValue for () {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        rmp::Value::Nil
    }
}

impl ToValue for bool {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        rmp::Value::Boolean(self)
    }
}

impl ToValue for u64 {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        rmp::Value::Integer(rmp::value::Integer::U64(self))
    }
}

impl ToValue for u8 {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        u64::to_value(self as u64)
    }
}

impl ToValue for u16 {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        u64::to_value(self as u64)
    }
}

impl ToValue for u32 {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        u64::to_value(self as u64)
    }
}

impl ToValue for usize {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        u64::to_value(self as u64)
    }
}

impl ToValue for i64 {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        rmp::Value::Integer(rmp::value::Integer::I64(self))
    }
}

impl ToValue for i8 {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        i64::to_value(self as i64)
    }
}

impl ToValue for i16 {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        i64::to_value(self as i64)
    }
}

impl ToValue for i32 {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        i64::to_value(self as i64)
    }
}

impl ToValue for isize {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        i64::to_value(self as i64)
    }
}

impl ToValue for f32 {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        rmp::Value::Float(rmp::value::Float::F32(self))
    }
}

impl ToValue for f64 {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        rmp::Value::Float(rmp::value::Float::F64(self))
    }
}

impl ToValue for String {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        rmp::Value::String(self)
    }
}

impl ToValue for &'static str {
    #[inline(always)]
    fn to_value(self) -> rmp::Value {
        rmp::Value::String(self.to_owned())
    }
}

impl<T> ToValue for Option<T> where T: ToValue {
    #[inline]
    fn to_value(self) -> rmp::Value {
        match self {
            Some(t) => t.to_value(),
            None => rmp::Value::Nil
        }
    }
}

impl<T> ToValue for Vec<T> where T: ToValue {
    fn to_value(self) -> rmp::Value {
        rmp::Value::Array(self.into_iter().map(|v| v.to_value()).collect())
    }
}

impl<K, V> ToValue for HashMap<K,V> where K: ToValue + Eq + Hash, V: ToValue {
    fn to_value(self) -> rmp::Value {
        rmp::Value::Map(self.into_iter().map(|(k, v)| (k.to_value(), v.to_value())).collect())
    }
}

macro_rules! tuple_to_value {
    ($($id:ident),+) => {
        impl<$($id : ToValue),*> ToValue for ($($id),*) {
            fn to_value(self) -> rmp::Value {
                #![allow(non_snake_case)]
                let ( $($id),+ ) = self;
                rmp::Value::Array(vec![$($id.to_value()),*])
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
