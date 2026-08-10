import json
import re
from collections.abc import Iterable
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from app.ingestion.normalizer import (
    is_dnp,
    parse_game_date,
    parse_made_attempted,
    parse_minutes,
    safe_int,
)
from app.ingestion.schemas import IngestedGame, IngestedPlayerStat, IngestedTeam
from app.ingestion.selectors import (
    BOX_SCORE_TABLE_SELECTORS,
    GAME_DATE_SELECTORS,
    TEAM_NAME_SELECTORS,
)

HEADER_ALIASES = {
    "PLAYER": "PLAYER",
    "PLAYERS": "PLAYER",
    "MIN": "MIN",
    "MINUTES": "MIN",
    "FGM-A": "FGM-A",
    "FG": "FGM-A",
    "FGM": "FGM",
    "FGA": "FGA",
    "3PM-A": "3PM-A",
    "3PT": "3PM-A",
    "3PTM-A": "3PM-A",
    "3PM": "3PM",
    "3PA": "3PA",
    "FTM-A": "FTM-A",
    "FT": "FTM-A",
    "FTM": "FTM",
    "FTA": "FTA",
    "+/-": "+/-",
    "OREB": "OREB",
    "DREB": "DREB",
    "REB": "REB",
    "AST": "AST",
    "PF": "PF",
    "STL": "STL",
    "TO": "TO",
    "TOV": "TO",
    "BS": "BS",
    "BLK": "BS",
    "PTS": "PTS",
}


class BoxScoreParseError(ValueError):
    pass


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalized_header(value: str) -> str:
    cleaned = _clean(value).upper().replace("−", "-").replace("–", "-")
    return HEADER_ALIASES.get(cleaned, cleaned)


def _first_text(soup: BeautifulSoup, selectors: Iterable[str]) -> str | None:
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            if element.name == "time" and element.get("datetime"):
                return str(element["datetime"])[:10]
            text = _clean(element.get_text(" ", strip=True))
            if text:
                return text
    return None


def _table_team_name(table: Tag) -> str | None:
    explicit = table.get("data-team-name")
    if explicit:
        return _clean(str(explicit))

    label = table.get("aria-label")
    if label:
        match = re.match(r"(.+?)\s+(?:player\s+)?box score", str(label), re.I)
        if match:
            return _clean(match.group(1))

    heading = table.find_previous(["h2", "h3", "h4"])
    return _clean(heading.get_text(" ", strip=True)) if heading else None


def _next_data_game(soup: BeautifulSoup) -> dict[str, object] | None:
    script = soup.select_one("script#__NEXT_DATA__")
    if not script or not script.string:
        return None
    try:
        data = json.loads(script.string)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    props = data.get("props")
    if not isinstance(props, dict):
        return None
    page_props = props.get("pageProps")
    if not isinstance(page_props, dict):
        return None
    game = page_props.get("game")
    return game if isinstance(game, dict) else None


def _metadata_team_name(team: object) -> str | None:
    if not isinstance(team, dict):
        return None
    raw_name = team.get("teamName")
    if not isinstance(raw_name, str) or not _clean(raw_name):
        return None
    name = _clean(raw_name)
    raw_city = team.get("teamCity")
    city = _clean(raw_city) if isinstance(raw_city, str) else ""
    if city and city.casefold() not in name.casefold():
        return f"{city} {name}"
    return name


def _page_team_names(soup: BeautifulSoup) -> list[str]:
    game = _next_data_game(soup)
    if game:
        away_name = _metadata_team_name(game.get("awayTeam"))
        home_name = _metadata_team_name(game.get("homeTeam"))
        if away_name and home_name and away_name != home_name:
            return [away_name, home_name]

    candidates: list[str] = []
    for selector in TEAM_NAME_SELECTORS:
        for element in soup.select(selector):
            name = _clean(element.get_text(" ", strip=True))
            if name and name not in candidates:
                candidates.append(name)
    return candidates[-2:] if len(candidates) >= 2 else []


def _metadata_game_date(soup: BeautifulSoup) -> str | None:
    game = _next_data_game(soup)
    if not game:
        return None
    for key in ("gameEt", "gameTimeUTC"):
        value = game.get(key)
        if isinstance(value, str) and value:
            return value[:10]
    return None


def _team_names(soup: BeautifulSoup, tables: list[Tag]) -> list[str]:
    table_names = [_table_team_name(table) for table in tables]
    if all(table_names) and table_names[0] != table_names[1]:
        return [str(name) for name in table_names]

    page_names = _page_team_names(soup)
    if len(page_names) == 2 and page_names[0] != page_names[1]:
        return page_names
    raise BoxScoreParseError("two distinct team names are required")


def _header_data(table: Tag) -> tuple[Tag, list[str]] | None:
    for row in table.find_all("tr"):
        headers = [
            _normalized_header(cell.get_text(" ", strip=True))
            for cell in row.find_all(["th", "td"])
        ]
        if "PLAYER" in headers:
            return row, headers
    return None


def _tables(soup: BeautifulSoup) -> list[Tag]:
    for selector in BOX_SCORE_TABLE_SELECTORS:
        candidates = [
            table
            for table in soup.select(selector)
            if _header_data(table) is not None
        ]
        if len(candidates) >= 2:
            return candidates[:2]
    raise BoxScoreParseError("could not find two box-score tables")


