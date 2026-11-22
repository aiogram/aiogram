//! Test types: hand-written the way B-04 writes and C-18 emits them, reduced to the fields
//! the tests use. Keys a table does not list are unknown keys; Message lists all 130 Bot API
//! fields (in `.butcher` order) and keeps the undecoded ones opaque in its sorted cold vec.
// fields no test reads are still part of each type's shape
#![allow(dead_code)]

use crate::decode::{
    ColdField, Cursor, Decode, DecodeResult, Field, IStr, Kind, Meta, Raw, Site, Table, Union,
    UnixTime, UnknownMember, WireEnum, cold_finish, cold_get, cold_set, required,
};

const fn f(wire: &'static str, kind: Kind, required: bool, cold: bool) -> Field {
    Field {
        wire,
        kind,
        required,
        cold,
    }
}

// ---- enums ----

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum ChatType {
    Channel,
    Group,
    Private,
    Supergroup,
    Unknown(Box<str>),
}

impl WireEnum for ChatType {
    const NAME: &'static str = "ChatType";
    const NAMES: &'static [&'static str] = &["channel", "group", "private", "supergroup"];
    const KNOWN: &'static [Self] = &[Self::Channel, Self::Group, Self::Private, Self::Supergroup];

    fn unknown(value: Box<str>) -> Self {
        Self::Unknown(value)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum EntityType {
    Bold,
    Code,
    Italic,
    Mention,
    TextLink,
    Url,
    Unknown(Box<str>),
}

impl WireEnum for EntityType {
    const NAME: &'static str = "MessageEntityType";
    const NAMES: &'static [&'static str] =
        &["bold", "code", "italic", "mention", "text_link", "url"];
    const KNOWN: &'static [Self] = &[
        Self::Bold,
        Self::Code,
        Self::Italic,
        Self::Mention,
        Self::TextLink,
        Self::Url,
    ];

    fn unknown(value: Box<str>) -> Self {
        Self::Unknown(value)
    }
}

// ---- User: boxed cold struct; `last_name` is left out (an unknown key) ----

#[derive(Debug)]
pub(crate) struct User {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) id: i64,
    pub(crate) is_bot: bool,
    pub(crate) first_name: Box<str>,
    pub(crate) username: Option<Box<str>>,
    pub(crate) language_code: Option<IStr>,
    pub(crate) cold: Option<Box<UserCold>>,
}

#[derive(Debug)]
pub(crate) struct UserCold {
    pub(crate) is_premium: Option<bool>,
    pub(crate) added_to_attachment_menu: Option<bool>,
}

#[derive(Default)]
pub(crate) struct UserPartial {
    id: Option<i64>,
    is_bot: Option<bool>,
    first_name: Option<Box<str>>,
    username: Option<Box<str>>,
    language_code: Option<IStr>,
    is_premium: Option<bool>,
    added_to_attachment_menu: Option<bool>,
}

pub(crate) static USER: Table = Table {
    fields: &[
        f("id", Kind::I64, true, false),
        f("is_bot", Kind::Bool, true, false),
        f("first_name", Kind::Str, true, false),
        f("username", Kind::Str, false, false),
        f("language_code", Kind::IStr, false, false),
        f("is_premium", Kind::Bool, false, true),
        f("added_to_attachment_menu", Kind::Bool, false, true),
    ],
    keys: &[
        ("added_to_attachment_menu", 6),
        ("first_name", 2),
        ("id", 0),
        ("is_bot", 1),
        ("is_premium", 5),
        ("language_code", 4),
        ("username", 3),
    ],
};

impl Decode for User {
    const TABLE: &'static Table = &USER;
    type Partial = UserPartial;
    type Bits = [u64; 1];

    fn set(p: &mut UserPartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => p.id = c.opt(Cursor::i64)?,
            1 => p.is_bot = c.opt(Cursor::bool)?,
            2 => p.first_name = c.opt(Cursor::str)?,
            3 => p.username = c.opt(Cursor::str)?,
            4 => p.language_code = c.opt(Cursor::istr)?,
            5 => p.is_premium = c.opt(Cursor::bool)?,
            _ => p.added_to_attachment_menu = c.opt(Cursor::bool)?,
        }
        Ok(())
    }

    fn finish(p: UserPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let id = required(p.id, "id", meta.span)?;
        let is_bot = required(p.is_bot, "is_bot", meta.span)?;
        let first_name = required(p.first_name, "first_name", meta.span)?;
        let cold = if p.is_premium.is_some() || p.added_to_attachment_menu.is_some() {
            Some(Box::new(UserCold {
                is_premium: p.is_premium,
                added_to_attachment_menu: p.added_to_attachment_menu,
            }))
        } else {
            None
        };
        Ok(Self {
            meta,
            id,
            is_bot,
            first_name,
            username: p.username,
            language_code: p.language_code,
            cold,
        })
    }
}

// ---- Chat: boxed cold struct, enum field ----

#[derive(Debug)]
pub(crate) struct Chat {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) id: i64,
    pub(crate) kind: ChatType,
    pub(crate) title: Option<Box<str>>,
    pub(crate) username: Option<Box<str>>,
    pub(crate) cold: Option<Box<ChatCold>>,
}

#[derive(Debug)]
pub(crate) struct ChatCold {
    pub(crate) is_forum: Option<bool>,
    pub(crate) first_name: Option<Box<str>>,
}

#[derive(Default)]
pub(crate) struct ChatPartial {
    id: Option<i64>,
    kind: Option<ChatType>,
    title: Option<Box<str>>,
    username: Option<Box<str>>,
    is_forum: Option<bool>,
    first_name: Option<Box<str>>,
}

pub(crate) static CHAT: Table = Table {
    fields: &[
        f("id", Kind::I64, true, false),
        f("type", Kind::Enum, true, false),
        f("title", Kind::Str, false, false),
        f("username", Kind::Str, false, false),
        f("is_forum", Kind::Bool, false, true),
        f("first_name", Kind::Str, false, true),
    ],
    keys: &[
        ("first_name", 5),
        ("id", 0),
        ("is_forum", 4),
        ("title", 2),
        ("type", 1),
        ("username", 3),
    ],
};

impl Decode for Chat {
    const TABLE: &'static Table = &CHAT;
    type Partial = ChatPartial;
    type Bits = [u64; 1];

    fn set(p: &mut ChatPartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => p.id = c.opt(Cursor::i64)?,
            1 => p.kind = c.opt(ChatType::read)?,
            2 => p.title = c.opt(Cursor::str)?,
            3 => p.username = c.opt(Cursor::str)?,
            4 => p.is_forum = c.opt(Cursor::bool)?,
            _ => p.first_name = c.opt(Cursor::str)?,
        }
        Ok(())
    }

    fn finish(p: ChatPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let id = required(p.id, "id", meta.span)?;
        let kind = required(p.kind, "type", meta.span)?;
        let cold = if p.is_forum.is_some() || p.first_name.is_some() {
            Some(Box::new(ChatCold {
                is_forum: p.is_forum,
                first_name: p.first_name,
            }))
        } else {
            None
        };
        Ok(Self {
            meta,
            id,
            kind,
            title: p.title,
            username: p.username,
            cold,
        })
    }
}

// ---- MessageEntity: i32 fields, enum with Unknown, boxed cold ----

#[derive(Debug)]
pub(crate) struct MessageEntity {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) kind: EntityType,
    pub(crate) offset: i32,
    pub(crate) length: i32,
    pub(crate) cold: Option<Box<MessageEntityCold>>,
}

#[derive(Debug)]
pub(crate) struct MessageEntityCold {
    pub(crate) url: Option<Box<str>>,
    pub(crate) language: Option<Box<str>>,
}

