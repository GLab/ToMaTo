use rmp;

#[derive(Debug, PartialEq)]
pub enum NetworkError {
    Read,
    Write
}

#[derive(Debug, PartialEq)]
pub enum FramingError {
    UnknownEncoding,
    InvalidCompressedData,
    MessageTooLarge,
    InvalidFormatedData
}

#[derive(Debug, PartialEq)]
pub enum MessageErrorCode {
    UnknownError, // Code 0
    InvalidBaseType, // Code 1
    InvalidBaseSize, // Code 2
    InvalidIdType, // Code 3
    InvalidMethodType, // Code 4
    InvalidArgsType, // Code 5
    InvalidKwArgsType, // Code 6
    InvalidKwArgsKeyType, // Code 7
    InvalidReplyTypeType, // Code 8
    InvalidErrorType, // Code 9
    UnknownReplyType, // Code 10
}

impl MessageErrorCode {
    pub fn from_code(code: u64) -> Self {
        match code {
            1 => MessageErrorCode::InvalidBaseType,
            2 => MessageErrorCode::InvalidBaseSize,
            3 => MessageErrorCode::InvalidIdType,
            4 => MessageErrorCode::InvalidMethodType,
            5 => MessageErrorCode::InvalidArgsType,
            6 => MessageErrorCode::InvalidKwArgsType,
            7 => MessageErrorCode::InvalidKwArgsKeyType,
            8 => MessageErrorCode::InvalidReplyTypeType,
            9 => MessageErrorCode::InvalidErrorType,
            10 => MessageErrorCode::UnknownReplyType,
            0 | _ => MessageErrorCode::UnknownError
        }
    }

    pub fn to_code(&self) -> u64 {
        match *self {
            MessageErrorCode::UnknownError => 0,
            MessageErrorCode::InvalidBaseType => 1,
            MessageErrorCode::InvalidBaseSize => 2,
            MessageErrorCode::InvalidIdType => 3,
            MessageErrorCode::InvalidMethodType => 4,
            MessageErrorCode::InvalidArgsType => 5,
            MessageErrorCode::InvalidKwArgsType => 6,
            MessageErrorCode::InvalidKwArgsKeyType => 7,
            MessageErrorCode::InvalidReplyTypeType => 8,
            MessageErrorCode::InvalidErrorType => 9,
            MessageErrorCode::UnknownReplyType => 10
        }
    }
}

#[derive(Debug, PartialEq)]
pub enum Error {
    Failure(rmp::Value),
    NoSuchMethod(String),
    TimedOut,
    NetworkError(NetworkError), // errors in the connection (tcp or ssl)
    FramingError(FramingError), // errors in the message framing and encoding
    MessageError(MessageErrorCode, Option<u64>), // errors in the message contents
    ConnectionEnded
}
