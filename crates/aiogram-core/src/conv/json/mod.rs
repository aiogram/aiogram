//! The JSON codec: dict load ([`load`]), one-pass bytes load ([`parse`]), dict dump ([`dump`]),
//! bytes dump ([`write`]).
pub(crate) mod dump;
pub(crate) mod load;
pub(crate) mod parse;
pub(crate) mod write;
