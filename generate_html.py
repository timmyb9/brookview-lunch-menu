from datetime import date, timedelta
from datetime import datetime
from zoneinfo import ZoneInfo
from fetch_menu import build_week_data, get_monday

CENTRAL = ZoneInfo("America/Chicago")

def today_central():
    """GitHub Actions runners are UTC -- always compute 'today' explicitly
    in Central time so the highlighted day and week rollover are correct
    regardless of when in the UTC day the job runs."""
    return datetime.now(CENTRAL).date()

# --- Design tokens -----------------------------------------------------
# Palette: bright, candy-ish, but kept to a tight set so it doesn't turn
# into confetti. One accent per weekday, everything else neutral.
DAY_COLORS = {
    "Monday":    {"bg": "#FFE8A3", "accent": "#F2A93B", "text": "#4A3200"},
    "Tuesday":   {"bg": "#FFD1E3", "accent": "#F2568D", "text": "#5C0F2E"},
    "Wednesday": {"bg": "#C9F2E0", "accent": "#2FB88A", "text": "#0B4A36"},
    "Thursday":  {"bg": "#D6E4FF", "accent": "#4C7DF2", "text": "#122B5C"},
    "Friday":    {"bg": "#F0DBFF", "accent": "#9B5DE5", "text": "#3A1259"},
}

CAT_ICON = {
    "Grains": "\U0001F35E",
    "Vegetables": "\U0001F966",
    "Fruit": "\U0001F353",
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="3600">
<title>Brookview Lunch Menu</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;800&family=Nunito:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0;
    padding: 0;
    background: #FFFBF3;
    font-family: 'Nunito', sans-serif;
  }}
  .wrap {{
    padding: 22px 26px 18px 26px;
  }}
  .header {{
    display: flex;
    align-items: baseline;
    gap: 14px;
    margin-bottom: 4px;
  }}
  h1 {{
    font-family: 'Baloo 2', sans-serif;
    font-weight: 800;
    font-size: 30px;
    margin: 0;
    color: #3A2145;
  }}
  .header .wave {{
    font-size: 26px;
  }}
  .subtitle {{
    font-size: 14px;
    font-weight: 700;
    color: #A8944F;
    margin: 0 0 16px 0;
  }}
  .week {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .day {{
    flex: 1 1 0;
    min-width: 168px;
    border-radius: 20px;
    padding: 14px 14px 16px 14px;
    position: relative;
    box-shadow: 0 3px 0 rgba(0,0,0,0.06);
  }}
  .day.today {{
    outline: 3px solid #3A2145;
    outline-offset: 2px;
  }}
  .today-flag {{
    position: absolute;
    top: -12px;
    right: 10px;
    background: #3A2145;
    color: #FFF9E8;
    font-family: 'Baloo 2', sans-serif;
    font-size: 11px;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 999px;
    letter-spacing: 0.5px;
  }}
  .day-name {{
    font-family: 'Baloo 2', sans-serif;
    font-weight: 800;
    font-size: 19px;
    margin-bottom: 0px;
  }}
  .day-date {{
    font-size: 11px;
    font-weight: 700;
    opacity: 0.65;
    margin-bottom: 10px;
  }}
  .entree-main {{
    background: rgba(255,255,255,0.72);
    border-radius: 12px;
    padding: 8px 10px;
    margin-bottom: 8px;
  }}
  .entree-label {{
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    opacity: 0.6;
    margin-bottom: 2px;
  }}
  .entree-name {{
    font-size: 14.5px;
    font-weight: 800;
    line-height: 1.25;
  }}
  .kydzable {{
    background: rgba(255,255,255,0.55);
    border: 2px dashed var(--accent);
    border-radius: 12px;
    padding: 6px 10px;
    margin-bottom: 10px;
  }}
  .kydzable .entree-label {{
    opacity: 0.8;
    color: inherit;
  }}
  .kydzable .entree-name {{
    font-size: 13px;
    font-weight: 700;
    opacity: 0.9;
  }}
  .side-row {{
    font-size: 12px;
    font-weight: 700;
    margin-top: 6px;
    display: flex;
    gap: 5px;
    align-items: flex-start;
  }}
  .side-icon {{
    font-size: 13px;
  }}
  .no-menu {{
    font-size: 13px;
    font-weight: 700;
    opacity: 0.5;
    font-style: italic;
    padding-top: 6px;
  }}
  .footer {{
    margin-top: 14px;
    font-size: 10.5px;
    font-weight: 700;
    color: #C9BB8E;
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>What's for Lunch?</h1>
    <span class="wave">&#127829;</span>
  </div>
  <div class="subtitle">Brookview Elementary &middot; Week of {week_label}</div>
  <div class="week">
    {days_html}
  </div>
  <div class="footer">Updated {updated}</div>
</div>
</body>
</html>
"""

DAY_TEMPLATE = """
<div class="day{today_class}" style="background:{bg}; color:{text}; --accent:{accent};">
  {today_flag}
  <div class="day-name">{label}</div>
  <div class="day-date">{date_str}</div>
  {content}
</div>
"""

def render_day(day, today, colors):
    is_today = day["date"] == today
    c = colors[day["label"]]

    if not day["main_entrees"] and not day["kydzable_entrees"] and not day["categories"]:
        content = '<div class="no-menu">No menu yet</div>'
    else:
        parts = []
        for entree in day["main_entrees"]:
            parts.append(
                f'<div class="entree-main"><div class="entree-label">Today\'s Lunch</div>'
                f'<div class="entree-name">{entree}</div></div>'
            )
        for entree in day["kydzable_entrees"]:
            parts.append(
                f'<div class="kydzable"><div class="entree-label">\u2b50 Kydzable</div>'
                f'<div class="entree-name">{entree}</div></div>'
            )
        for cat, items in day["categories"].items():
            icon = CAT_ICON.get(cat, "")
            parts.append(
                f'<div class="side-row"><span class="side-icon">{icon}</span>'
                f'<span>{", ".join(items)}</span></div>'
            )
        content = "".join(parts)

    return DAY_TEMPLATE.format(
        today_class=" today" if is_today else "",
        today_flag='<div class="today-flag">TODAY</div>' if is_today else "",
        bg=c["bg"],
        text=c["text"],
        accent=c["accent"],
        label=day["label"],
        date_str=day["date_str"],
        content=content,
    )

def generate(output_path="index.html"):
    today = today_central()
    monday = get_monday(today)
    # If it's the weekend, show next week instead of a stale past week
    if today.weekday() >= 5:
        monday = monday + timedelta(weeks=1)
    days = build_week_data(monday)
    days_html = "".join(render_day(d, today, DAY_COLORS) for d in days)
    week_label = f'{monday.strftime("%b %-d")} - {(monday + timedelta(days=4)).strftime("%b %-d, %Y")}'
    html = HTML_TEMPLATE.format(
        week_label=week_label,
        days_html=days_html,
        updated=today.strftime("%B %-d, %Y"),
    )
    with open(output_path, "w") as f:
        f.write(html)
    print(f"Wrote {output_path}")

if __name__ == "__main__":
    generate()
