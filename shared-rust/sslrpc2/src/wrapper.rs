use rmp;

use std::collections::HashMap;
use std::sync::Arc;
use std::borrow::Cow;

use super::server::Method as WrappedMethod;
use super::util::ToValue;

pub enum Error {
    TooManyArgs(usize, usize),
    DuplicateParam(&'static str)
}

impl ToValue for Error {
    fn to_value(self) -> rmp::Value {
        let mut err: Vec<(rmp::Value, rmp::Value)> = Vec::new();
        match self {
            Error::TooManyArgs(given, max) => {
                err.push(("type".to_value(), "user".to_value()));
                err.push(("code".to_value(), "too_many_args".to_value()));
                err.push(("message".to_value(), "too many arguments".to_value()));
                err.push(("data".to_value(), rmp::Value::Map(vec![
                    ("args_given".to_value(), given.to_value()),
                    ("args_max".to_value(), max.to_value())
                ])));
            },
            Error::DuplicateParam(name) => {
                err.push(("type".to_value(), "user".to_value()));
                err.push(("code".to_value(), "duplicate_param".to_value()));
                err.push(("message".to_value(), "duplicate parameter".to_value()));
                err.push(("data".to_value(), rmp::Value::Map(vec![
                    ("param_name".to_value(), name.to_value())
                ])));
            }
        }
        rmp::Value::Map(err)
    }
}

pub struct Params(HashMap<Cow<'static, str>, rmp::Value>);

impl Params {
    pub fn new(mut args: Vec<rmp::Value>, mut kwargs: HashMap<Cow<'static, str>, rmp::Value>, arg_names: &Vec<&'static str>) -> Result<Params, Error> {
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
