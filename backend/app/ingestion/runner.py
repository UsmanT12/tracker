import logging
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import ScraperGameResult, ScraperRun
from app.db.repositories.ingestion import IngestionRepository
from app.ingestion.schemas import DiscoveredGame
from app.ingestion.sources.base import WnbaSource

logger = logging.getLogger(__name__)


class IngestionRunner:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        source_factory: Callable[[], WnbaSource],
    ) -> None:
        self.session_factory = session_factory
        self.source_factory = source_factory

    def _create_run(self, season: int) -> ScraperRun:
        with self.session_factory.begin() as session:
            run = ScraperRun(season=season, status="running")
            session.add(run)
            session.flush()
            run_id = run.id
        with self.session_factory() as session:
            return session.get(ScraperRun, run_id)

    def _update_run(self, run_id, **values: object) -> None:
        with self.session_factory.begin() as session:
            run = session.get(ScraperRun, run_id)
            if run is None:
                raise RuntimeError(f"scraper run {run_id} disappeared")
            for key, value in values.items():
                setattr(run, key, value)

    def _increment(self, run_id, field: str, amount: int = 1) -> None:
        with self.session_factory.begin() as session:
            run = session.get(ScraperRun, run_id)
            setattr(run, field, getattr(run, field) + amount)

    def _record_result(
        self,
        run_id,
        game: DiscoveredGame,
        status: str,
        *,
        rows: int = 0,
        error: str | None = None,
    ) -> None:
        with self.session_factory.begin() as session:
            session.add(
                ScraperGameResult(
                    scraper_run_id=run_id,
                    source_game_id=game.source_game_id,
                    source_url=game.source_url,
                    status=status,
                    rows_upserted=rows,
                    error_message=error,
                )
            )

    def run_season(
        self,
        *,
        season: int,
        force: bool = False,
        limit: int | None = None,
        continue_on_error: bool = True,
        completed_only: bool = False,
    ) -> ScraperRun:
        run = self._create_run(season)
        run_id = run.id
        source = self.source_factory()
        errors: list[str] = []
        try:
            games = source.discover_games(season, completed_only=completed_only)
            if limit is not None:
                games = games[:limit]
            self._update_run(run_id, games_discovered=len(games))

            for index, game in enumerate(games, start=1):
                with self.session_factory() as session:
                    exists = IngestionRepository(session).game_exists(game.source_game_id)
                if exists and not force:
                    logger.info(
                        "[%s/%s] skipped existing game_id=%s",
                        index,
                        len(games),
                        game.source_game_id,
                    )
                    self._increment(run_id, "games_skipped")
                    self._record_result(run_id, game, "skipped")
                    continue

                try:
                    parsed = source.fetch_game(game, season)
                    with self.session_factory.begin() as session:
                        rows = IngestionRepository(session).import_game(parsed)
                    self._increment(run_id, "games_processed")
                    self._increment(run_id, "player_stat_rows_upserted", rows)
                    self._record_result(run_id, game, "completed", rows=rows)
                    logger.info(
                        "[%s/%s] imported game_id=%s rows=%s",
                        index,
                        len(games),
                        game.source_game_id,
                        rows,
                    )
                except Exception as exc:
                    message = f"{game.source_game_id}: {type(exc).__name__}: {exc}"
                    errors.append(message)
                    self._increment(run_id, "games_failed")
                    self._record_result(run_id, game, "failed", error=message)
                    logger.exception(
                        "[%s/%s] failed game_id=%s url=%s",
                        index,
                        len(games),
                        game.source_game_id,
                        game.source_url,
                    )
                    if not continue_on_error:
                        raise

            status = "partial" if errors else "completed"
            self._update_run(
                run_id,
                status=status,
                completed_at=datetime.now(UTC),
                error_summary="\n".join(errors) or None,
            )
        except Exception as exc:
            self._update_run(
                run_id,
                status="failed",
                completed_at=datetime.now(UTC),
                error_summary=f"{type(exc).__name__}: {exc}",
            )
            raise
        finally:
            source.close()

        with self.session_factory() as session:
            return session.get(ScraperRun, run_id)