#[derive(Default)]
pub(crate) struct MessageEntityPartial {
    kind: Option<EntityType>,
    offset: Option<i32>,
    length: Option<i32>,
    url: Option<Box<str>>,
    language: Option<Box<str>>,
}

pub(crate) static MESSAGE_ENTITY: Table = Table {
    fields: &[
        f("type", Kind::Enum, true, false),
        f("offset", Kind::I32, true, false),
        f("length", Kind::I32, true, false),
        f("url", Kind::Str, false, true),
        f("language", Kind::Str, false, true),
    ],
    keys: &[
        ("language", 4),
        ("length", 2),
        ("offset", 1),
        ("type", 0),
        ("url", 3),
    ],
};

impl Decode for MessageEntity {
    const TABLE: &'static Table = &MESSAGE_ENTITY;
    type Partial = MessageEntityPartial;
    type Bits = [u64; 1];

    fn set(p: &mut MessageEntityPartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => p.kind = c.opt(EntityType::read)?,
            1 => p.offset = c.opt(Cursor::i32)?,
            2 => p.length = c.opt(Cursor::i32)?,
            3 => p.url = c.opt(Cursor::str)?,
            _ => p.language = c.opt(Cursor::str)?,
        }
        Ok(())
    }

    fn finish(p: MessageEntityPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let kind = required(p.kind, "type", meta.span)?;
        let offset = required(p.offset, "offset", meta.span)?;
        let length = required(p.length, "length", meta.span)?;
        let cold = if p.url.is_some() || p.language.is_some() {
            Some(Box::new(MessageEntityCold {
                url: p.url,
                language: p.language,
            }))
        } else {
            None
        };
        Ok(Self {
            meta,
            kind,
            offset,
            length,
            cold,
        })
    }
}

// ---- PhotoSize: hot only; `file_size` is left out (an unknown key) ----

#[derive(Debug)]
pub(crate) struct PhotoSize {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) file_id: Box<str>,
    pub(crate) file_unique_id: Box<str>,
    pub(crate) width: i32,
    pub(crate) height: i32,
}

#[derive(Default)]
pub(crate) struct PhotoSizePartial {
    file_id: Option<Box<str>>,
    file_unique_id: Option<Box<str>>,
    width: Option<i32>,
    height: Option<i32>,
}

pub(crate) static PHOTO_SIZE: Table = Table {
    fields: &[
        f("file_id", Kind::Str, true, false),
        f("file_unique_id", Kind::Str, true, false),
        f("width", Kind::I32, true, false),
        f("height", Kind::I32, true, false),
    ],
    keys: &[
        ("file_id", 0),
        ("file_unique_id", 1),
        ("height", 3),
        ("width", 2),
    ],
};

impl Decode for PhotoSize {
    const TABLE: &'static Table = &PHOTO_SIZE;
    type Partial = PhotoSizePartial;
    type Bits = [u64; 1];

    fn set(p: &mut PhotoSizePartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => p.file_id = c.opt(Cursor::str)?,
            1 => p.file_unique_id = c.opt(Cursor::str)?,
            2 => p.width = c.opt(Cursor::i32)?,
            _ => p.height = c.opt(Cursor::i32)?,
        }
        Ok(())
    }

    fn finish(p: PhotoSizePartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let file_id = required(p.file_id, "file_id", meta.span)?;
        let file_unique_id = required(p.file_unique_id, "file_unique_id", meta.span)?;
        let width = required(p.width, "width", meta.span)?;
        let height = required(p.height, "height", meta.span)?;
        Ok(Self {
            meta,
            file_id,
            file_unique_id,
            width,
            height,
        })
    }
}

// ---- TextQuote ----

#[derive(Debug)]
pub(crate) struct TextQuote {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) text: Box<str>,
    pub(crate) entities: Option<Box<[MessageEntity]>>,
    pub(crate) position: i32,
    pub(crate) is_manual: Option<bool>,
}

#[derive(Default)]
pub(crate) struct TextQuotePartial {
    text: Option<Box<str>>,
    entities: Option<Box<[MessageEntity]>>,
    position: Option<i32>,
    is_manual: Option<bool>,
}

pub(crate) static TEXT_QUOTE: Table = Table {
    fields: &[
        f("text", Kind::Str, true, false),
        f("entities", Kind::Array, false, false),
        f("position", Kind::I32, true, false),
        f("is_manual", Kind::Bool, false, false),
    ],
    keys: &[
        ("entities", 1),
        ("is_manual", 3),
        ("position", 2),
        ("text", 0),
    ],
};

impl Decode for TextQuote {
    const TABLE: &'static Table = &TEXT_QUOTE;
    type Partial = TextQuotePartial;
    type Bits = [u64; 1];

    fn set(p: &mut TextQuotePartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => p.text = c.opt(Cursor::str)?,
            1 => p.entities = c.opt(|c| c.list(MessageEntity::decode))?,
            2 => p.position = c.opt(Cursor::i32)?,
            _ => p.is_manual = c.opt(Cursor::bool)?,
        }
        Ok(())
    }

    fn finish(p: TextQuotePartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let text = required(p.text, "text", meta.span)?;
        let position = required(p.position, "position", meta.span)?;
        Ok(Self {
            meta,
            text,
            entities: p.entities,
            position,
            is_manual: p.is_manual,
        })
    }
}

// ---- Location: f64 ----

#[derive(Debug)]
pub(crate) struct Location {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) latitude: f64,
    pub(crate) longitude: f64,
    pub(crate) horizontal_accuracy: Option<f64>,
}

#[derive(Default)]
pub(crate) struct LocationPartial {
    latitude: Option<f64>,
    longitude: Option<f64>,
    horizontal_accuracy: Option<f64>,
}

pub(crate) static LOCATION: Table = Table {
    fields: &[
        f("latitude", Kind::F64, true, false),
        f("longitude", Kind::F64, true, false),
        f("horizontal_accuracy", Kind::F64, false, false),
    ],
    keys: &[
        ("horizontal_accuracy", 2),
        ("latitude", 0),
        ("longitude", 1),
    ],
};

impl Decode for Location {
    const TABLE: &'static Table = &LOCATION;
    type Partial = LocationPartial;
    type Bits = [u64; 1];

    fn set(p: &mut LocationPartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => p.latitude = c.opt(Cursor::f64)?,
            1 => p.longitude = c.opt(Cursor::f64)?,
            _ => p.horizontal_accuracy = c.opt(Cursor::f64)?,
        }
        Ok(())
    }

    fn finish(p: LocationPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let latitude = required(p.latitude, "latitude", meta.span)?;
        let longitude = required(p.longitude, "longitude", meta.span)?;
        Ok(Self {
            meta,
            latitude,
            longitude,
            horizontal_accuracy: p.horizontal_accuracy,
        })
    }
}

// ---- InlineKeyboardMarkup: nested arrays ----

#[derive(Debug)]
pub(crate) struct InlineKeyboardButton {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) text: Box<str>,
    pub(crate) url: Option<Box<str>>,
    pub(crate) callback_data: Option<Box<str>>,
}

#[derive(Default)]
pub(crate) struct InlineKeyboardButtonPartial {
    text: Option<Box<str>>,
    url: Option<Box<str>>,
    callback_data: Option<Box<str>>,
}

pub(crate) static INLINE_KEYBOARD_BUTTON: Table = Table {
    fields: &[
        f("text", Kind::Str, true, false),
        f("url", Kind::Str, false, false),
        f("callback_data", Kind::Str, false, false),
    ],
    keys: &[("callback_data", 2), ("text", 0), ("url", 1)],
};

