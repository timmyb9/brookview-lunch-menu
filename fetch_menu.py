import requests
import json
from datetime import date, timedelta
import re

SCHOOL_ID = "78d53de7-47aa-4048-9069-6652df5e3549"  # Brookview Elementary, Waukee CSD
SERVING_LINE = "ELEM LUNCH"
MEAL_TYPE = "Lunch"

def get_monday(d):
    return d - timedelta(days=d.weekday())

def fetch_week(monday):
    url = "https://webapis.schoolcafe.com/api/CalendarView/GetWeeklyMenuitems"
    params = {
        "SchoolId": SCHOOL_ID,
        "ServingDate": monday.strftime("%m/%d/%Y"),
        "ServingLine": SERVING_LINE,
        "MealType": MEAL_TYPE,
        "enabledWeekendMenus": "false",
    }
    r = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=15)
    r.raise_for_status()
    return r.json()

CATEGORY_ORDER = ["ENTREES", "GRAINS", "VEGETABLES", "FRUITS", "DAIRY", "CONDIMENTS"]
CATEGORY_LABELS = {
    "ENTREES": "Entrees",
    "GRAINS": "Grains",
    "VEGETABLES": "Vegetables",
    "FRUITS": "Fruit",
    "DAIRY": "Milk",
    "CONDIMENTS": "Condiments",
}

# Categories we never want to show on the board
EXCLUDED_CATEGORIES = {"DAIRY", "CONDIMENTS"}

# Sunbutter is a standing daily backup — never worth calling out.
EXCLUDED_ITEMS = [
    "sunbutter sandwich entree",
]

# Items that SchoolCafe's feed sometimes mislabels "Kydzable" but are
# really just the standing daily "Cold Entree Option" per the district's
# own printed menu (only Tue/Wed that week were genuinely Kydzable-branded).
# Matched as a case-insensitive substring. Grow this list as new standing
# items are spotted in future weeks.
COLD_ENTREE_ITEMS = [
    "hardboiled egg, cheese stick, & muffin top variety",
    "italian deli sub sandwich",
]

KYDZABLE_PREFIX_RE = re.compile(r"^kydzable entree\s*w/\s*", re.IGNORECASE)

def clean_items(items):
    names = []
    for i in items:
        desc = (i.get("MenuItemDescription") or "").strip()
        if not desc or "not been published" in desc.lower():
            continue
        if any(ex in desc.lower() for ex in EXCLUDED_ITEMS):
            continue
        names.append(desc)
    return names

def split_entrees(items):
    """Split into three groups: the main rotating hot lunch entree(s),
    genuine daily Kydzable specials, and the standing 'Cold Entree
    Option' (same item most days, occasionally mislabeled 'Kydzable' by
    the feed). The 'Kydzable Entree w/' prefix is stripped from Kydzable
    items since it's already called out by the section heading."""
    kydzable, cold, main = [], [], []
    for i in items:
        stripped = KYDZABLE_PREFIX_RE.sub("", i).strip()
        if any(ce in i.lower() for ce in COLD_ENTREE_ITEMS):
            cold.append(stripped)
        elif "kydzable" in i.lower():
            kydzable.append(stripped)
        else:
            main.append(i)
    return main, kydzable, cold

def build_week_data(monday):
    raw = fetch_week(monday)
    days = []
    for i in range(5):  # Mon-Fri
        d = monday + timedelta(days=i)
        key_variants = [f"{d.month}/{d.day}/{d.year}", d.strftime("%-m/%-d/%Y")]
        day_json = None
        for k in key_variants:
            if k in raw:
                day_json = raw[k]
                break
        if day_json is None:
            for k, v in raw.items():
                # fallback: match by parsing
                try:
                    m, dd, y = k.split("/")
                    if int(m) == d.month and int(dd) == d.day and int(y) == d.year:
                        day_json = v
                        break
                except ValueError:
                    pass
        categories = {}
        main_entrees, kydzable_entrees, cold_entrees = [], [], []
        if day_json:
            for cat in CATEGORY_ORDER:
                if cat in EXCLUDED_CATEGORIES:
                    continue
                items = clean_items(day_json.get(cat, []))
                if not items:
                    continue
                if cat == "ENTREES":
                    main_entrees, kydzable_entrees, cold_entrees = split_entrees(items)
                else:
                    categories[CATEGORY_LABELS[cat]] = items
        days.append({
            "date": d,
            "label": d.strftime("%A"),
            "date_str": d.strftime("%b %-d"),
            "main_entrees": main_entrees,
            "kydzable_entrees": kydzable_entrees,
            "cold_entrees": cold_entrees,
            "categories": categories,
        })
    return days

if __name__ == "__main__":
    today = date.today()
    monday = get_monday(today)
    data = build_week_data(monday)
    for day in data:
        print(day["label"], day["date_str"])
        print("  entrees:", day["main_entrees"])
        print("  kydzable:", day["kydzable_entrees"])
        for cat, items in day["categories"].items():
            print("  ", cat, "->", items)
