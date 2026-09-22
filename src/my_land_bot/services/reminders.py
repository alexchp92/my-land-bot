from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class ReminderPlan:
    kind: str
    due_date: date
    text: str


def plans_for_notice(deadline: date, today: date) -> list[ReminderPlan]:
    messages = {
        7: "До окончания приёма заявлений от заинтересованных лиц осталось 7 дней.",
        3: "До окончания приёма заявлений от заинтересованных лиц осталось 3 дня.",
        1: "Завтра заканчивается приём заявлений от заинтересованных лиц.",
        0: "Сегодня заканчивается приём заявлений. Проверьте статус в официальном источнике или администрации.",
        -2: "Срок приёма заявлений завершён. Уточните в администрации дальнейшее решение.",
    }
    offset = (deadline - today).days
    if offset not in messages:
        return []
    kind = "notice_followup" if offset == -2 else f"notice_{offset}d"
    return [ReminderPlan(kind, deadline, messages[offset])]


def plans_for_auction(
    application_deadline: date | None, auction_date: date | None, today: date
) -> list[ReminderPlan]:
    plans: list[ReminderPlan] = []
    if application_deadline:
        offset = (application_deadline - today).days
        texts = {
            7: "До окончания подачи заявки на аукцион осталось 7 дней.",
            3: "До окончания подачи заявки на аукцион осталось 3 дня.",
            1: "Завтра заканчивается подача заявки на аукцион.",
            0: "Сегодня заканчивается подача заявки на аукцион.",
        }
        if offset in texts:
            plans.append(
                ReminderPlan(f"auction_application_{offset}d", application_deadline, texts[offset])
            )
    if auction_date and auction_date - timedelta(days=1) == today:
        plans.append(
            ReminderPlan(
                "auction_tomorrow", auction_date, "Завтра состоится аукцион по вашему участку."
            )
        )
    return plans
