# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Git AI Reporter: AI-Driven Git Repository Analysis and Narrative Generation.

This script analyzes a Git repository over a specified timeframe, uses a tiered
set of Google Gemini models to summarize the development activity, and generates
two key artifacts:
1. A narrative summary in NEWS.md for stakeholders.
2. A structured list of changes in CHANGELOG.txt, following the
   "Keep a Changelog" standard.
"""

import asyncio
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import os
from pathlib import Path
import shutil
import tomllib
from typing import Final

from git import GitCommandError
from git import NoSuchPathError
from git import Repo
from google import genai
from pydantic import BaseModel
from rich.console import Console
import typer

from git_ai_reporter import __version__
from git_ai_reporter.analysis.git_analyzer import GitAnalyzer
from git_ai_reporter.analysis.git_analyzer import GitAnalyzerConfig
from git_ai_reporter.cache import CacheManager
from git_ai_reporter.config import Settings
from git_ai_reporter.orchestration import AnalysisOrchestrator
from git_ai_reporter.orchestration import OrchestratorConfig
from git_ai_reporter.orchestration import OrchestratorServices
from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.services.gemini import GeminiClientConfig
from git_ai_reporter.services.gemini import GeminiClientError
from git_ai_reporter.writing.artifact_writer import ArtifactWriter

CONSOLE: Final = Console()


class RepositoryParams(BaseModel):
    """Repository-related parameters."""

    repo_path: str


class TimeRangeParams(BaseModel):
    """Time range parameters for analysis."""

    weeks: int
    start_date_str: str | None = None
    end_date_str: str | None = None


class AppConfigParams(BaseModel):
    """Application configuration parameters."""

    config_file: str | None = None
    cache_dir: str
    no_cache: bool = False
    debug: bool = False
    pre_release: str | None = None


class MainFunctionParams(BaseModel):
    """All parameters for the main function."""

    repo_path: str
    weeks: int
    start_date_str: str | None = None
    end_date_str: str | None = None
    config_file: str | None = None
    cache_dir: str
    no_cache: bool = False
    debug: bool = False


# Constants for history generation detection
MIN_NEWS_CONTENT_LENGTH: Final = 100
MIN_NEWS_LINE_COUNT: Final = 5

# Configuration status constants
CONFIG_SET_STATUS: Final = "Set"
CONFIG_NOT_SET_STATUS: Final = "Not set"

# Version information is imported at the top

APP: Final = typer.Typer(
    name="git-ai-reporter",
    help="AI-Driven Git Repository Analysis and Narrative Generation",
    add_completion=True,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=False,  # Allow running without args
    epilog="[bold]For more information:[/bold] https://github.com/paudley/git-ai-reporter",
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        CONSOLE.print(
            f"[bold green]git-ai-reporter[/bold green] version [cyan]{__version__}[/cyan]"
        )
        raise typer.Exit()


# --- Helper Functions for CLI Setup ---
def _setup(
    repo_path: str, settings: Settings, cache_dir: str, no_cache: bool, debug: bool
) -> tuple[AnalysisOrchestrator, Repo]:
    """Initializes and returns the main AnalysisOrchestrator and Repo object.

    This function acts as the composition root, creating and wiring together all
    the necessary service objects for the application.

    Args:
        repo_path: The path to the Git repository.
        settings: The application settings object.
        cache_dir: The directory to store cache files.
        no_cache: A flag to bypass caching.
        debug: A flag to enable debug mode.

    Returns:
        A tuple containing an initialized AnalysisOrchestrator instance and the Repo object.

    Raises:
        typer.Exit: If initialization fails due to a missing API key or invalid repo path.
    """
    try:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment or .env file.")

        # Create Gemini client
        gemini_client = _create_gemini_client(settings, debug)

        # Initialize repository
        repo = _initialize_repo(repo_path)

        # Create services and config
        services = _create_services(repo, settings, cache_dir, gemini_client, debug)
        config = _create_config(no_cache, settings, debug)

        return AnalysisOrchestrator(services=services, config=config), repo
    except (ValueError, FileNotFoundError) as e:
        CONSOLE.print(str(e), style="bold red")
        raise typer.Exit(code=1) from e


def _create_gemini_client(settings: Settings, debug: bool) -> GeminiClient:
    """Create and configure a Gemini client."""
    gemini_config = GeminiClientConfig(
        model_tier1=settings.MODEL_TIER_1,
        model_tier2=settings.MODEL_TIER_2,
        model_tier3=settings.MODEL_TIER_3,
        input_token_limit_tier1=settings.GEMINI_INPUT_TOKEN_LIMIT_TIER1,
        input_token_limit_tier2=settings.GEMINI_INPUT_TOKEN_LIMIT_TIER2,
        input_token_limit_tier3=settings.GEMINI_INPUT_TOKEN_LIMIT_TIER3,
        max_tokens_tier1=settings.MAX_TOKENS_TIER_1,
        max_tokens_tier2=settings.MAX_TOKENS_TIER_2,
        max_tokens_tier3=settings.MAX_TOKENS_TIER_3,
        temperature=settings.TEMPERATURE,
        api_timeout=settings.GEMINI_API_TIMEOUT,
        debug=debug,
    )
    return GeminiClient(genai.Client(api_key=settings.GEMINI_API_KEY), gemini_config)


def _initialize_repo(repo_path: str) -> Repo:
    """Initialize and validate repository."""
    try:
        return Repo(repo_path, search_parent_directories=True)
    except (GitCommandError, NoSuchPathError) as e:
        raise FileNotFoundError(f"Not a valid git repository: {repo_path}") from e


def _create_services(
    repo: Repo, settings: Settings, cache_dir: str, gemini_client: GeminiClient, debug: bool
) -> OrchestratorServices:
    """Create orchestrator services."""
    repo_path_obj = Path(repo.working_dir)
    cache_manager = CacheManager(repo_path_obj / cache_dir)

    git_analyzer = GitAnalyzer(
        repo,
        GitAnalyzerConfig(
            trivial_commit_types=settings.TRIVIAL_COMMIT_TYPES,
            trivial_file_patterns=settings.TRIVIAL_FILE_PATTERNS,
            git_command_timeout=settings.GIT_COMMAND_TIMEOUT,
            debug=debug,
        ),
    )
    artifact_writer = ArtifactWriter(
        news_file=str(repo_path_obj / settings.NEWS_FILE),
        changelog_file=str(repo_path_obj / settings.CHANGELOG_FILE),
        daily_updates_file=str(repo_path_obj / settings.DAILY_UPDATES_FILE),
        console=CONSOLE,
    )
    return OrchestratorServices(
        git_analyzer=git_analyzer,
        gemini_client=gemini_client,
        cache_manager=cache_manager,
        artifact_writer=artifact_writer,
        console=CONSOLE,
    )


def _create_config(no_cache: bool, settings: Settings, debug: bool) -> OrchestratorConfig:
    """Create orchestrator configuration."""
    return OrchestratorConfig(
        no_cache=no_cache,
        max_concurrent_tasks=settings.MAX_CONCURRENT_GIT_COMMANDS,
        debug=debug,
    )


def _load_settings(config_file: str | None) -> Settings:
    """Loads settings from a TOML file, falling back to defaults."""
    if not config_file:
        return Settings()

    config_path = Path(config_file)
    if not config_path.is_file():
        CONSOLE.print(f"Config file not found: {config_file}", style="bold red")
        raise typer.Exit(code=1)
    with config_path.open("rb") as f:
        toml_config = tomllib.load(f)
    return Settings(**toml_config)


def _determine_date_range(
    weeks: int, start_date_str: str | None, end_date_str: str | None
) -> tuple[datetime, datetime]:
    """Determines the start and end date for the analysis."""
    end_date = (
        datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if end_date_str
        else datetime.now(timezone.utc)
    )
    start_date = (
        datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if start_date_str
        else end_date - timedelta(weeks=weeks)
    )
    return start_date, end_date


def _should_generate_full_history(repo_path: str, settings: Settings) -> bool:
    """Determines if we should generate the full repository history.

    Returns True if NEWS.md doesn't exist or is empty/trivial.

    Args:
        repo_path: Path to the repository.
        settings: Application settings.

    Returns:
        True if full history should be generated.
    """
    news_file = Path(repo_path) / settings.NEWS_FILE

    # If file doesn't exist, generate full history
    if not news_file.exists():
        return True

    # If file is empty or very small (just header), generate full history
    try:
        content = news_file.read_text(encoding="utf-8").strip()
        # Consider it empty if it's just the header or very minimal content
        if len(content) < MIN_NEWS_CONTENT_LENGTH or content.count("\n") < MIN_NEWS_LINE_COUNT:
            return True
    except (OSError, UnicodeDecodeError):
        # If we can't read it, regenerate to be safe
        return True

    return False


def _get_full_repo_date_range(git_analyzer: GitAnalyzer) -> tuple[datetime, datetime]:
    """Gets the full date range for the repository from first commit to now.

    Args:
        git_analyzer: The git analyzer instance.

    Returns:
        Tuple of (start_date, end_date) covering the full repository history.
    """
    end_date = datetime.now(timezone.utc)

    # Get the first commit date
    if first_commit_date := git_analyzer.get_first_commit_date():
        # Start from the beginning of the week containing the first commit
        start_date = first_commit_date.replace(tzinfo=timezone.utc)
        # Round down to start of week (Monday)
        days_since_monday = start_date.weekday()
        start_date = start_date - timedelta(days=days_since_monday)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # Fallback to 1 year if we can't determine first commit
        start_date = end_date - timedelta(weeks=52)

    return start_date, end_date


def _run_analysis(
    repo_params: RepositoryParams,
    time_params: TimeRangeParams,
    app_config: AppConfigParams,
) -> None:
    """Core analysis logic extracted from main CLI function.

    Args:
        repo_params: Repository-related parameters.
        time_params: Time range parameters for analysis.
        app_config: Application configuration parameters.
    """
    settings = _load_settings(app_config.config_file)
    orchestrator, repo = _setup(
        repo_params.repo_path, settings, app_config.cache_dir, app_config.no_cache, app_config.debug
    )
    try:
        # Check if we should generate full history (when NEWS.md is missing/empty)
        if not time_params.start_date_str and _should_generate_full_history(
            repo_params.repo_path, settings
        ):
            CONSOLE.print(
                "NEWS.md not found or empty - generating full repository history", style="yellow"
            )
            start_date, end_date = _get_full_repo_date_range(orchestrator.services.git_analyzer)
            CONSOLE.print(
                f"Analyzing full repository history from {start_date.date()} to {end_date.date()}"
            )
        else:
            start_date, end_date = _determine_date_range(
                time_params.weeks, time_params.start_date_str, time_params.end_date_str
            )

        asyncio.run(orchestrator.run(start_date, end_date, app_config.pre_release))
    except GeminiClientError as e:
        CONSOLE.print(f"\n[bold red]A fatal error occurred during analysis:[/bold red]\n{e}")
        raise typer.Exit(code=1) from e
    finally:
        # Ensure the repo object is closed to release all resources and child processes.
        repo.close()


# --- Main Application Logic ---
@APP.command("analyze", help="Analyze repository and generate documentation")
def analyze(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    repo_path: str = typer.Option(
        ".",
        "--repo-path",
        "-r",
        help="Path to the Git repository.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        rich_help_panel="Repository Configuration",
    ),
    weeks: int = typer.Option(
        4,
        "--weeks",
        "-w",
        min=1,
        max=52,
        help="Number of past weeks to analyze.",
        rich_help_panel="Time Range",
    ),
    start_date_str: str | None = typer.Option(
        None,
        "--start-date",
        "-s",
        help="Start date in YYYY-MM-DD format. Overrides --weeks.",
        rich_help_panel="Time Range",
    ),
    end_date_str: str | None = typer.Option(
        None,
        "--end-date",
        "-e",
        help="End date in YYYY-MM-DD format. Defaults to now.",
        rich_help_panel="Time Range",
    ),
    config_file: str | None = typer.Option(
        None,
        "--config-file",
        "-c",
        help="Path to a TOML configuration file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        rich_help_panel="Configuration",
    ),
    cache_dir: str = typer.Option(
        ".git-report-cache",
        "--cache-dir",
        help="Path to the cache directory.",
        rich_help_panel="Configuration",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Ignore existing cache and re-analyze everything.",
        rich_help_panel="Configuration",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode with verbose logging and no progress bars.",
        rich_help_panel="Output Options",
    ),
    pre_release: str | None = typer.Option(
        None,
        "--pre-release",
        help="Generate release documentation for the specified version. Formats content as if the release has already happened (e.g., '1.2.3').",
        rich_help_panel="Output Options",
    ),
    version: bool = typer.Option(  # pylint: disable=unused-argument
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Generates AI-powered development summaries for a Git repository.

    This command analyzes a Git repository over a specified timeframe, uses Google's
    Gemini models to understand the changes, and then generates two key artifacts:
    a narrative summary in NEWS.md and a structured changelog in CHANGELOG.txt.

    Args:
        repo_path: The file path to the local Git repository.
        weeks: The number of past weeks to analyze. This is overridden by
            start_date if provided.
        start_date_str: Start date in YYYY-MM-DD format. Overrides weeks parameter.
        end_date_str: End date in YYYY-MM-DD format. Defaults to current date.
        config_file: Path to a TOML configuration file for settings.
        cache_dir: Directory path for storing cache files.
        no_cache: If True, ignore existing cache and re-analyze everything.
        debug: Enable verbose logging and disable progress bars.
        pre_release: Version string for pre-release documentation generation.
            Formats content as if the release has already happened.
        version: If True, show version information and exit.
    """
    repo_params = RepositoryParams(repo_path=repo_path)
    time_params = TimeRangeParams(
        weeks=weeks,
        start_date_str=start_date_str,
        end_date_str=end_date_str,
    )
    app_config = AppConfigParams(
        config_file=config_file,
        cache_dir=cache_dir,
        no_cache=no_cache,
        debug=debug,
        pre_release=pre_release,
    )

    _run_analysis(repo_params, time_params, app_config)


