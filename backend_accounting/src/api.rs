use std::sync::Arc;

use sslrpc2::{Params, Value};

use super::data::Data;

pub struct Api(Data);

impl Api {
    fn get_record(&self, params: Params) -> Result<Value, Value> {
        unimplemented!();
    }
}
