BASE_CSS = """
<style>
:root {
  --bg:#f6f8fb;
  --card:#ffffff;
  --text:#1f2937;
  --muted:#6b7280;
  --accent:#2563eb;
}
.stApp {background:var(--bg);}
h1,h2,h3 {color:var(--text);}
.card {background:var(--card); border:1px solid #e5e7eb; border-radius:14px; padding:16px; margin-bottom:12px; box-shadow:0 1px 2px rgba(0,0,0,.05)}
.badge {display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600;}
.badge-ok {background:#dcfce7;color:#166534}
.badge-wip {background:#dbeafe;color:#1e40af}
.badge-warn {background:#fee2e2;color:#991b1b}
.small-muted{color:var(--muted);font-size:12px}
</style>
"""
