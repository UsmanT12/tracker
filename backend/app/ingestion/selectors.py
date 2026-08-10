SCHEDULE_GAME_LINK_SELECTORS = (
    'a[href*="/game/"][href*="wnba"]',
    'a[href*="/game/"]',
    'a[href*="/boxscore"]',
)

BOX_SCORE_TABLE_SELECTORS = (
    'table[aria-label*="Box Score"]',
    'table[class*="BoxScore"]',
    "table",
)

TEAM_NAME_SELECTORS = (
    '[data-testid*="team-name"]',
    '[class*="TeamName__name"]',
    "h2",
)

GAME_DATE_SELECTORS = (
    "time[datetime]",
    '[data-testid*="game-date"]',
    '[class*="GameStatusExpanded__date"]',
)