impl Decode for InlineKeyboardButton {
    const TABLE: &'static Table = &INLINE_KEYBOARD_BUTTON;
    type Partial = InlineKeyboardButtonPartial;
    type Bits = [u64; 1];

    fn set(p: &mut InlineKeyboardButtonPartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => p.text = c.opt(Cursor::str)?,
            1 => p.url = c.opt(Cursor::str)?,
            _ => p.callback_data = c.opt(Cursor::str)?,
        }
        Ok(())
    }

    fn finish(p: InlineKeyboardButtonPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let text = required(p.text, "text", meta.span)?;
        Ok(Self {
            meta,
            text,
            url: p.url,
            callback_data: p.callback_data,
        })
    }
}

#[derive(Debug)]
pub(crate) struct InlineKeyboardMarkup {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) inline_keyboard: Box<[Box<[InlineKeyboardButton]>]>,
}

#[derive(Default)]
pub(crate) struct InlineKeyboardMarkupPartial {
    inline_keyboard: Option<Box<[Box<[InlineKeyboardButton]>]>>,
}

pub(crate) static INLINE_KEYBOARD_MARKUP: Table = Table {
    fields: &[f("inline_keyboard", Kind::Array, true, false)],
    keys: &[("inline_keyboard", 0)],
};

impl Decode for InlineKeyboardMarkup {
    const TABLE: &'static Table = &INLINE_KEYBOARD_MARKUP;
    type Partial = InlineKeyboardMarkupPartial;
    type Bits = [u64; 1];

    fn set(p: &mut InlineKeyboardMarkupPartial, _id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        p.inline_keyboard = c.opt(|c| c.list(|c| c.list(InlineKeyboardButton::decode)))?;
        Ok(())
    }

    fn finish(p: InlineKeyboardMarkupPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let inline_keyboard = required(p.inline_keyboard, "inline_keyboard", meta.span)?;
        Ok(Self {
            meta,
            inline_keyboard,
        })
    }
}

// ---- Message: hot fields inline, every other field in a sorted cold vec ----

/// Field ids of Message (`.butcher` order).
pub(crate) mod m {
    pub(crate) const MESSAGE_ID: u16 = 0;
    pub(crate) const DATE: u16 = 1;
    pub(crate) const CHAT: u16 = 2;
    pub(crate) const MESSAGE_THREAD_ID: u16 = 3;
    pub(crate) const FROM: u16 = 5;
    pub(crate) const REPLY_TO_MESSAGE: u16 = 15;
    pub(crate) const TEXT: u16 = 31;
    pub(crate) const ENTITIES: u16 = 32;
    pub(crate) const PHOTO: u16 = 41;
    pub(crate) const CAPTION: u16 = 47;
    pub(crate) const CAPTION_ENTITIES: u16 = 48;
    pub(crate) const REPLY_MARKUP: u16 = 113;
    pub(crate) const SENDER_BOOST_COUNT: u16 = 7;
    pub(crate) const SENDER_BUSINESS_BOT: u16 = 8;
    pub(crate) const SENDER_TAG: u16 = 9;
    pub(crate) const BUSINESS_CONNECTION_ID: u16 = 11;
    pub(crate) const IS_TOPIC_MESSAGE: u16 = 13;
    pub(crate) const IS_AUTOMATIC_FORWARD: u16 = 14;
    pub(crate) const QUOTE: u16 = 17;
    pub(crate) const REPLY_TO_CHECKLIST_TASK_ID: u16 = 19;
    pub(crate) const VIA_BOT: u16 = 21;
    pub(crate) const EDIT_DATE: u16 = 24;
    pub(crate) const HAS_PROTECTED_CONTENT: u16 = 25;
    pub(crate) const IS_FROM_OFFLINE: u16 = 26;
    pub(crate) const IS_PAID_POST: u16 = 27;
    pub(crate) const MEDIA_GROUP_ID: u16 = 28;
    pub(crate) const AUTHOR_SIGNATURE: u16 = 29;
    pub(crate) const PAID_STAR_COUNT: u16 = 30;
    pub(crate) const EFFECT_ID: u16 = 35;
    pub(crate) const SHOW_CAPTION_ABOVE_MEDIA: u16 = 49;
    pub(crate) const HAS_MEDIA_SPOILER: u16 = 50;
    pub(crate) const LOCATION: u16 = 57;
    pub(crate) const FORWARD_ORIGIN: u16 = 12;
    pub(crate) const PINNED_MESSAGE: u16 = 71;
    // opaque fields the tests use
    pub(crate) const ANIMATION: u16 = 36;
    pub(crate) const STICKER: u16 = 42;
    pub(crate) const GIVEAWAY: u16 = 96;
    pub(crate) const TON_WALLET_TRANSFER: u16 = 122;
    pub(crate) const FORWARD_DATE: u16 = 123;
}

#[derive(Debug)]
pub(crate) struct Message {
    pub(crate) meta: Meta<[u64; 3]>,
    pub(crate) message_id: i64,
    pub(crate) date: UnixTime,
    pub(crate) chat: Chat,
    pub(crate) message_thread_id: Option<i64>,
    pub(crate) from_user: Option<User>,
    pub(crate) reply_to_message: Option<Box<Message>>,
    pub(crate) text: Option<Box<str>>,
    pub(crate) entities: Option<Box<[MessageEntity]>>,
    pub(crate) photo: Option<Box<[PhotoSize]>>,
    pub(crate) caption: Option<Box<str>>,
    pub(crate) caption_entities: Option<Box<[MessageEntity]>>,
    pub(crate) reply_markup: Option<InlineKeyboardMarkup>,
    /// sorted by field id
    pub(crate) cold: Box<[MessageCold]>,
}

#[derive(Debug)]
pub(crate) enum MessageCold {
    SenderBoostCount(i64),
    SenderBusinessBot(User),
    SenderTag(Box<str>),
    BusinessConnectionId(Box<str>),
    IsTopicMessage(bool),
    IsAutomaticForward(bool),
    Quote(TextQuote),
    ReplyToChecklistTaskId(i64),
    ViaBot(User),
    EditDate(UnixTime),
    HasProtectedContent(bool),
    IsFromOffline(bool),
    IsPaidPost(bool),
    MediaGroupId(Box<str>),
    AuthorSignature(Box<str>),
    PaidStarCount(i64),
    EffectId(Box<str>),
    ShowCaptionAboveMedia(bool),
    HasMediaSpoiler(bool),
    Location(Location),
    ForwardOrigin(MessageOrigin),
    PinnedMessage(MaybeInaccessibleMessage),
    /// a field outside the decoded set, by id
    Opaque(u16, Raw),
}

impl ColdField for MessageCold {
    fn id(&self) -> u16 {
        match self {
            Self::SenderBoostCount(_) => m::SENDER_BOOST_COUNT,
            Self::SenderBusinessBot(_) => m::SENDER_BUSINESS_BOT,
            Self::SenderTag(_) => m::SENDER_TAG,
            Self::BusinessConnectionId(_) => m::BUSINESS_CONNECTION_ID,
            Self::IsTopicMessage(_) => m::IS_TOPIC_MESSAGE,
            Self::IsAutomaticForward(_) => m::IS_AUTOMATIC_FORWARD,
            Self::Quote(_) => m::QUOTE,
            Self::ReplyToChecklistTaskId(_) => m::REPLY_TO_CHECKLIST_TASK_ID,
            Self::ViaBot(_) => m::VIA_BOT,
            Self::EditDate(_) => m::EDIT_DATE,
            Self::HasProtectedContent(_) => m::HAS_PROTECTED_CONTENT,
            Self::IsFromOffline(_) => m::IS_FROM_OFFLINE,
            Self::IsPaidPost(_) => m::IS_PAID_POST,
            Self::MediaGroupId(_) => m::MEDIA_GROUP_ID,
            Self::AuthorSignature(_) => m::AUTHOR_SIGNATURE,
            Self::PaidStarCount(_) => m::PAID_STAR_COUNT,
            Self::EffectId(_) => m::EFFECT_ID,
            Self::ShowCaptionAboveMedia(_) => m::SHOW_CAPTION_ABOVE_MEDIA,
            Self::HasMediaSpoiler(_) => m::HAS_MEDIA_SPOILER,
            Self::Location(_) => m::LOCATION,
            Self::ForwardOrigin(_) => m::FORWARD_ORIGIN,
            Self::PinnedMessage(_) => m::PINNED_MESSAGE,
            Self::Opaque(id, _) => *id,
        }
    }
}

