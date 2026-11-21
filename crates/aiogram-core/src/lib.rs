//! `aiogram._core`: the native core of aiogram.

mod conv;
mod decode;

use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Version of the crate; the release bump keeps it equal to `aiogram.__version__`.
const VERSION: &str = env!("CARGO_PKG_VERSION");
/// Version of the pyo3 crate this module was built with, taken from `Cargo.lock` by `build.rs`.
const PYO3_VERSION: &str = env!("AIOGRAM_CORE_PYO3_VERSION");
/// Cargo profile (`debug` or `release`), set by `build.rs`.
const PROFILE: &str = env!("AIOGRAM_CORE_PROFILE");
/// Target triple, set by `build.rs`.
const TARGET: &str = env!("AIOGRAM_CORE_TARGET");
/// LTO mode of the profile, set by `build.rs`.
const LTO: &str = env!("AIOGRAM_CORE_LTO");

/// Build metadata of the extension, reported by `aiogram info`.
#[pyfunction(name = "build_info")]
fn py_build_info(py: Python<'_>) -> PyResult<Bound<'_, PyDict>> {
    let info = PyDict::new(py);
    for (key, value) in build_info() {
        info.set_item(key, value)?;
    }
    Ok(info)
}

#[pymodule(gil_used = false)]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", VERSION)?;
    m.add_function(wrap_pyfunction!(py_build_info, m)?)?;
    // one line per native group; its stub is `aiogram/_core/<name>.pyi` (AGENTS.md)
    register_submodule(m, "conv", conv::register)
}

/// Adds the native submodule `<parent>.<name>`, filled by `fill`.
///
/// Everything lives in one `.so`, so the import system has no file to find the submodule by:
/// the `sys.modules` entry is what makes `import aiogram._core.conv` and
/// `from aiogram._core.conv import Kind` work. The fully qualified name keeps `__name__` and
/// `repr` equal to the import path.
fn register_submodule(
    parent: &Bound<'_, PyModule>,
    name: &str,
    fill: fn(&Bound<'_, PyModule>) -> PyResult<()>,
) -> PyResult<()> {
    let py = parent.py();
    let qualified = format!("{}.{name}", parent.name()?);
    let module = PyModule::new(py, &qualified)?;
    // a spec (no loader: nothing to reload) keeps `importlib.util.find_spec` and pydoc working
    let spec = py
        .import("importlib.machinery")?
        .getattr("ModuleSpec")?
        .call1((&qualified, py.None()))?;
    module.setattr("__spec__", spec)?;
    module.setattr("__package__", parent.name()?)?;
    fill(&module)?;
    parent.add(name, &module)?;
    py.import("sys")?
        .getattr("modules")?
        .set_item(qualified, module)
}

fn build_info() -> [(&'static str, &'static str); 5] {
    [
        ("version", VERSION),
        ("pyo3_version", PYO3_VERSION),
        ("profile", PROFILE),
        ("lto", LTO),
        ("target", TARGET),
    ]
}

#[cfg(test)]
mod tests {
    #[test]
    fn build_info_fields_are_set() {
        for (key, value) in super::build_info() {
            assert!(!value.is_empty(), "{key} is empty");
        }
    }
}