def _row_values(row: Tag, headers: list[str]) -> tuple[dict[str, str], Tag | None]:
    cells = row.find_all(["th", "td"], recursive=False)
    if not cells:
        cells = row.find_all(["th", "td"])
    values = [_clean(cell.get_text(" ", strip=True)) for cell in cells]
    if len(values) < 2:
        return {}, None
    data = {headers[index]: value for index, value in enumerate(values[: len(headers)])}
    return data, cells[0]


def _player_display_name(player_cell: Tag | None, fallback: str) -> str:
    if not player_cell:
        return fallback
    full_name = player_cell.select_one('[class*="NameFull"]')
    if full_name:
        text = _clean(full_name.get_text(" ", strip=True))
        if text:
            return text
    player_link = player_cell.find("a", href=True)
    if player_link:
        link_strings = list(player_link.stripped_strings)
        if link_strings:
            return _clean(link_strings[0])
    return fallback


def _parse_player_rows(
    table: Tag,
    *,
    team_name: str,
    opponent_name: str,
    is_home: bool | None,
) -> list[IngestedPlayerStat]:
    header_data = _header_data(table)
    if not header_data:
        raise BoxScoreParseError(f"PLAYER column missing for {team_name}")
    header_row, headers = header_data
    rows = table.find_all("tr")
    header_index = rows.index(header_row)

    result: list[IngestedPlayerStat] = []
    for row in rows[header_index + 1 :]:
        data, player_cell = _row_values(row, headers)
        player_name = _player_display_name(player_cell, data.get("PLAYER", ""))
        if not player_name or "TOTAL" in player_name.upper():
            continue

        dnp, dnp_reason = is_dnp(data)
        fgm, fga = _shot_values(data, "FGM-A", "FGM", "FGA")
        fg3m, fg3a = _shot_values(data, "3PM-A", "3PM", "3PA")
        ftm, fta = _shot_values(data, "FTM-A", "FTM", "FTA")
        player_link = player_cell.find("a", href=True) if player_cell else None
        source_player_id = None
        if player_link:
            match = re.search(r"/player/([^/?#]+)", str(player_link["href"]))
            source_player_id = match.group(1) if match else None

        result.append(
            IngestedPlayerStat(
                display_name=player_name,
                source_player_id=source_player_id,
                team_name=team_name,
                opponent_name=opponent_name,
                is_home=is_home,
                played=not dnp,
                dnp_reason=dnp_reason,
                minutes_seconds=parse_minutes(data.get("MIN")),
                fgm=fgm,
                fga=fga,
                fg3m=fg3m,
                fg3a=fg3a,
                ftm=ftm,
                fta=fta,
                plus_minus=safe_int(data.get("+/-")) if data.get("+/-") else None,
                oreb=safe_int(data.get("OREB")),
                dreb=safe_int(data.get("DREB")),
                reb=safe_int(data.get("REB")),
                ast=safe_int(data.get("AST")),
                pf=safe_int(data.get("PF")),
                stl=safe_int(data.get("STL")),
                tov=safe_int(data.get("TO")),
                blk=safe_int(data.get("BS")),
                pts=safe_int(data.get("PTS")),
            )
        )
    return result


def _shot_values(
    data: dict[str, str],
    combined_key: str,
    made_key: str,
    attempted_key: str,
) -> tuple[int, int]:
    if data.get(combined_key):
        return parse_made_attempted(data[combined_key])
    return safe_int(data.get(made_key)), safe_int(data.get(attempted_key))


def parse_box_score(
    html: str,
    *,
    source_url: str,
    source_game_id: str,
    season: int,
) -> IngestedGame:
    soup = BeautifulSoup(html, "html.parser")
    tables = _tables(soup)
    team_names = _team_names(soup, tables)

    date_text = (
        str(soup.select_one("[data-game-date]")["data-game-date"])
        if soup.select_one("[data-game-date]")
        else _first_text(soup, GAME_DATE_SELECTORS) or _metadata_game_date(soup)
    )
    if not date_text:
        raise BoxScoreParseError("game date is required")

    home_index = next(
        (
            index
            for index, table in enumerate(tables)
            if str(table.get("data-home", "")).lower() == "true"
        ),
        1,
    )
    away_index = 1 - home_index
    home_name = str(team_names[home_index])
    away_name = str(team_names[away_index])
    stats: list[IngestedPlayerStat] = []
    for index, table in enumerate(tables):
        team_name = str(team_names[index])
        opponent_name = str(team_names[1 - index])
        stats.extend(
            _parse_player_rows(
                table,
                team_name=team_name,
                opponent_name=opponent_name,
                is_home=index == home_index,
            )
        )

    parsed_path = urlparse(source_url).path.lower()
    season_type = "playoffs" if "playoff" in parsed_path else "regular"
    return IngestedGame(
        source_game_id=source_game_id,
        source_url=source_url,
        season=season,
        season_type=season_type,
        game_date=parse_game_date(date_text),
        home_team=IngestedTeam(name=home_name),
        away_team=IngestedTeam(name=away_name),
        player_stats=stats,
    )