impl Message {
    pub(crate) fn cold(&self, id: u16) -> Option<&MessageCold> {
        cold_get(&self.cold, id)
    }

    pub(crate) fn edit_date(&self) -> Option<UnixTime> {
        match self.cold(m::EDIT_DATE)? {
            MessageCold::EditDate(value) => Some(*value),
            _ => None,
        }
    }

    pub(crate) fn via_bot(&self) -> Option<&User> {
        match self.cold(m::VIA_BOT)? {
            MessageCold::ViaBot(value) => Some(value),
            _ => None,
        }
    }

    pub(crate) fn forward_origin(&self) -> Option<&MessageOrigin> {
        match self.cold(m::FORWARD_ORIGIN)? {
            MessageCold::ForwardOrigin(value) => Some(value),
            _ => None,
        }
    }

    pub(crate) fn pinned_message(&self) -> Option<&MaybeInaccessibleMessage> {
        match self.cold(m::PINNED_MESSAGE)? {
            MessageCold::PinnedMessage(value) => Some(value),
            _ => None,
        }
    }

    /// The raw range of an opaque field.
    pub(crate) fn opaque(&self, id: u16) -> Option<Raw> {
        match self.cold(id)? {
            MessageCold::Opaque(_, raw) => Some(*raw),
            _ => None,
        }
    }
}

#[derive(Default)]
pub(crate) struct MessagePartial {
    message_id: Option<i64>,
    date: Option<UnixTime>,
    chat: Option<Chat>,
    message_thread_id: Option<i64>,
    from_user: Option<User>,
    reply_to_message: Option<Box<Message>>,
    text: Option<Box<str>>,
    entities: Option<Box<[MessageEntity]>>,
    photo: Option<Box<[PhotoSize]>>,
    caption: Option<Box<str>>,
    caption_entities: Option<Box<[MessageEntity]>>,
    reply_markup: Option<InlineKeyboardMarkup>,
    cold: Vec<MessageCold>,
}

