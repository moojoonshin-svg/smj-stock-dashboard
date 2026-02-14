import csv
import json
import os
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener, urlopen

from flask import Flask, redirect, render_template_string, request, url_for

from todo import add_item, load_items, remove_item, toggle_done


app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
STOCKS_PATH = BASE_DIR / "stocks.json"
STARTUP_REFRESH_DONE = False


def _clear_broken_proxy_env():
    keys = [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "GIT_HTTP_PROXY",
        "GIT_HTTPS_PROXY",
    ]
    for key in keys:
        value = os.environ.get(key, "")
        if "127.0.0.1:9" in value or "localhost:9" in value:
            os.environ.pop(key, None)


_clear_broken_proxy_env()


PAGE = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TODO Dashboard</title>
  <style>
    :root {
      --card: #ffffff;
      --line: #d9dfeb;
      --text: #192230;
      --muted: #6b7585;
      --accent: #1f6feb;
      --danger: #d12f2f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: linear-gradient(160deg, #eef3ff 0%, #f7f9fc 45%, #f2f4f8 100%);
      color: var(--text);
      font-family: "Segoe UI", "Noto Sans KR", sans-serif;
    }
    .wrap {
      max-width: 900px;
      margin: 40px auto;
      padding: 0 16px;
      display: grid;
      gap: 16px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 6px 20px rgba(20, 40, 80, 0.08);
    }
    h1 {
      margin: 0 0 14px;
      font-size: 28px;
    }
    .sub {
      margin: 0 0 12px;
      color: var(--muted);
      font-size: 14px;
    }
    .error {
      color: var(--danger);
      font-size: 14px;
      margin-top: 10px;
    }
    .chart-wrap {
      height: 420px;
    }
    .range-form {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
    }
    .tooltip-mode {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      color: var(--muted);
      font-size: 14px;
    }
    .range-form input[type="number"] {
      width: 96px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 14px;
    }
    .stock-form {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
    }
    .stock-form input[type="text"] {
      width: 140px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 14px;
      text-transform: uppercase;
    }
    .chip-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      background: #f8fafe;
      font-size: 13px;
    }
    .chip button {
      padding: 4px 8px;
      font-size: 12px;
      border-radius: 999px;
      background: var(--danger);
    }
    .add-form {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
    }
    .add-form input[type="text"] {
      flex: 1;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 15px;
    }
    button {
      border: 0;
      border-radius: 8px;
      padding: 10px 14px;
      font-size: 14px;
      cursor: pointer;
      background: var(--accent);
      color: #fff;
    }
    ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    li {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 10px 0;
      border-top: 1px solid var(--line);
    }
    .left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }
    .text {
      word-break: break-word;
    }
    .done .text {
      color: var(--muted);
      text-decoration: line-through;
    }
    .inline {
      margin: 0;
    }
    .delete-btn {
      background: var(--danger);
    }
    .empty {
      padding: 16px 0 6px;
      color: var(--muted);
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>TODO</h1>
      <form class="add-form" action="{{ url_for('add') }}" method="post">
        <input type="text" name="text" placeholder="할 일을 입력하세요" required>
        <input type="hidden" name="days" value="{{ days }}">
        <button type="submit">추가</button>
      </form>

      {% if items %}
      <ul>
        {% for i, item in items %}
        <li class="{% if item.done %}done{% endif %}">
          <div class="left">
            <form class="inline" action="{{ url_for('toggle', index=i) }}" method="post">
              <input type="hidden" name="days" value="{{ days }}">
              <input type="checkbox" {% if item.done %}checked{% endif %} onchange="this.form.submit()">
            </form>
            <span class="text">{{ item.text }}</span>
          </div>
          <form class="inline" action="{{ url_for('delete', index=i) }}" method="post">
            <input type="hidden" name="days" value="{{ days }}">
            <button class="delete-btn" type="submit">삭제</button>
          </form>
        </li>
        {% endfor %}
      </ul>
      {% else %}
      <p class="empty">할 일이 없습니다.</p>
      {% endif %}
    </div>

    <div class="card">
      <h1>Stock Dashboard</h1>
      <p class="sub">{{ symbols_text }} recent {{ days }} trading days normalized (start=1.0)</p>
      <form class="stock-form" method="post" action="{{ url_for('add_stock') }}">
        <input type="text" name="symbol" placeholder="Ticker (e.g. SCHG)" required>
        <input type="hidden" name="days" value="{{ days }}">
        <button type="submit">Add Symbol</button>
      </form>
      {% if symbols %}
      <div class="chip-list">
        {% for symbol in symbols %}
        <form class="chip" method="post" action="{{ url_for('delete_stock', symbol=symbol) }}">
          <span>{{ symbol }}</span>
          <input type="hidden" name="days" value="{{ days }}">
          <button type="submit">x</button>
        </form>
        {% endfor %}
      </div>
      {% endif %}
      <form class="range-form" method="get" action="{{ url_for('index') }}">
        <label for="days">Days</label>
        <input id="days" type="number" name="days" min="2" max="180" value="{{ days }}" required>
        <input type="hidden" name="refresh" value="1">
        <button type="submit">Refresh</button>
      </form>
      <label class="tooltip-mode" for="tooltipAll">
        <input id="tooltipAll" type="checkbox" checked>
        Show all symbols in tooltip
      </label>
      <div class="chart-wrap">
        <canvas id="stockChart"></canvas>
      </div>
      {% if updated_at %}
      <p class="sub">Updated (UTC): {{ updated_at }}</p>
      {% endif %}
      {% if fetch_error %}
      <p class="error">{{ fetch_error }}</p>
      {% endif %}
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <script>
    const series = {{ stock_series | tojson }};
    const labels = series.length ? series[0].prices.map(p => p.date) : [];
    const colors = ["#1f6feb", "#d12f2f", "#0f9d58", "#ff9800"];

    const datasets = series.map((s, i) => {
      const base = s.prices.length ? Number(s.prices[0].close) : 1;
      const normalized = s.prices.map(p => {
        const close = Number(p.close);
        if (!base || Number.isNaN(close)) return null;
        return Number((close / base).toFixed(4));
      });
      return {
        label: `${s.symbol} (${s.source})`,
        data: normalized,
        actualPrices: s.prices.map(p => Number(p.close)),
        borderColor: colors[i % colors.length],
        backgroundColor: colors[i % colors.length],
        borderWidth: 2,
        tension: 0.25,
        pointRadius: 3,
        fill: false
      };
    });

    const stockChart = new Chart(document.getElementById("stockChart"), {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                const symbol = context.dataset.label;
                const normalized = context.parsed.y;
                const actual = context.dataset.actualPrices?.[context.dataIndex];
                const normText = normalized == null ? "-" : normalized.toFixed(4);
                const actualText = actual == null ? "-" : actual.toFixed(2);
                return `${symbol} | norm: ${normText}, close: $${actualText}`;
              }
            }
          }
        },
        scales: {
          y: { title: { display: true, text: "Normalized (start=1.0)" } },
          x: { title: { display: true, text: "Date" } }
        }
      }
    });

    const tooltipAllCheckbox = document.getElementById("tooltipAll");
    tooltipAllCheckbox.addEventListener("change", function() {
      const showAll = tooltipAllCheckbox.checked;
      stockChart.options.interaction.mode = showAll ? "index" : "nearest";
      stockChart.options.plugins.tooltip.mode = showAll ? "index" : "nearest";
      stockChart.options.plugins.tooltip.intersect = !showAll;
      stockChart.update();
    });
  </script>