@APP.command("cache", help="Manage cache operations")
def cache_command(
    clear: bool = typer.Option(
        False,
        "--clear",
        help="Clear all cached data",
        rich_help_panel="Actions",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        help="Show cache statistics",
        rich_help_panel="Actions",
    ),
    cache_dir: str = typer.Option(
        ".git-report-cache",
        "--cache-dir",
        help="Path to the cache directory.",
        rich_help_panel="Configuration",
    ),
) -> None:
    """Manage the analysis cache.

    This command allows you to clear or inspect the cache used by git-ai-reporter
    to store API responses and analysis results.
    """
    cache_path = Path(cache_dir)

    if show:
        if cache_path.exists():
            cache_size = sum(f.stat().st_size for f in cache_path.rglob("*") if f.is_file())
            cache_files = len(list(cache_path.rglob("*")))
            CONSOLE.print("[bold]Cache Statistics:[/bold]")
            CONSOLE.print(f"  Location: [cyan]{cache_path.absolute()}[/cyan]")
            CONSOLE.print(f"  Files: [green]{cache_files}[/green]")
            CONSOLE.print(f"  Size: [yellow]{cache_size / (1024 * 1024):.2f} MB[/yellow]")
        else:
            CONSOLE.print("[yellow]No cache directory found.[/yellow]")

    if clear:
        if cache_path.exists():
            shutil.rmtree(cache_path)
            CONSOLE.print(f"[green]✓[/green] Cache cleared at [cyan]{cache_path}[/cyan]")
        else:
            CONSOLE.print("[yellow]No cache to clear.[/yellow]")

    if not clear and not show:
        CONSOLE.print("[yellow]Please specify --clear or --show[/yellow]")
        raise typer.Exit(1)