pub(crate) static MESSAGE: Table = Table {
    fields: &[
        f("message_id", Kind::I64, true, false),
        f("date", Kind::UnixTime, true, false),
        f("chat", Kind::Object, true, false),
        f("message_thread_id", Kind::I64, false, false),
        f("direct_messages_topic", Kind::Opaque, false, true),
        f("from", Kind::Object, false, false),
        f("sender_chat", Kind::Opaque, false, true),
        f("sender_boost_count", Kind::I64, false, true),
        f("sender_business_bot", Kind::Object, false, true),
        f("sender_tag", Kind::Str, false, true),
        f("guest_query_id", Kind::Opaque, false, true),
        f("business_connection_id", Kind::Str, false, true),
        f("forward_origin", Kind::Object, false, true),
        f("is_topic_message", Kind::Bool, false, true),
        f("is_automatic_forward", Kind::Bool, false, true),
        f("reply_to_message", Kind::Object, false, false),
        f("external_reply", Kind::Opaque, false, true),
        f("quote", Kind::Object, false, true),
        f("reply_to_story", Kind::Opaque, false, true),
        f("reply_to_checklist_task_id", Kind::I64, false, true),
        f("reply_to_poll_option_id", Kind::Opaque, false, true),
        f("via_bot", Kind::Object, false, true),
        f("guest_bot_caller_user", Kind::Opaque, false, true),
        f("guest_bot_caller_chat", Kind::Opaque, false, true),
        f("edit_date", Kind::UnixTime, false, true),
        f("has_protected_content", Kind::Bool, false, true),
        f("is_from_offline", Kind::Bool, false, true),
        f("is_paid_post", Kind::Bool, false, true),
        f("media_group_id", Kind::Str, false, true),
        f("author_signature", Kind::Str, false, true),
        f("paid_star_count", Kind::I64, false, true),
        f("text", Kind::Str, false, false),
        f("entities", Kind::Array, false, false),
        f("link_preview_options", Kind::Opaque, false, true),
        f("suggested_post_info", Kind::Opaque, false, true),
        f("effect_id", Kind::Str, false, true),
        f("animation", Kind::Opaque, false, true),
        f("audio", Kind::Opaque, false, true),
        f("document", Kind::Opaque, false, true),
        f("live_photo", Kind::Opaque, false, true),
        f("paid_media", Kind::Opaque, false, true),
        f("photo", Kind::Array, false, false),
        f("sticker", Kind::Opaque, false, true),
        f("story", Kind::Opaque, false, true),
        f("video", Kind::Opaque, false, true),
        f("video_note", Kind::Opaque, false, true),
        f("voice", Kind::Opaque, false, true),
        f("caption", Kind::Str, false, false),
        f("caption_entities", Kind::Array, false, false),
        f("show_caption_above_media", Kind::Bool, false, true),
        f("has_media_spoiler", Kind::Bool, false, true),
        f("checklist", Kind::Opaque, false, true),
        f("contact", Kind::Opaque, false, true),
        f("dice", Kind::Opaque, false, true),
        f("game", Kind::Opaque, false, true),
        f("poll", Kind::Opaque, false, true),
        f("venue", Kind::Opaque, false, true),
        f("location", Kind::Object, false, true),
        f("new_chat_members", Kind::Opaque, false, true),
        f("left_chat_member", Kind::Opaque, false, true),
        f("chat_owner_left", Kind::Opaque, false, true),
        f("chat_owner_changed", Kind::Opaque, false, true),
        f("new_chat_title", Kind::Opaque, false, true),
        f("new_chat_photo", Kind::Opaque, false, true),
        f("delete_chat_photo", Kind::Opaque, false, true),
        f("group_chat_created", Kind::Opaque, false, true),
        f("supergroup_chat_created", Kind::Opaque, false, true),
        f("channel_chat_created", Kind::Opaque, false, true),
        f(
            "message_auto_delete_timer_changed",
            Kind::Opaque,
            false,
            true,
        ),
        f("migrate_to_chat_id", Kind::Opaque, false, true),
        f("migrate_from_chat_id", Kind::Opaque, false, true),
        f("pinned_message", Kind::Object, false, true),
        f("invoice", Kind::Opaque, false, true),
        f("successful_payment", Kind::Opaque, false, true),
        f("refunded_payment", Kind::Opaque, false, true),
        f("users_shared", Kind::Opaque, false, true),
        f("chat_shared", Kind::Opaque, false, true),
        f("gift", Kind::Opaque, false, true),
        f("unique_gift", Kind::Opaque, false, true),
        f("gift_upgrade_sent", Kind::Opaque, false, true),
        f("connected_website", Kind::Opaque, false, true),
        f("write_access_allowed", Kind::Opaque, false, true),
        f("passport_data", Kind::Opaque, false, true),
        f("proximity_alert_triggered", Kind::Opaque, false, true),
        f("boost_added", Kind::Opaque, false, true),
        f("chat_background_set", Kind::Opaque, false, true),
        f("checklist_tasks_done", Kind::Opaque, false, true),
        f("checklist_tasks_added", Kind::Opaque, false, true),
        f("direct_message_price_changed", Kind::Opaque, false, true),
        f("forum_topic_created", Kind::Opaque, false, true),
        f("forum_topic_edited", Kind::Opaque, false, true),
        f("forum_topic_closed", Kind::Opaque, false, true),
        f("forum_topic_reopened", Kind::Opaque, false, true),
        f("general_forum_topic_hidden", Kind::Opaque, false, true),
        f("general_forum_topic_unhidden", Kind::Opaque, false, true),
        f("giveaway_created", Kind::Opaque, false, true),
        f("giveaway", Kind::Opaque, false, true),
        f("giveaway_winners", Kind::Opaque, false, true),
        f("giveaway_completed", Kind::Opaque, false, true),
        f("managed_bot_created", Kind::Opaque, false, true),
        f("paid_message_price_changed", Kind::Opaque, false, true),
        f("poll_option_added", Kind::Opaque, false, true),
        f("poll_option_deleted", Kind::Opaque, false, true),
        f("suggested_post_approved", Kind::Opaque, false, true),
        f("suggested_post_approval_failed", Kind::Opaque, false, true),
        f("suggested_post_declined", Kind::Opaque, false, true),
        f("suggested_post_paid", Kind::Opaque, false, true),
        f("suggested_post_refunded", Kind::Opaque, false, true),
        f("video_chat_scheduled", Kind::Opaque, false, true),
        f("video_chat_started", Kind::Opaque, false, true),
        f("video_chat_ended", Kind::Opaque, false, true),
        f("video_chat_participants_invited", Kind::Opaque, false, true),
        f("web_app_data", Kind::Opaque, false, true),
        f("reply_markup", Kind::Object, false, false),
        f("rich_message", Kind::Opaque, false, true),
        f("receiver_user", Kind::Opaque, false, true),
        f("ephemeral_message_id", Kind::Opaque, false, true),
        f("community_chat_added", Kind::Opaque, false, true),
        f("community_chat_removed", Kind::Opaque, false, true),
        f("community_chat_joined", Kind::Opaque, false, true),
        f("widget", Kind::Opaque, false, true),
        f("paid_messages_waived", Kind::Opaque, false, true),
        f("ton_wallet_transfer", Kind::Opaque, false, true),
        f("forward_date", Kind::Opaque, false, true),
        f("forward_from", Kind::Opaque, false, true),
        f("forward_from_chat", Kind::Opaque, false, true),
        f("forward_from_message_id", Kind::Opaque, false, true),
        f("forward_sender_name", Kind::Opaque, false, true),
        f("forward_signature", Kind::Opaque, false, true),
        f("user_shared", Kind::Opaque, false, true),
    ],
    keys: &[
        ("animation", 36),
        ("audio", 37),
        ("author_signature", 29),
        ("boost_added", 84),
        ("business_connection_id", 11),
        ("caption", 47),
        ("caption_entities", 48),
        ("channel_chat_created", 67),
        ("chat", 2),
        ("chat_background_set", 85),
        ("chat_owner_changed", 61),
        ("chat_owner_left", 60),
        ("chat_shared", 76),
        ("checklist", 51),
        ("checklist_tasks_added", 87),
        ("checklist_tasks_done", 86),
        ("community_chat_added", 117),
        ("community_chat_joined", 119),
        ("community_chat_removed", 118),
        ("connected_website", 80),
        ("contact", 52),
        ("date", 1),
        ("delete_chat_photo", 64),
        ("dice", 53),
        ("direct_message_price_changed", 88),
        ("direct_messages_topic", 4),
        ("document", 38),
        ("edit_date", 24),
        ("effect_id", 35),
        ("entities", 32),
        ("ephemeral_message_id", 116),
        ("external_reply", 16),
        ("forum_topic_closed", 91),
        ("forum_topic_created", 89),
        ("forum_topic_edited", 90),
        ("forum_topic_reopened", 92),
        ("forward_date", 123),
        ("forward_from", 124),
        ("forward_from_chat", 125),
        ("forward_from_message_id", 126),
        ("forward_origin", 12),
        ("forward_sender_name", 127),
        ("forward_signature", 128),
        ("from", 5),
        ("from_user", 5),
        ("game", 54),
        ("general_forum_topic_hidden", 93),
        ("general_forum_topic_unhidden", 94),
        ("gift", 77),
        ("gift_upgrade_sent", 79),
        ("giveaway", 96),
        ("giveaway_completed", 98),
        ("giveaway_created", 95),
        ("giveaway_winners", 97),
        ("group_chat_created", 65),
        ("guest_bot_caller_chat", 23),
        ("guest_bot_caller_user", 22),
        ("guest_query_id", 10),
        ("has_media_spoiler", 50),
        ("has_protected_content", 25),
        ("invoice", 72),
        ("is_automatic_forward", 14),
        ("is_from_offline", 26),
        ("is_paid_post", 27),
        ("is_topic_message", 13),
        ("left_chat_member", 59),
        ("link_preview_options", 33),
        ("live_photo", 39),
        ("location", 57),
        ("managed_bot_created", 99),
        ("media_group_id", 28),
        ("message_auto_delete_timer_changed", 68),
        ("message_id", 0),
        ("message_thread_id", 3),
        ("migrate_from_chat_id", 70),
        ("migrate_to_chat_id", 69),
        ("new_chat_members", 58),
        ("new_chat_photo", 63),
        ("new_chat_title", 62),
        ("paid_media", 40),
        ("paid_message_price_changed", 100),
        ("paid_messages_waived", 121),
        ("paid_star_count", 30),
        ("passport_data", 82),
        ("photo", 41),
        ("pinned_message", 71),
        ("poll", 55),
        ("poll_option_added", 101),
        ("poll_option_deleted", 102),
        ("proximity_alert_triggered", 83),
        ("quote", 17),
        ("receiver_user", 115),
        ("refunded_payment", 74),
        ("reply_markup", 113),
        ("reply_to_checklist_task_id", 19),
        ("reply_to_message", 15),
        ("reply_to_poll_option_id", 20),
        ("reply_to_story", 18),
        ("rich_message", 114),
        ("sender_boost_count", 7),
        ("sender_business_bot", 8),
        ("sender_chat", 6),
        ("sender_tag", 9),
        ("show_caption_above_media", 49),
        ("sticker", 42),
        ("story", 43),
        ("successful_payment", 73),
        ("suggested_post_approval_failed", 104),
        ("suggested_post_approved", 103),
        ("suggested_post_declined", 105),
        ("suggested_post_info", 34),
        ("suggested_post_paid", 106),
        ("suggested_post_refunded", 107),
        ("supergroup_chat_created", 66),
        ("text", 31),
        ("ton_wallet_transfer", 122),
        ("unique_gift", 78),
        ("user_shared", 129),
        ("users_shared", 75),
        ("venue", 56),
        ("via_bot", 21),
        ("video", 44),
        ("video_chat_ended", 110),
        ("video_chat_participants_invited", 111),
        ("video_chat_scheduled", 108),
        ("video_chat_started", 109),
        ("video_note", 45),
        ("voice", 46),
        ("web_app_data", 112),
        ("widget", 120),
        ("write_access_allowed", 81),
    ],
};

impl Decode for Message {
    const TABLE: &'static Table = &MESSAGE;
    type Partial = MessagePartial;
    type Bits = [u64; 3];

