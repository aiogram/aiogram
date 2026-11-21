use butcher::cli::{Cli, Command, exit, run};
use clap::{CommandFactory, Parser};

const COMMANDS: [&str; 6] = ["fetch", "build", "emit", "diff", "check", "import-legacy"];

#[test]
fn command_is_valid() {
    Cli::command().debug_assert();
}

#[test]
fn lists_the_six_commands() {
    let cli = Cli::command();
    let names: Vec<_> = cli.get_subcommands().map(|c| c.get_name()).collect();
    assert_eq!(names, COMMANDS);
}

#[test]
fn every_command_is_a_failing_stub() {
    for name in COMMANDS {
        let command = Cli::try_parse_from(["butcher", name]).unwrap().command;
        let message = run(command).unwrap_err();
        assert!(
            message.starts_with(&format!("butcher {name}: not implemented (owned by C-")),
            "{message}"
        );
    }
    assert_eq!(exit(run(Command::Fetch)), std::process::ExitCode::FAILURE);
    assert_eq!(exit(Ok(())), std::process::ExitCode::SUCCESS);
}
