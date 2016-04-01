use std::mem;

use time;

pub type Time = i64;

#[inline]
pub fn now() -> Time {
    time::get_time().sec
}


pub struct Binary;

impl Binary {
    #[inline(always)]
    pub fn read_u16(data: &[u8]) -> u16 {
        ((data[0] as u16) << 8) | data[1] as u16
    }

    #[inline(always)]
    pub fn read_i16(data: &[u8]) -> i16 {
        unsafe { mem::transmute(Self::read_u16(data)) }
    }

    #[inline(always)]
    pub fn write_u16(val: u16, data: &mut [u8]) {
        data[0] = ((val >> 8) & 0xff) as u8;
        data[1] = (val & 0xff) as u8;
    }

    #[inline(always)]
    pub fn write_i16(val: i16, data: &mut [u8]) {
        Self::write_u16(unsafe { mem::transmute(val) }, data)
    }

    #[inline(always)]
    pub fn read_u32(data: &[u8]) -> u32 {
        ((data[0] as u32) << 24) | ((data[1] as u32) << 16) |
        ((data[2] as u32) << 8) | data[3] as u32
    }

    #[inline(always)]
    pub fn read_i32(data: &[u8]) -> i32 {
        unsafe { mem::transmute(Self::read_u32(data)) }
    }

    #[inline(always)]
    pub fn read_f32(data: &[u8]) -> f32 {
        unsafe { mem::transmute(Self::read_u32(data)) }
    }

    #[inline(always)]
    pub fn write_u32(val: u32, data: &mut [u8]) {
        data[0] = ((val >> 24) & 0xff) as u8;
        data[1] = ((val >> 16) & 0xff) as u8;
        data[2] = ((val >> 8) & 0xff) as u8;
        data[3] = (val & 0xff) as u8;
    }

    #[inline(always)]
    pub fn write_i32(val: i32, data: &mut [u8]) {
        Self::write_u32(unsafe { mem::transmute(val) }, data)
    }

    #[inline(always)]
    pub fn write_f32(val: f32, data: &mut [u8]) {
        Self::write_u32(unsafe { mem::transmute(val) }, data)
    }

    #[inline(always)]
    pub fn read_u64(data: &[u8]) -> u64 {
        ((data[0] as u64) << 56) | ((data[1] as u64) << 48) |
        ((data[2] as u64) << 40) | ((data[3] as u64) << 32) |
        ((data[4] as u64) << 24) | ((data[5] as u64) << 16) |
        ((data[6] as u64) << 8) | data[7] as u64
    }

    #[inline(always)]
    pub fn read_i64(data: &[u8]) -> i64 {
        unsafe { mem::transmute(Self::read_u64(data)) }
    }

    #[inline(always)]
    pub fn read_f64(data: &[u8]) -> f64 {
        unsafe { mem::transmute(Self::read_u64(data)) }
    }

    #[inline(always)]
    pub fn write_u64(val: u64, data: &mut [u8]) {
        data[0] = ((val >> 56) & 0xff) as u8;
        data[1] = ((val >> 48) & 0xff) as u8;
        data[2] = ((val >> 40) & 0xff) as u8;
        data[3] = ((val >> 32) & 0xff) as u8;
        data[4] = ((val >> 24) & 0xff) as u8;
        data[5] = ((val >> 16) & 0xff) as u8;
        data[6] = ((val >> 8) & 0xff) as u8;
        data[7] = (val & 0xff) as u8;
    }

    #[inline(always)]
    pub fn write_i64(val: i64, data: &mut [u8]) {
        Self::write_u64(unsafe { mem::transmute(val) }, data)
    }

    #[inline(always)]
    pub fn write_f64(val: f64, data: &mut [u8]) {
        Self::write_u64(unsafe { mem::transmute(val) }, data)
    }
}
