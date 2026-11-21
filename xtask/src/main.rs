//! `cargo xtask <task>` (alias in `.cargo/config.toml`).

use std::process::ExitCode;

use clap::Parser;

#[derive(Debug, Parser)]
#[command(name = "cargo xtask", bin_name = "cargo xtask")]
enum Xtask {
    /// Reproducible Bot API code generator (crates/butcher)
    Butcher(butcher::cli::Cli),
}

fn main() -> ExitCode {
    match Xtask::parse() {
        Xtask::Butcher(cli) => butcher::cli::exit(butcher::cli::run(cli.command)),
    }
}

#[cfg(test)]
mod tests {
    use clap::CommandFactory;
    use clap::error::ErrorKind;

    use super::*;

    #[test]
    fn command_is_valid() {
        Xtask::command().debug_assert();
    }

    #[test]
    fn butcher_help_lists_every_command() {
        let err = Xtask::try_parse_from(["cargo xtask", "butcher", "--help"]).unwrap_err();
        assert_eq!(err.kind(), ErrorKind::DisplayHelp);
        let help = err.render().to_string();
        assert!(
            help.contains("Usage: cargo xtask butcher <COMMAND>"),
            "{help}"
        );
        for name in ["fetch", "build", "emit", "diff", "check", "import-legacy"] {
            assert!(
                help.contains(&format!("  {name} ")),
                "{name} missing from:\n{help}"
            );
        }
    }

    #[test]
    fn butcher_command_reaches_the_stub() {
        let Xtask::Butcher(cli) =
            Xtask::try_parse_from(["cargo xtask", "butcher", "check"]).unwrap();
        assert_eq!(cli.command, butcher::cli::Command::Check);
        assert!(butcher::cli::run(cli.command).is_err());
    }
}
