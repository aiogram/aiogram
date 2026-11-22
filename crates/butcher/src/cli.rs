//! `cargo xtask butcher <cmd>`. Every command is a stub until the plan that owns it fills it in.

use std::ffi::OsString;
use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Args, Parser, Subcommand};

use crate::{bundle, fetch};

#[derive(Debug, Parser)]
#[command(name = "butcher", about = "Reproducible Bot API code generator")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Command,
}

#[derive(Debug, Clone, PartialEq, Eq, Subcommand)]
pub enum Command {
    /// Download the Bot API sources into the cache (C-02)
    Fetch(FetchArgs),
    /// Sources -> per-adapter IR + merged IR + manifest (C-03..C-08)
    Build(BuildArgs),
    /// Write generated files from the IR (C-12+)
    Emit,
    /// Structured change list between two snapshots (C-10)
    Diff,
    /// Offline CI gate (C-23)
    Check,
    /// One-off `.butcher/**` migration (C-11)
    ImportLegacy,
}

#[derive(Debug, Clone, PartialEq, Eq, Args)]
pub struct FetchArgs {
    /// The Bot API page
    #[arg(long, default_value = fetch::HTML_URL)]
    pub html: String,
    /// An optional preview page (e.g. https://corefork.telegram.org/bots/api)
    #[arg(long)]
    pub preview: Option<String>,
    /// The machine-readable schema; HTML served here counts as unreachable
    #[arg(long, default_value = fetch::OPENAPI_URL)]
    pub openapi: String,
    #[arg(long, default_value = fetch::ERRORS_URL)]
    pub errors: String,
    #[arg(long, default_value = fetch::DEFAULT_CACHE)]
    pub cache: PathBuf,
    /// After fetching, pack the cached sources and manifest.toml into this tar.gz
    #[arg(long, value_name = "FILE")]
    pub bundle: Option<PathBuf>,
}

#[derive(Debug, Clone, PartialEq, Eq, Args)]
pub struct BuildArgs {
    #[arg(long, default_value = fetch::DEFAULT_CACHE)]
    pub cache: PathBuf,
    /// Read the sources from a bundle made by `fetch --bundle` instead of the cache
    #[arg(long, value_name = "BUNDLE")]
    pub offline: Option<PathBuf>,
}

/// Runs a command; `Err` is the message for stderr.
pub fn run(command: Command) -> Result<(), String> {
    let (name, owner) = match command {
        Command::Fetch(args) => return run_fetch(args).map_err(|e| e.to_string()),
        Command::Build(args) => {
            // the sources come from the cache or a bundle, never the network (D118)
            let fetched = match &args.offline {
                Some(bundle) => bundle::unpack(bundle, &args.cache),
                None => fetch::Fetched::load(&args.cache),
            };
            fetched.map_err(|e| e.to_string())?;
            ("build", "C-03..C-08")
        }
        Command::Emit => ("emit", "C-12+"),
        Command::Diff => ("diff", "C-10"),
        Command::Check => ("check", "C-23"),
        Command::ImportLegacy => ("import-legacy", "C-11"),
    };
    // ponytail: stubs exit 1 so a CI step wired to one cannot pass silently
    Err(format!(
        "butcher {name}: not implemented (owned by {owner})"
    ))
}

fn run_fetch(args: FetchArgs) -> Result<(), crate::Error> {
    let opts = fetch::Options {
        html: args.html,
        preview: args.preview,
        openapi: args.openapi,
        errors: args.errors,
        cache: args.cache,
        ..fetch::Options::default()
    };
    let fetched = fetch::fetch(&opts)?;
    for (name, record) in fetched.records() {
        println!("{name}: {:?} {}", record.status, record.url);
    }
    if let Some(out) = args.bundle {
        bundle::pack(&opts.cache, &out)?;
        println!("bundle: {}", out.display());
    }
    Ok(())
}

pub fn exit(result: Result<(), String>) -> ExitCode {
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(message) => {
            eprintln!("{message}");
            ExitCode::FAILURE
        }
    }
}

pub fn main(args: impl IntoIterator<Item = OsString>) -> ExitCode {
    exit(run(Cli::parse_from(args).command))
}
