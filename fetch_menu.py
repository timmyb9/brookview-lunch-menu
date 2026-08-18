import requests
import json
from datetime import date, timedelta

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

# Items offered essentially every day that aren't worth calling out daily.
# Matched as a case-insensitive substring, so close variants still get caught.
EXCLUDED_ITEMS = [
    "sunbutter sandwich entree",
]

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

import re

KYDZABLE_PREFIX_RE = re.compile(r"^kydzable entree\s*w/\s*", re.IGNORECASE)

def split_entrees(items):
    """Separate the daily 'Kydzable' option from the main rotating entree(s).
    The 'Kydzable Entree w/' prefix is stripped since it's already called
    out by the section heading."""
    kydzable, main = [], []
    for i in items:
        if "kydzable" in i.lower():
            kydzable.append(KYDZABLE_PREFIX_RE.sub("", i).strip())
        else:
            main.append(i)
    return main, kydzable

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
        main_entrees, kydzable_entrees = [], []
        if day_json:
            for cat in CATEGORY_ORDER:
                if cat in EXCLUDED_CATEGORIES:
                    continue
                items = clean_items(day_json.get(cat, []))
                if not items:
                    continue
                if cat == "ENTREES":
                    main_entrees, kydzable_entrees = split_entrees(items)
                else:
                    categories[CATEGORY_LABELS[cat]] = items
        days.append({
            "date": d,
            "label": d.strftime("%A"),
            "date_str": d.strftime("%b %-d"),
            "main_entrees": main_entrees,
            "kydzable_entrees": kydzable_entrees,
            "categories": categories,
        })
    return days

if __name__ == "__main__":
    today = date.today()
    monday = get_monday(today)
    data = build_week_data(monday)
    for day in data:
        print(day["label"], day["date_str"])
        for cat, items in day["categories"].items():
            print("  ", cat, "->", items)