</body>
</html>
"""


def _normalize_days(raw_days, default=7):
    try:
        days = int(raw_days)
    except (TypeError, ValueError):
        days = default
    return max(2, min(days, 180))


def load_stock_config():
    default_config = {
        "symbols": [],
        "refresh_days": 7,
        "updated_at": "",
        "series": [],
    }
    if not STOCKS_PATH.exists():
        return default_config

    raw_text = STOCKS_PATH.read_text(encoding="utf-8")
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        sanitized = re.sub(r",\s*([}\]])", r"\1", raw_text)
        try:
            data = json.loads(sanitized)
        except json.JSONDecodeError:
            return default_config

    if isinstance(data, list):
        symbols = data
        refresh_days = 7
        updated_at = ""
        series = []
    elif isinstance(data, dict):
        symbols = data.get("symbols", [])
        refresh_days = _normalize_days(data.get("refresh_days", 7), 7)
        updated_at = data.get("updated_at", "")
        series = data.get("series", [])
    else:
        return default_config

    clean = []
    for symbol in symbols:
        if isinstance(symbol, str):
            s = symbol.strip().upper()
            if s:
                clean.append(s)
    if not isinstance(series, list):
        series = []
    if not isinstance(updated_at, str):
        updated_at = ""
    return {
        "symbols": clean,
        "refresh_days": refresh_days,
        "updated_at": updated_at,
        "series": series,
    }


def save_stock_config(config):
    payload = {
        "symbols": config.get("symbols", []),
        "refresh_days": _normalize_days(config.get("refresh_days", 7), 7),
        "updated_at": config.get("updated_at", ""),
        "series": config.get("series", []),
    }
    STOCKS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _http_get_text(url):
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0 Safari/537.36"
            )
        },
    )
    try:
        with urlopen(req, timeout=8) as resp:
            return resp.read().decode("utf-8")
    except URLError:
        # Some environments inject broken local proxy variables
        # (e.g. 127.0.0.1:9). Retry once with proxies disabled.
        opener = build_opener(ProxyHandler({}))
        with opener.open(req, timeout=8) as resp:
            return resp.read().decode("utf-8")


def _yahoo_range_for_days(days):
    if days <= 22:
        return "1mo"
    if days <= 66:
        return "3mo"
    if days <= 132:
        return "6mo"
    return "1y"


def fetch_from_yahoo(symbol, days):
    data_range = _yahoo_range_for_days(days)
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?range={data_range}&interval=1d&includePrePost=false&events=div%2Csplit"
    )
    try:
        raw = _http_get_text(url)
        data = json.loads(raw)
        result = data["chart"]["result"][0]
        timestamps = result.get("timestamp") or []
        closes = result["indicators"]["quote"][0].get("close") or []
    except (KeyError, IndexError, TypeError, ValueError, URLError):
        return None

    points = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
        points.append({"date": day, "close": round(float(close), 2)})

    if len(points) < days:
        return None

    return {"symbol": symbol, "source": "Yahoo", "prices": points[-days:]}


def fetch_from_stooq(symbol, days):
    # Stooq symbol format for US stocks: nvda.us, ionq.us
    stooq_symbol = f"{symbol.lower()}.us"
    url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"
    try:
        raw = _http_get_text(url)
        reader = csv.DictReader(StringIO(raw))
    except URLError:
        return None

    points = []
    for row in reader:
        date = row.get("Date")
        close = row.get("Close")
        if not date or not close or close == "0":
            continue
        try:
            points.append({"date": date, "close": round(float(close), 2)})
        except ValueError:
            continue

    if len(points) < days:
        return None

    return {"symbol": symbol, "source": "Stooq", "prices": points[-days:]}


def fetch_recent_prices(symbols, days):
    series = []
    failed = []
    for symbol in symbols:
        data = fetch_from_yahoo(symbol, days)
        if data is None:
            data = fetch_from_stooq(symbol, days)
        if data is None:
            failed.append(symbol)
            continue
        series.append(data)
    return series, failed


@app.get("/")
def index():
    global STARTUP_REFRESH_DONE
    items = list(enumerate(load_items(), start=1))
    config = load_stock_config()
    symbols = config["symbols"]
    requested_days = _normalize_days(
        request.args.get("days", config["refresh_days"]),
        config["refresh_days"],
    )
    refresh_requested = request.args.get("refresh") == "1"
    cached_symbols = [
        s.get("symbol") for s in config.get("series", []) if isinstance(s, dict)
    ]
    symbols_changed = sorted(cached_symbols) != sorted(symbols)
    should_refresh = (
        refresh_requested
        or not STARTUP_REFRESH_DONE
        or not config.get("series")
        or symbols_changed
    )

    failed = []
    if should_refresh:
        stock_series, failed = fetch_recent_prices(symbols, requested_days)
        if stock_series:
            config["series"] = stock_series
            config["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        config["refresh_days"] = requested_days
        save_stock_config(config)
        STARTUP_REFRESH_DONE = True
    else:
        stock_series = config.get("series", [])

    days = config.get("refresh_days", 7)
    fetch_error = ""
    if failed:
        fetch_error = "Failed to fetch: " + ", ".join(failed)
    return render_template_string(
        PAGE,
        items=items,
        stock_series=stock_series,
        updated_at=config.get("updated_at", ""),
        symbols_text=", ".join(symbols) if symbols else "No symbols",
        symbols=symbols,
        days=days,
        fetch_error=fetch_error,
    )


@app.post("/add")
def add():
    text = request.form.get("text", "").strip()
    days = _normalize_days(request.form.get("days", "7"), 7)
    if text:
        add_item(text)
    return redirect(url_for("index", days=days))


@app.post("/toggle/<int:index>")
def toggle(index):
    days = _normalize_days(request.form.get("days", "7"), 7)
    toggle_done(index)
    return redirect(url_for("index", days=days))


@app.post("/delete/<int:index>")
def delete(index):
    days = _normalize_days(request.form.get("days", "7"), 7)
    remove_item(index)
    return redirect(url_for("index", days=days))


@app.post("/stocks/add")
def add_stock():
    symbol = request.form.get("symbol", "").strip().upper()
    days = _normalize_days(request.form.get("days", "7"), 7)
    if not symbol or not re.fullmatch(r"[A-Z0-9.\-^]{1,12}", symbol):
        return redirect(url_for("index", days=days))

    config = load_stock_config()
    symbols = config.get("symbols", [])
    if symbol not in symbols:
        symbols.append(symbol)
        config["symbols"] = symbols
        save_stock_config(config)
    return redirect(url_for("index", days=days, refresh=1))


@app.post("/stocks/delete/<symbol>")
def delete_stock(symbol):
    days = _normalize_days(request.form.get("days", "7"), 7)
    target = (symbol or "").strip().upper()
    config = load_stock_config()
    symbols = [s for s in config.get("symbols", []) if s != target]
    config["symbols"] = symbols
    save_stock_config(config)
    return redirect(url_for("index", days=days, refresh=1))


if __name__ == "__main__":
    app.run(debug=True)
