"""Copy the legacy ``player_stats`` table into the normalized schema.

The source table is read-only. Run Alembic first, inspect the dry-run summary,
then pass ``--execute`` to import.
"""

import argparse
import re
from collections import defaultdict
from datetime import date

from app.core.config import get_settings
from app.db.repositories.ingestion import IngestionRepository
from app.ingestion.normalizer import parse_minutes
from app.ingestion.schemas import IngestedGame, IngestedPlayerStat, IngestedTeam
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Write normalized records")
    args = parser.parse_args()

    engine = create_engine(get_settings().database_url)
    with engine.connect() as connection:
        exists = connection.scalar(
            text("SELECT to_regclass('public.player_stats') IS NOT NULL")
        )
        if not exists:
            print("Legacy player_stats table was not found.")
            return 1
        rows = connection.execute(text("SELECT * FROM player_stats ORDER BY game_date")).all()

    grouped: dict[tuple[date, tuple[str, str]], list[dict]] = defaultdict(list)
    skipped = 0
    for raw in rows:
        row = dict(raw._mapping)
        team = str(row.get("team") or "").strip()
        opponent = str(row.get("opponent") or "").strip()
        if not team or not opponent:
            skipped += 1
            continue
        grouped[(row["game_date"], tuple(sorted((team, opponent))))].append(row)

    print(
        f"Found {len(rows)} legacy rows across {len(grouped)} games; "
        f"{skipped} rows lack an opponent and will be skipped."
    )
    if not args.execute:
        print("Dry run only. Re-run with --execute after reviewing this summary.")
        return 0

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    imported_rows = 0
    for (game_date, team_pair), game_rows in grouped.items():
        away_name, home_name = team_pair
        stats = []
        for row in game_rows:
            minutes = parse_minutes(row.get("minutes"))
            stats.append(
                IngestedPlayerStat(
                    display_name=row["player"],
                    team_name=row["team"],
                    opponent_name=row["opponent"],
                    is_home=None,
                    played=minutes > 0,
                    dnp_reason=None if minutes > 0 else "Legacy DNP",
                    minutes_seconds=minutes,
                    fgm=row.get("fgm") or 0,
                    fga=row.get("fga") or 0,
                    fg3m=row.get("tpm") or 0,
                    fg3a=row.get("tpa") or 0,
                    ftm=row.get("ftm") or 0,
                    fta=row.get("fta") or 0,
                    plus_minus=row.get("plus_minus"),
                    oreb=row.get("oreb") or 0,
                    dreb=row.get("dreb") or 0,
                    reb=row.get("reb") or 0,
                    ast=row.get("ast") or 0,
                    pf=row.get("pf") or 0,
                    stl=row.get("stl") or 0,
                    tov=row.get("tov") or 0,
                    blk=row.get("blk") or 0,
                    pts=row.get("pts") or 0,
                )
            )
        source_id = f"legacy-{game_date.isoformat()}-{slug(away_name)}-{slug(home_name)}"
        game = IngestedGame(
            source_game_id=source_id,
            source_url=f"legacy://player_stats/{source_id}",
            season=game_date.year,
            game_date=game_date,
            away_team=IngestedTeam(name=away_name),
            home_team=IngestedTeam(name=home_name),
            player_stats=stats,
        )
        with factory.begin() as session:
            imported_rows += IngestionRepository(session).import_game(game)

    print(f"Imported or updated {imported_rows} player-game rows from {len(grouped)} games.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