    fn set(p: &mut MessagePartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        use MessageCold as C;
        let cold = &mut p.cold;
        match id {
            m::MESSAGE_ID => p.message_id = c.opt(Cursor::i64)?,
            m::DATE => p.date = c.opt(Cursor::time)?,
            m::CHAT => p.chat = c.opt(Chat::decode)?,
            m::MESSAGE_THREAD_ID => p.message_thread_id = c.opt(Cursor::i64)?,
            m::FROM => p.from_user = c.opt(User::decode)?,
            m::REPLY_TO_MESSAGE => {
                p.reply_to_message = c.opt(|c| Message::decode(c).map(Box::new))?
            }
            m::TEXT => p.text = c.opt(Cursor::str)?,
            m::ENTITIES => p.entities = c.opt(|c| c.list(MessageEntity::decode))?,
            m::PHOTO => p.photo = c.opt(|c| c.list(PhotoSize::decode))?,
            m::CAPTION => p.caption = c.opt(Cursor::str)?,
            m::CAPTION_ENTITIES => p.caption_entities = c.opt(|c| c.list(MessageEntity::decode))?,
            m::REPLY_MARKUP => p.reply_markup = c.opt(InlineKeyboardMarkup::decode)?,
            m::SENDER_BOOST_COUNT => {
                cold_set(cold, id, c.opt(Cursor::i64)?.map(C::SenderBoostCount))
            }
            m::SENDER_BUSINESS_BOT => {
                cold_set(cold, id, c.opt(User::decode)?.map(C::SenderBusinessBot))
            }
            m::SENDER_TAG => cold_set(cold, id, c.opt(Cursor::str)?.map(C::SenderTag)),
            m::BUSINESS_CONNECTION_ID => {
                cold_set(cold, id, c.opt(Cursor::str)?.map(C::BusinessConnectionId))
            }
            m::IS_TOPIC_MESSAGE => cold_set(cold, id, c.opt(Cursor::bool)?.map(C::IsTopicMessage)),
            m::IS_AUTOMATIC_FORWARD => {
                cold_set(cold, id, c.opt(Cursor::bool)?.map(C::IsAutomaticForward))
            }
            m::QUOTE => cold_set(cold, id, c.opt(TextQuote::decode)?.map(C::Quote)),
            m::REPLY_TO_CHECKLIST_TASK_ID => {
                cold_set(cold, id, c.opt(Cursor::i64)?.map(C::ReplyToChecklistTaskId));
            }
            m::VIA_BOT => cold_set(cold, id, c.opt(User::decode)?.map(C::ViaBot)),
            m::EDIT_DATE => cold_set(cold, id, c.opt(Cursor::time)?.map(C::EditDate)),
            m::HAS_PROTECTED_CONTENT => {
                cold_set(cold, id, c.opt(Cursor::bool)?.map(C::HasProtectedContent))
            }
            m::IS_FROM_OFFLINE => cold_set(cold, id, c.opt(Cursor::bool)?.map(C::IsFromOffline)),
            m::IS_PAID_POST => cold_set(cold, id, c.opt(Cursor::bool)?.map(C::IsPaidPost)),
            m::MEDIA_GROUP_ID => cold_set(cold, id, c.opt(Cursor::str)?.map(C::MediaGroupId)),
            m::AUTHOR_SIGNATURE => cold_set(cold, id, c.opt(Cursor::str)?.map(C::AuthorSignature)),
            m::PAID_STAR_COUNT => cold_set(cold, id, c.opt(Cursor::i64)?.map(C::PaidStarCount)),
            m::EFFECT_ID => cold_set(cold, id, c.opt(Cursor::str)?.map(C::EffectId)),
            m::SHOW_CAPTION_ABOVE_MEDIA => {
                cold_set(cold, id, c.opt(Cursor::bool)?.map(C::ShowCaptionAboveMedia));
            }
            m::HAS_MEDIA_SPOILER => {
                cold_set(cold, id, c.opt(Cursor::bool)?.map(C::HasMediaSpoiler))
            }
            m::LOCATION => cold_set(cold, id, c.opt(Location::decode)?.map(C::Location)),
            m::FORWARD_ORIGIN => cold_set(
                cold,
                id,
                c.opt(MessageOrigin::decode)?.map(C::ForwardOrigin),
            ),
            m::PINNED_MESSAGE => cold_set(
                cold,
                id,
                c.opt(MaybeInaccessibleMessage::decode)?
                    .map(C::PinnedMessage),
            ),
            _ => cold_set(
                cold,
                id,
                c.opt(Cursor::opaque)?.map(|raw| C::Opaque(id, raw)),
            ),
        }
        Ok(())
    }

    fn finish(p: MessagePartial, meta: Meta<[u64; 3]>) -> DecodeResult<Self> {
        let message_id = required(p.message_id, "message_id", meta.span)?;
        let date = required(p.date, "date", meta.span)?;
        let chat = required(p.chat, "chat", meta.span)?;
        Ok(Self {
            meta,
            message_id,
            date,
            chat,
            message_thread_id: p.message_thread_id,
            from_user: p.from_user,
            reply_to_message: p.reply_to_message,
            text: p.text,
            entities: p.entities,
            photo: p.photo,
            caption: p.caption,
            caption_entities: p.caption_entities,
            reply_markup: p.reply_markup,
            cold: cold_finish(p.cold),
        })
    }
}

// ---- Update: the four message fields and chat_member; every other update type is an unknown
// key here, reported to the hook as an unknown update type ----

#[derive(Debug)]
pub(crate) struct Update {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) update_id: i64,
    pub(crate) message: Option<Box<Message>>,
    pub(crate) edited_message: Option<Box<Message>>,
    pub(crate) channel_post: Option<Box<Message>>,
    pub(crate) edited_channel_post: Option<Box<Message>>,
    pub(crate) chat_member: Option<Box<ChatMemberUpdated>>,
}

#[derive(Default)]
pub(crate) struct UpdatePartial {
    update_id: Option<i64>,
    message: Option<Box<Message>>,
    edited_message: Option<Box<Message>>,
    channel_post: Option<Box<Message>>,
    edited_channel_post: Option<Box<Message>>,
    chat_member: Option<Box<ChatMemberUpdated>>,
}

pub(crate) static UPDATE: Table = Table {
    fields: &[
        f("update_id", Kind::I64, true, false),
        f("message", Kind::Object, false, false),
        f("edited_message", Kind::Object, false, false),
        f("channel_post", Kind::Object, false, false),
        f("edited_channel_post", Kind::Object, false, false),
        f("chat_member", Kind::Object, false, false),
    ],
    keys: &[
        ("channel_post", 3),
        ("chat_member", 5),
        ("edited_channel_post", 4),
        ("edited_message", 2),
        ("message", 1),
        ("update_id", 0),
    ],
};

fn boxed_message(c: &mut Cursor<'_>) -> DecodeResult<Box<Message>> {
    Message::decode(c).map(Box::new)
}

impl Decode for Update {
    const TABLE: &'static Table = &UPDATE;
    type Partial = UpdatePartial;
    type Bits = [u64; 1];
    const UNKNOWN_KEYS: Option<(&'static str, Site)> = Some(("Update", Site::UpdateType));

    fn set(p: &mut UpdatePartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => p.update_id = c.opt(Cursor::i64)?,
            1 => p.message = c.opt(boxed_message)?,
            2 => p.edited_message = c.opt(boxed_message)?,
            3 => p.channel_post = c.opt(boxed_message)?,
            4 => p.edited_channel_post = c.opt(boxed_message)?,
            _ => p.chat_member = c.opt(|c| ChatMemberUpdated::decode(c).map(Box::new))?,
        }
        Ok(())
    }

