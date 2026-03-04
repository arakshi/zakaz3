BASE_CSS = """
<style>
:root {
  --bg: #f3f5f9;
  --surface: #ffffff;
  --surface-soft: #f8fafc;
  --text: #0f172a;
  --muted: #475569;
  --border: #dbe1ea;
  --accent: #1d4ed8;
}

html, body, .stApp, [data-testid="stAppViewContainer"], .main {
  background: var(--bg) !important;
  color: var(--text) !important;
}

/* Безопасный контраст текста */
.stApp p,
.stApp span,
.stApp label,
.stMarkdown p,
.stMarkdown span,
h1, h2, h3, h4, h5 {
  color: var(--text) !important;
}

small, .small-muted, .stCaption {
  color: var(--muted) !important;
}

/* Основные области */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  color: var(--text) !important;
  border-right: 1px solid var(--border);
}

section[data-testid="stSidebar"] * {
  color: var(--text) !important;
}

[data-testid="stHeader"],
[data-testid="stToolbar"] {
  background: transparent !important;
}

[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 8px 10px;
}

[data-testid="stDataFrame"],
[data-testid="stTable"],
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border);
  border-radius: 10px;
}

/* карточки */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .06);
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.badge-ok { background: #dcfce7; color: #166534 !important; }
.badge-wip { background: #dbeafe; color: #1e40af !important; }
.badge-warn { background: #fee2e2; color: #991b1b !important; }
.small-muted { color: var(--muted) !important; font-size: 12px; }

/* Формы */
.stTextInput input,
.stTextArea textarea,
.stDateInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div {
  background: var(--surface) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}

/* Выпадающие меню BaseWeb */
div[role="listbox"],
li[role="option"],
ul[role="listbox"] {
  background: var(--surface) !important;
  color: var(--text) !important;
}

/* Кнопки */
.stButton > button,
.stDownloadButton > button {
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
}

.stButton > button[kind="primary"] {
  background: var(--accent) !important;
  color: #ffffff !important;
  border-color: var(--accent) !important;
}
</style>
"""
