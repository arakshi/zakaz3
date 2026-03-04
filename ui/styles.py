BASE_CSS = """
<style>
:root {
  --bg: #f3f5f9;
  --surface: #ffffff;
  --surface-soft: #f8fafc;
  --text: #111827;
  --muted: #4b5563;
  --border: #dbe1ea;
  --accent: #1d4ed8;
}

/* Базовый контраст */
html, body, .stApp {
  background: var(--bg) !important;
  color: var(--text) !important;
}

/* Принудительно делаем текст темным, чтобы не было белого на белом */
.stApp,
.stApp p,
.stApp span,
.stApp div,
.stApp label,
.stApp li,
.stMarkdown,
.stMarkdown p,
.stMarkdown span,
h1, h2, h3, h4, h5 {
  color: var(--text) !important;
}

small, .small-muted, .stCaption, .st-emotion-cache-16idsys p {
  color: var(--muted) !important;
}

/* Контейнеры Streamlit */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border);
}

[data-testid="stHeader"], [data-testid="stToolbar"] {
  background: transparent !important;
}

[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 8px 10px;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
  background: var(--surface) !important;
  border: 1px solid var(--border);
  border-radius: 10px;
}

/* Наши карточки */
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

/* Инпуты/селекты */
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div,
.stDateInput input,
.stNumberInput input {
  background: var(--surface) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}

.stButton > button,
.stDownloadButton > button {
  border-radius: 10px;
}
</style>
"""
