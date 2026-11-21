//! `cargo xtask butcher <cmd>`. Every command is a stub until the plan that owns it fills it in.

use std::ffi::OsString;
use std::process::ExitCode;

use clap::{Parser, Subcommand};

#[derive(Debug, Parser)]
#[command(name = "butcher", about = "Reproducible Bot API code generator")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Command,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Subcommand)]
pub enum Command {
    /// Download the Bot API sources into the cache (C-02)
    Fetch,
    /// Sources -> per-adapter IR + merged IR + manifest (C-03..C-08)
    Build,
    /// Write generated files from the IR (C-12+)
    Emit,
    /// Structured change list between two snapshots (C-10)
    Diff,
    /// Offline CI gate (C-23)
    Check,
    /// One-off `.butcher/**` migration (C-11)
    ImportLegacy,
}

/// Runs a command; `Err` is the message for stderr.
pub fn run(command: Command) -> Result<(), String> {
    let (name, owner) = match command {
        Command::Fetch => ("fetch", "C-02"),
        Command::Build => ("build", "C-03..C-08"),
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
