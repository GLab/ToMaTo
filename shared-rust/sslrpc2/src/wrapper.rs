use rmp;

use std::sync::Arc;
use std::borrow::Cow;

use super::server::Method as WrappedMethod;
use super::util::ToValue;
use super::msgs::{Args, KwArgs};

pub enum Error {
    TooManyArgs(usize, usize),
    DuplicateParam(&'static str)
}

impl ToValue for Error {
    fn to_value(self) -> rmp::Value {
        match self {
            Error::TooManyArgs(given, max) => to_value!{
                "type" => "user",
                "code" => "too_many_args",
                "message" => "too many arguments",
                "data" => to_value!{
                    "args_given" => given,
                    "args_max" => max
                }
            },
            Error::DuplicateParam(name) => to_value!{
                "type" => "user",
                "code" => "duplicate_param",
                "message" => "duplicate parameter",
                "data" => to_value!{
                    "param_name" => name
                }
            }
        }
    }
}

#[derive(Debug)]
pub struct Params(KwArgs);

impl Params {
    pub fn new(mut args: Args, mut kwargs: KwArgs, arg_names: &Vec<&'static str>) -> Result<Params, Error> {
        if args.len() > arg_names.len() {
            return Err(Error::TooManyArgs(args.len(), arg_names.len()));
        }
        let len = args.len();
        for i in 0..len {
            let name = arg_names[len-i-1];
            if kwargs.contains_key(name) {
                return Err(Error::DuplicateParam(name))
            }
            kwargs.insert(Cow::Borrowed(name), args.pop().unwrap());
        }
        Ok(Params(kwargs))
    }

    #[inline(always)]
    pub fn get(&self, name: &str) -> Option<&rmp::Value> {
        self.0.get(name)
    }

    #[inline(always)]
    pub fn take(&mut self, name: &str) -> Option<rmp::Value> {
        self.0.remove(name)
    }
}

pub type Method<R, E> = Box<Fn(Params) -> Result<R, E> + Sync + Send>;

pub fn wrap<R: ToValue + 'static, E: ToValue + 'static>(meth: Method<R, E>, arg_names: Vec<&'static str>) -> WrappedMethod {
    Arc::new(move |args, kwargs| {
        meth(try!(Params::new(args, kwargs, &arg_names).map_err(|e| e.to_value())))
        .map(|v| v.to_value()).map_err(|e| e.to_value())
    })
}
