import logging
import re
import time
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from app.ingestion.parser import parse_box_score
from app.ingestion.schemas import DiscoveredGame, IngestedGame
from app.ingestion.selectors import SCHEDULE_GAME_LINK_SELECTORS

logger = logging.getLogger(__name__)

FINAL_STATUS_PATTERN = re.compile(r"^FINAL(?:/\w+)?$", re.IGNORECASE)


def schedule_url(season: int) -> str:
    return f"https://www.wnba.com/schedule?season={season}&month=all"


def source_game_id(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    match = re.search(r"/game/([^/]+)", path)
    if match:
        return match.group(1)
    parts = [
        part for part in path.split("/") if part and part not in {"boxscore", "box-score"}
    ]
    if parts:
        return parts[-1]
    raise ValueError(f"cannot extract a game ID from {url!r}")


def box_score_url(url: str) -> str:
    normalized = url.split("#", 1)[0].split("?", 1)[0].rstrip("/")
    if normalized.endswith("/boxscore"):
        normalized = normalized.removesuffix("/boxscore")
    return normalized if normalized.endswith("/box-score") else f"{normalized}/box-score"


def schedule_status_is_final(text: str) -> bool:
    return any(
        FINAL_STATUS_PATTERN.fullmatch(line.strip())
        for line in text.splitlines()
        if line.strip()
    )


class SeleniumWnbaSource:
    def __init__(
        self,
        *,
        headless: bool = True,
        chrome_binary: str | None = None,
        wait_seconds: int = 20,
    ) -> None:
        options = webdriver.ChromeOptions()
        options.page_load_strategy = "eager"
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1440,1200")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-sync")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--no-first-run")
        options.add_experimental_option(
            "prefs",
            {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
            },
        )
        if chrome_binary:
            options.binary_location = chrome_binary
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, wait_seconds)

    def discover_games(
        self,
        season: int,
        *,
        completed_only: bool = False,
    ) -> list[DiscoveredGame]:
        url = schedule_url(season)
        logger.info("opening schedule season=%s url=%s", season, url)
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": (
                    'try { localStorage.setItem("wnba_schedule_hide_prev_games", "false"); } '
                    "catch (error) {}"
                )
            },
        )
        self.driver.get(url)
        self.wait.until(ec.presence_of_element_located((By.TAG_NAME, "body")))
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        if "access denied" in f"{self.driver.title} {body_text}".casefold():
            raise RuntimeError(
                "WNBA schedule access was denied by the upstream web firewall; "
                "retry from a local network or run with --no-headless"
            )

        discovered: dict[str, str] = {}
        stable_rounds = 0
        previous_count = -1
        link_selector = ", ".join(SCHEDULE_GAME_LINK_SELECTORS)
        for _ in range(30):
            link_records = self.driver.execute_script(
                """
                return Array.from(document.querySelectorAll(arguments[0])).map((link) => {
                    const card = link.closest('[class*="GameTile__container"]');
                    return {
                        href: link.href || "",
                        cardText: card ? card.innerText : "",
                    };
                });
                """,
                link_selector,
            )
            for record in link_records or []:
                href = record.get("href") if isinstance(record, dict) else None
                card_text = record.get("cardText", "") if isinstance(record, dict) else ""
                if not isinstance(href, str) or not href:
                    continue
                if completed_only and (
                    not isinstance(card_text, str) or not schedule_status_is_final(card_text)
                ):
                    continue
                normalized_url = box_score_url(urljoin(url, href))
                try:
                    discovered[source_game_id(normalized_url)] = normalized_url
                except ValueError:
                    logger.debug("ignored non-game link href=%s", href)

            stable_rounds = stable_rounds + 1 if len(discovered) == previous_count else 0
            if stable_rounds >= 3:
                break
            previous_count = len(discovered)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.4)

        if not discovered:
            qualifier = " completed" if completed_only else ""
            raise RuntimeError(f"no{qualifier} game URLs discovered at {url}")
        logger.info(
            "discovered games season=%s count=%s completed_only=%s",
            season,
            len(discovered),
            completed_only,
        )
        return [
            DiscoveredGame(source_game_id=game_id, source_url=game_url)
            for game_id, game_url in sorted(discovered.items())
        ]

    def fetch_game(self, game: DiscoveredGame, season: int) -> IngestedGame:
        logger.info("opening box score game_id=%s url=%s", game.source_game_id, game.source_url)
        self.driver.get(game.source_url)
        self.wait.until(ec.presence_of_element_located((By.TAG_NAME, "body")))

        box_score_links = self.driver.find_elements(By.CSS_SELECTOR, "a#box-score")
        if box_score_links:
            resolved_url = box_score_links[0].get_attribute("href")
            if resolved_url and resolved_url != self.driver.current_url:
                logger.info(
                    "resolved current box-score route game_id=%s url=%s",
                    game.source_game_id,
                    resolved_url,
                )
                self.driver.get(resolved_url)

        try:
            self.wait.until(
                lambda driver: sum(
                    any(
                        cell.text.strip().upper() in {"PLAYER", "PLAYERS"}
                        for cell in table.find_elements(By.CSS_SELECTOR, "th, td")
                    )
                    for table in driver.find_elements(By.CSS_SELECTOR, "table")
                )
                >= 2
            )
        except TimeoutException as exc:
            raise RuntimeError(
                f"two player-stat tables not found url={self.driver.current_url}"
            ) from exc
        return parse_box_score(
            self.driver.page_source,
            source_url=self.driver.current_url,
            source_game_id=game.source_game_id,
            season=season,
        )

    def close(self) -> None:
        self.driver.quit()