    fn finish(p: UpdatePartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let update_id = required(p.update_id, "update_id", meta.span)?;
        Ok(Self {
            meta,
            update_id,
            message: p.message,
            edited_message: p.edited_message,
            channel_post: p.channel_post,
            edited_channel_post: p.edited_channel_post,
            chat_member: p.chat_member,
        })
    }
}

// ---- MessageOrigin: tagged by `type` (two variants here); common field `date` ----

#[derive(Debug)]
pub(crate) enum MessageOrigin {
    User(MessageOriginUser),
    HiddenUser(MessageOriginHiddenUser),
    Unknown(Box<UnknownMember<MessageOriginCommon>>),
}

impl Union for MessageOrigin {
    const ENTITY: &'static str = "MessageOrigin";
    const KEY: &'static str = "type";
    type Common = MessageOriginCommon;

    fn variant(value: Option<&[u8]>, c: &mut Cursor<'_>) -> Option<DecodeResult<Self>> {
        Some(match value? {
            br#""user""# => MessageOriginUser::decode(c).map(Self::User),
            br#""hidden_user""# => MessageOriginHiddenUser::decode(c).map(Self::HiddenUser),
            _ => return None,
        })
    }

    fn unknown(member: UnknownMember<MessageOriginCommon>) -> Self {
        Self::Unknown(Box::new(member))
    }
}

#[derive(Debug)]
pub(crate) struct MessageOriginCommon {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) date: UnixTime,
}

#[derive(Default)]
pub(crate) struct MessageOriginCommonPartial {
    date: Option<UnixTime>,
}

pub(crate) static MESSAGE_ORIGIN_COMMON: Table = Table {
    fields: &[
        f("type", Kind::Str, true, false),
        f("date", Kind::UnixTime, true, false),
    ],
    keys: &[("date", 1), ("type", 0)],
};

impl Decode for MessageOriginCommon {
    const TABLE: &'static Table = &MESSAGE_ORIGIN_COMMON;
    type Partial = MessageOriginCommonPartial;
    type Bits = [u64; 1];

    fn set(p: &mut MessageOriginCommonPartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            // the tag: a constant of the variant
            0 => drop(c.opaque()?),
            _ => p.date = c.opt(Cursor::time)?,
        }
        Ok(())
    }

    fn finish(p: MessageOriginCommonPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let date = required(p.date, "date", meta.span)?;
        Ok(Self { meta, date })
    }
}

#[derive(Debug)]
pub(crate) struct MessageOriginUser {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) date: UnixTime,
    pub(crate) sender_user: User,
}

#[derive(Default)]
pub(crate) struct MessageOriginUserPartial {
    date: Option<UnixTime>,
    sender_user: Option<User>,
}

pub(crate) static MESSAGE_ORIGIN_USER: Table = Table {
    fields: &[
        f("type", Kind::Str, true, false),
        f("date", Kind::UnixTime, true, false),
        f("sender_user", Kind::Object, true, false),
    ],
    keys: &[("date", 1), ("sender_user", 2), ("type", 0)],
};

impl Decode for MessageOriginUser {
    const TABLE: &'static Table = &MESSAGE_ORIGIN_USER;
    type Partial = MessageOriginUserPartial;
    type Bits = [u64; 1];

    fn set(p: &mut MessageOriginUserPartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => drop(c.opaque()?),
            1 => p.date = c.opt(Cursor::time)?,
            _ => p.sender_user = c.opt(User::decode)?,
        }
        Ok(())
    }

    fn finish(p: MessageOriginUserPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let date = required(p.date, "date", meta.span)?;
        let sender_user = required(p.sender_user, "sender_user", meta.span)?;
        Ok(Self {
            meta,
            date,
            sender_user,
        })
    }
}

#[derive(Debug)]
pub(crate) struct MessageOriginHiddenUser {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) date: UnixTime,
    pub(crate) sender_user_name: Box<str>,
}

#[derive(Default)]
pub(crate) struct MessageOriginHiddenUserPartial {
    date: Option<UnixTime>,
    sender_user_name: Option<Box<str>>,
}

pub(crate) static MESSAGE_ORIGIN_HIDDEN_USER: Table = Table {
    fields: &[
        f("type", Kind::Str, true, false),
        f("date", Kind::UnixTime, true, false),
        f("sender_user_name", Kind::Str, true, false),
    ],
    keys: &[("date", 1), ("sender_user_name", 2), ("type", 0)],
};

impl Decode for MessageOriginHiddenUser {
    const TABLE: &'static Table = &MESSAGE_ORIGIN_HIDDEN_USER;
    type Partial = MessageOriginHiddenUserPartial;
    type Bits = [u64; 1];

    fn set(
        p: &mut MessageOriginHiddenUserPartial,
        id: u16,
        c: &mut Cursor<'_>,
    ) -> DecodeResult<()> {
        match id {
            0 => drop(c.opaque()?),
            1 => p.date = c.opt(Cursor::time)?,
            _ => p.sender_user_name = c.opt(Cursor::str)?,
        }
        Ok(())
    }

    fn finish(p: MessageOriginHiddenUserPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let date = required(p.date, "date", meta.span)?;
        let sender_user_name = required(p.sender_user_name, "sender_user_name", meta.span)?;
        Ok(Self {
            meta,
            date,
            sender_user_name,
        })
    }
}

// ---- MaybeInaccessibleMessage: undiscriminated, predicate `date == 0` ----

#[derive(Debug)]
pub(crate) enum MaybeInaccessibleMessage {
    Message(Box<Message>),
    Inaccessible(InaccessibleMessage),
    Unknown(Box<UnknownMember<InaccessibleMessage>>),
}

impl Union for MaybeInaccessibleMessage {
    const ENTITY: &'static str = "MaybeInaccessibleMessage";
    const KEY: &'static str = "date";
    // the shared fields are exactly InaccessibleMessage's
    type Common = InaccessibleMessage;

    fn variant(value: Option<&[u8]>, c: &mut Cursor<'_>) -> Option<DecodeResult<Self>> {
        Some(if value == Some(b"0") {
            InaccessibleMessage::decode(c).map(Self::Inaccessible)
        } else {
            Message::decode(c).map(|message| Self::Message(Box::new(message)))
        })
    }

    fn unknown(member: UnknownMember<InaccessibleMessage>) -> Self {
        Self::Unknown(Box::new(member))
    }
}

#[derive(Debug)]
pub(crate) struct InaccessibleMessage {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) chat: Chat,
    pub(crate) message_id: i64,
    pub(crate) date: UnixTime,
}

#[derive(Default)]
pub(crate) struct InaccessibleMessagePartial {
    chat: Option<Chat>,
    message_id: Option<i64>,
    date: Option<UnixTime>,
}

pub(crate) static INACCESSIBLE_MESSAGE: Table = Table {
    fields: &[
        f("chat", Kind::Object, true, false),
        f("message_id", Kind::I64, true, false),
        f("date", Kind::UnixTime, true, false),
    ],
    keys: &[("chat", 0), ("date", 2), ("message_id", 1)],
};

impl Decode for InaccessibleMessage {
    const TABLE: &'static Table = &INACCESSIBLE_MESSAGE;
    type Partial = InaccessibleMessagePartial;
    type Bits = [u64; 1];

    fn set(p: &mut InaccessibleMessagePartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => p.chat = c.opt(Chat::decode)?,
            1 => p.message_id = c.opt(Cursor::i64)?,
            _ => p.date = c.opt(Cursor::time)?,
        }
        Ok(())
    }

    fn finish(p: InaccessibleMessagePartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let chat = required(p.chat, "chat", meta.span)?;
        let message_id = required(p.message_id, "message_id", meta.span)?;
        let date = required(p.date, "date", meta.span)?;
        Ok(Self {
            meta,
            chat,
            message_id,
            date,
        })
    }
}

