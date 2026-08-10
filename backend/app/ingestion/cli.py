from typing import Annotated

import typer

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.repositories.ingestion import IngestionRepository
from app.db.session import SessionLocal
from app.ingestion.runner import IngestionRunner
from app.ingestion.schemas import DiscoveredGame
from app.ingestion.sources.selenium_wnba import SeleniumWnbaSource, source_game_id

app = typer.Typer(help="Independent WNBA statistics ingestion commands.")


def _source(headless: bool) -> SeleniumWnbaSource:
    settings = get_settings()
    return SeleniumWnbaSource(headless=headless, chrome_binary=settings.chrome_binary)


@app.command("scrape-season")
def scrape_season(
    season: Annotated[int, typer.Option(min=1997, help="WNBA season to import")],
    headless: Annotated[
        bool, typer.Option("--headless/--no-headless", help="Run Chrome without a window")
    ] = True,
    force: Annotated[bool, typer.Option(help="Update games already stored")] = False,
    limit: Annotated[int | None, typer.Option(min=1, help="Import only the first N games")] = None,
    completed_only: Annotated[
        bool,
        typer.Option(
            "--completed-only",
            help="Import only games currently marked FINAL on the WNBA schedule",
        ),
    ] = False,
    continue_on_error: Annotated[
        bool,
        typer.Option(
            "--continue-on-error/--stop-on-error",
            help="Continue importing after an individual game fails",
        ),
    ] = True,
) -> None:
    configure_logging()
    runner = IngestionRunner(SessionLocal, lambda: _source(headless))
    run = runner.run_season(
        season=season,
        force=force,
        limit=limit,
        continue_on_error=continue_on_error,
        completed_only=completed_only,
    )
    typer.echo(
        f"run={run.id} status={run.status} processed={run.games_processed} "
        f"skipped={run.games_skipped} failed={run.games_failed} "
        f"rows={run.player_stat_rows_upserted}"
    )
    if run.status in {"failed", "partial"}:
        raise typer.Exit(code=1)


@app.command("scrape-game")
def scrape_game(
    url: Annotated[str, typer.Option(help="WNBA game or box-score URL")],
    season: Annotated[int | None, typer.Option(help="Season; defaults to parsed game year")] = None,
    headless: Annotated[bool, typer.Option("--headless/--no-headless")] = True,
) -> None:
    configure_logging()
    source = _source(headless)
    game = DiscoveredGame(source_game_id=source_game_id(url), source_url=url)
    try:
        parsed = source.fetch_game(game, season or 0)
        if season is None:
            parsed.season = parsed.game_date.year
        with SessionLocal.begin() as session:
            rows = IngestionRepository(session).import_game(parsed)
        typer.echo(f"imported game={parsed.source_game_id} rows={rows}")
    finally:
        source.close()


if __name__ == "__main__":
    app()