@APP.command("config", help="Show configuration information")
def config_command(
    show_env: bool = typer.Option(
        False,
        "--env",
        help="Show environment variables",
        rich_help_panel="Options",
    ),
    validate: bool = typer.Option(
        False,
        "--validate",
        help="Validate configuration",
        rich_help_panel="Options",
    ),
) -> None:
    """Display and validate configuration settings.

    This command shows the current configuration settings and can validate
    that all required settings are properly configured.
    """
    CONSOLE.print("[bold]Git AI Reporter Configuration[/bold]\n")

    if show_env:
        CONSOLE.print("[bold cyan]Environment Variables:[/bold cyan]")
        env_vars = {
            "GEMINI_API_KEY": (
                CONFIG_SET_STATUS if os.getenv("GEMINI_API_KEY") else CONFIG_NOT_SET_STATUS
            ),
            "GIT_AI_REPORTER_CONFIG": os.getenv("GIT_AI_REPORTER_CONFIG", CONFIG_NOT_SET_STATUS),
            "GIT_AI_REPORTER_CACHE": os.getenv("GIT_AI_REPORTER_CACHE", CONFIG_NOT_SET_STATUS),
        }
        for key, value in env_vars.items():
            status = "[green]✓[/green]" if value != CONFIG_NOT_SET_STATUS else "[red]✗[/red]"
            CONSOLE.print(f"  {status} {key}: {value}")

    if validate:
        CONSOLE.print("\n[bold cyan]Configuration Validation:[/bold cyan]")
        try:
            settings = Settings()
            if settings.GEMINI_API_KEY:
                CONSOLE.print("  [green]✓[/green] Gemini API key configured")
            else:
                CONSOLE.print("  [red]✗[/red] Gemini API key missing")
                raise typer.Exit(1)

            CONSOLE.print("  [green]✓[/green] All settings valid")
        except Exception as e:
            CONSOLE.print(f"  [red]✗[/red] Configuration error: {e}")
            raise typer.Exit(1)

    if not show_env and not validate:
        # Show basic info
        try:
            settings = Settings()
            CONSOLE.print("[bold]Model Configuration:[/bold]")
            CONSOLE.print(f"  Tier 1: [cyan]{settings.MODEL_TIER_1}[/cyan]")
            CONSOLE.print(f"  Tier 2: [cyan]{settings.MODEL_TIER_2}[/cyan]")
            CONSOLE.print(f"  Tier 3: [cyan]{settings.MODEL_TIER_3}[/cyan]")
            CONSOLE.print("\n[bold]Output Files:[/bold]")
            CONSOLE.print(f"  News: [cyan]{settings.NEWS_FILE}[/cyan]")
            CONSOLE.print(f"  Changelog: [cyan]{settings.CHANGELOG_FILE}[/cyan]")
            CONSOLE.print(f"  Daily Updates: [cyan]{settings.DAILY_UPDATES_FILE}[/cyan]")
        except Exception as e:
            CONSOLE.print(f"[red]Error loading configuration: {e}[/red]")
            raise typer.Exit(1)


@APP.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(  # pylint: disable=unused-argument
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Git AI Reporter - Transform your Git history into intelligent documentation.

    When run without a subcommand, analyzes the current directory with default settings.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand provided, run analyze with defaults
        CONSOLE.print(
            "[dim]No command specified, running 'analyze' on current directory...[/dim]\n"
        )
        analyze(
            repo_path=".",
            weeks=4,
            start_date_str=None,
            end_date_str=None,
            config_file=None,
            cache_dir=".git-report-cache",
            no_cache=False,
            debug=False,
            pre_release=None,
            version=False,
        )


def main() -> None:
    """Entry point for the CLI application."""
    APP()


if __name__ == "__main__":
    main()