// ---- ChatMember: tagged by `status` (two variants here); common field `user` ----

#[derive(Debug)]
pub(crate) enum ChatMember {
    Member(ChatMemberMember),
    Administrator(Box<ChatMemberAdministrator>),
    Unknown(Box<UnknownMember<ChatMemberCommon>>),
}

impl Union for ChatMember {
    const ENTITY: &'static str = "ChatMember";
    const KEY: &'static str = "status";
    type Common = ChatMemberCommon;

    fn variant(value: Option<&[u8]>, c: &mut Cursor<'_>) -> Option<DecodeResult<Self>> {
        Some(match value? {
            br#""member""# => ChatMemberMember::decode(c).map(Self::Member),
            br#""administrator""# => ChatMemberAdministrator::decode(c)
                .map(|member| Self::Administrator(Box::new(member))),
            _ => return None,
        })
    }

    fn unknown(member: UnknownMember<ChatMemberCommon>) -> Self {
        Self::Unknown(Box::new(member))
    }
}

#[derive(Debug)]
pub(crate) struct ChatMemberCommon {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) user: User,
}

#[derive(Default)]
pub(crate) struct ChatMemberCommonPartial {
    user: Option<User>,
}

pub(crate) static CHAT_MEMBER_COMMON: Table = Table {
    fields: &[
        f("status", Kind::Str, true, false),
        f("user", Kind::Object, true, false),
    ],
    keys: &[("status", 0), ("user", 1)],
};

impl Decode for ChatMemberCommon {
    const TABLE: &'static Table = &CHAT_MEMBER_COMMON;
    type Partial = ChatMemberCommonPartial;
    type Bits = [u64; 1];

    fn set(p: &mut ChatMemberCommonPartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => drop(c.opaque()?),
            _ => p.user = c.opt(User::decode)?,
        }
        Ok(())
    }

    fn finish(p: ChatMemberCommonPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let user = required(p.user, "user", meta.span)?;
        Ok(Self { meta, user })
    }
}

#[derive(Debug)]
pub(crate) struct ChatMemberMember {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) user: User,
    pub(crate) until_date: Option<UnixTime>,
}

#[derive(Default)]
pub(crate) struct ChatMemberMemberPartial {
    user: Option<User>,
    until_date: Option<UnixTime>,
}

pub(crate) static CHAT_MEMBER_MEMBER: Table = Table {
    fields: &[
        f("status", Kind::Str, true, false),
        f("user", Kind::Object, true, false),
        f("until_date", Kind::UnixTime, false, false),
    ],
    keys: &[("status", 0), ("until_date", 2), ("user", 1)],
};

impl Decode for ChatMemberMember {
    const TABLE: &'static Table = &CHAT_MEMBER_MEMBER;
    type Partial = ChatMemberMemberPartial;
    type Bits = [u64; 1];

    fn set(p: &mut ChatMemberMemberPartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => drop(c.opaque()?),
            1 => p.user = c.opt(User::decode)?,
            _ => p.until_date = c.opt(Cursor::time)?,
        }
        Ok(())
    }

    fn finish(p: ChatMemberMemberPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let user = required(p.user, "user", meta.span)?;
        Ok(Self {
            meta,
            user,
            until_date: p.until_date,
        })
    }
}

#[derive(Debug)]
pub(crate) struct ChatMemberAdministrator {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) user: User,
    pub(crate) can_be_edited: bool,
    pub(crate) custom_title: Option<Box<str>>,
}

#[derive(Default)]
pub(crate) struct ChatMemberAdministratorPartial {
    user: Option<User>,
    can_be_edited: Option<bool>,
    custom_title: Option<Box<str>>,
}

pub(crate) static CHAT_MEMBER_ADMINISTRATOR: Table = Table {
    fields: &[
        f("status", Kind::Str, true, false),
        f("user", Kind::Object, true, false),
        f("can_be_edited", Kind::Bool, true, false),
        f("custom_title", Kind::Str, false, false),
    ],
    keys: &[
        ("can_be_edited", 2),
        ("custom_title", 3),
        ("status", 0),
        ("user", 1),
    ],
};

impl Decode for ChatMemberAdministrator {
    const TABLE: &'static Table = &CHAT_MEMBER_ADMINISTRATOR;
    type Partial = ChatMemberAdministratorPartial;
    type Bits = [u64; 1];

    fn set(
        p: &mut ChatMemberAdministratorPartial,
        id: u16,
        c: &mut Cursor<'_>,
    ) -> DecodeResult<()> {
        match id {
            0 => drop(c.opaque()?),
            1 => p.user = c.opt(User::decode)?,
            2 => p.can_be_edited = c.opt(Cursor::bool)?,
            _ => p.custom_title = c.opt(Cursor::str)?,
        }
        Ok(())
    }

    fn finish(p: ChatMemberAdministratorPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let user = required(p.user, "user", meta.span)?;
        let can_be_edited = required(p.can_be_edited, "can_be_edited", meta.span)?;
        Ok(Self {
            meta,
            user,
            can_be_edited,
            custom_title: p.custom_title,
        })
    }
}

// ---- ChatMemberUpdated: two ChatMember unions ----

#[derive(Debug)]
pub(crate) struct ChatMemberUpdated {
    pub(crate) meta: Meta<[u64; 1]>,
    pub(crate) chat: Chat,
    pub(crate) from_user: User,
    pub(crate) date: UnixTime,
    pub(crate) old_chat_member: ChatMember,
    pub(crate) new_chat_member: ChatMember,
}

#[derive(Default)]
pub(crate) struct ChatMemberUpdatedPartial {
    chat: Option<Chat>,
    from_user: Option<User>,
    date: Option<UnixTime>,
    old_chat_member: Option<ChatMember>,
    new_chat_member: Option<ChatMember>,
}

pub(crate) static CHAT_MEMBER_UPDATED: Table = Table {
    fields: &[
        f("chat", Kind::Object, true, false),
        f("from", Kind::Object, true, false),
        f("date", Kind::UnixTime, true, false),
        f("old_chat_member", Kind::Object, true, false),
        f("new_chat_member", Kind::Object, true, false),
    ],
    keys: &[
        ("chat", 0),
        ("date", 2),
        ("from", 1),
        ("from_user", 1),
        ("new_chat_member", 4),
        ("old_chat_member", 3),
    ],
};

impl Decode for ChatMemberUpdated {
    const TABLE: &'static Table = &CHAT_MEMBER_UPDATED;
    type Partial = ChatMemberUpdatedPartial;
    type Bits = [u64; 1];

    fn set(p: &mut ChatMemberUpdatedPartial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()> {
        match id {
            0 => p.chat = c.opt(Chat::decode)?,
            1 => p.from_user = c.opt(User::decode)?,
            2 => p.date = c.opt(Cursor::time)?,
            3 => p.old_chat_member = c.opt(ChatMember::decode)?,
            _ => p.new_chat_member = c.opt(ChatMember::decode)?,
        }
        Ok(())
    }

    fn finish(p: ChatMemberUpdatedPartial, meta: Meta<[u64; 1]>) -> DecodeResult<Self> {
        let chat = required(p.chat, "chat", meta.span)?;
        let from_user = required(p.from_user, "from", meta.span)?;
        let date = required(p.date, "date", meta.span)?;
        let old_chat_member = required(p.old_chat_member, "old_chat_member", meta.span)?;
        let new_chat_member = required(p.new_chat_member, "new_chat_member", meta.span)?;
        Ok(Self {
            meta,
            chat,
            from_user,
            date,
            old_chat_member,
            new_chat_member,
        })
    }
}
