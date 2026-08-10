import json
from pathlib import Path

from bs4 import BeautifulSoup

from app.ingestion.parser import parse_box_score

FIXTURE = Path(__file__).parents[1] / "fixtures" / "completed_game.html"


def test_parses_all_players_without_whitelist() -> None:
    parsed = parse_box_score(
        FIXTURE.read_text(),
        source_url="https://www.wnba.com/game/pho-vs-lva-20240514/boxscore",
        source_game_id="pho-vs-lva-20240514",
        season=2024,
    )

    assert parsed.game_date.isoformat() == "2024-05-14"
    assert parsed.home_team.name == "Las Vegas Aces"
    assert parsed.away_team.name == "Phoenix Mercury"
    assert len(parsed.player_stats) == 3
    assert {row.display_name for row in parsed.player_stats} == {
        "Kahleah Copper",
        "Reserve Player",
        "A'ja Wilson",
    }

    dnp = next(row for row in parsed.player_stats if row.display_name == "Reserve Player")
    assert dnp.played is False
    assert dnp.minutes_seconds == 0

    wilson = next(row for row in parsed.player_stats if row.display_name == "A'ja Wilson")
    assert wilson.source_player_id == "2001"
    assert (wilson.fgm, wilson.fga, wilson.fg3m, wilson.fg3a) == (10, 18, 0, 0)


def test_uses_next_data_when_table_headings_do_not_identify_teams() -> None:
    soup = BeautifulSoup(FIXTURE.read_text(), "html.parser")
    for table in soup.select("table"):
        table.attrs.pop("data-team-name", None)
        table.attrs.pop("data-home", None)
        table["aria-label"] = "Box Score"
    for heading in soup.select("h2"):
        heading.string = "Box Score"
    soup.select_one("time").decompose()

    metadata = {
        "props": {
            "pageProps": {
                "game": {
                    "gameEt": "2024-05-14T22:00:00Z",
                    "awayTeam": {"teamCity": "Phoenix", "teamName": "Mercury"},
                    "homeTeam": {"teamCity": "Las Vegas", "teamName": "Aces"},
                }
            }
        }
    }
    script = soup.new_tag("script", id="__NEXT_DATA__", type="application/json")
    script.string = json.dumps(metadata)
    soup.body.append(script)

    parsed = parse_box_score(
        str(soup),
        source_url="https://www.wnba.com/game/1022400001/boxscore",
        source_game_id="1022400001",
        season=2024,
    )

    assert parsed.away_team.name == "Phoenix Mercury"
    assert parsed.home_team.name == "Las Vegas Aces"
    assert parsed.game_date.isoformat() == "2024-05-14"
    assert {row.team_name for row in parsed.player_stats} == {
        "Phoenix Mercury",
        "Las Vegas Aces",
    }


def test_parses_current_separate_shooting_columns_and_full_player_name() -> None:
    html = """
    <html><body>
      <time datetime="2025-05-02">Friday, May 2, 2025</time>
      <table data-team-name="Brazil National Team">
        <tr>
          <th>PLAYER</th><th>MIN</th><th>FGM</th><th>FGA</th>
          <th>3PM</th><th>3PA</th><th>FTM</th><th>FTA</th><th>PTS</th>
        </tr>
        <tr>
          <td>
            <a href="/player/100/emanuely-de-oliveria">
              <span class="Player_gbpNameFull__abc">Emanuely de Oliveria</span>
              <span class="Player_gbpNameShort__abc">E. de Oliveria</span>
            </a>
            <span>F</span>
          </td>
          <td>16:22</td><td>1</td><td>7</td><td>0</td><td>4</td>
          <td>1</td><td>2</td><td>3</td>
        </tr>
      </table>
      <table data-team-name="Chicago Sky" data-home="true">
        <tr>
          <th>PLAYER</th><th>MIN</th><th>FGM</th><th>FGA</th>
          <th>3PM</th><th>3PA</th><th>FTM</th><th>FTA</th><th>PTS</th>
        </tr>
        <tr>
          <td>
            <a href="/player/200/angel-reese">
              <span class="Player_gbpNameFull__abc">Angel Reese</span>
              <span class="Player_gbpNameShort__abc">A. Reese</span>
            </a>
            <span>F</span>
          </td>
          <td>16:40</td><td>4</td><td>7</td><td>0</td><td>0</td>
          <td>7</td><td>10</td><td>15</td>
        </tr>
      </table>
    </body></html>
    """

    parsed = parse_box_score(
        html,
        source_url="https://www.wnba.com/game/bra-vs-chi-1012500001/box-score",
        source_game_id="1012500001",
        season=2025,
    )

    assert [row.display_name for row in parsed.player_stats] == [
        "Emanuely de Oliveria",
        "Angel Reese",
    ]
    assert (
        parsed.player_stats[1].fgm,
        parsed.player_stats[1].fga,
        parsed.player_stats[1].ftm,
        parsed.player_stats[1].fta,
        parsed.player_stats[1].pts,
    ) == (4, 7, 7, 10, 15)
