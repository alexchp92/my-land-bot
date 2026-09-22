from datetime import date

from my_land_bot.services.reminders import plans_for_auction, plans_for_notice


def test_notice_reminder_is_created_seven_days_before_deadline() -> None:
    plans = plans_for_notice(date(2026, 10, 10), date(2026, 10, 3))
    assert len(plans) == 1
    assert plans[0].kind == "notice_7d"


def test_notice_has_no_reminder_on_irrelevant_day() -> None:
    assert plans_for_notice(date(2026, 10, 10), date(2026, 10, 4)) == []


def test_auction_reminds_on_day_before_auction() -> None:
    plans = plans_for_auction(None, date(2026, 10, 10), date(2026, 10, 9))
    assert plans[0].kind == "auction_tomorrow"
