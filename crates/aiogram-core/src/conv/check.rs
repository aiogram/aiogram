//! The strict check of Python values (`ModelBase.__init__`): exactly what the dump accepts,
//! without building its output.

use pyo3::prelude::*;

use super::errors::{Ctx, VResult};
use super::ir::Kind;
use super::json::dump;

pub(crate) fn check(
    py: Python<'_>,
    value: &Bound<'_, PyAny>,
    kind: &Kind,
    ctx: Ctx,
) -> VResult<()> {
    dump::walk::<false>(py, value, kind, ctx).map(drop)
}
