# NSE Swing Scanner - Golden Cross + SMA, Momentum, Volume, Returns & Interactive HTML
# Author: Aryashree Pritikrishna
# Date: 2 October 2025
# Usage: python nse_golden_cross.py day|weekly|monthly [--index-scope 50|100|200|500]

import yfinance as yf
import pandas as pd
import requests
import io
import os
import argparse
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result
import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import time

# Use Agg backend for matplotlib
import matplotlib
matplotlib.use('Agg')

# -----------------------------
# Retry Utility
# -----------------------------
def is_falsey_series(value):
    return value is None or (isinstance(value, pd.DataFrame) and value.empty)

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=5, max=10),
        retry=retry_if_result(is_falsey_series))
def download_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True, timeout=30)
        if not df.empty:
            return df
    except Exception:
        time.sleep(1)
        return pd.DataFrame()
    return pd.DataFrame()

# -----------------------------
# Get NSE tickers
# -----------------------------
def get_nifty_tickers(scope):
    index_name = f"nifty{scope}list"
    local_file = f'ind_{index_name}.csv'
    
    def load_and_filter(df):
        valid_tickers = [s for s in df['Symbol'].tolist() if not pd.isna(s) and isinstance(s, str) and 'DUMMY' not in s.upper()]
        return [f"{s}.NS" for s in valid_tickers]

    if os.path.exists(local_file):
        try:
            df = pd.read_csv(local_file)
            return load_and_filter(df)
        except:
            pass

    url = f"https://nsearchives.nseindia.com/content/indices/ind_{index_name}.csv"
    print(f"Attempting to download Nifty {scope} list from: {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(local_file, 'w', encoding='utf-8') as f:
            f.write(resp.text)
        df = pd.read_csv(io.StringIO(resp.text))
        return load_and_filter(df)
    except Exception as e:
        print(f"Error downloading Nifty {scope} list: {e}")
        return []

# -----------------------------
# Stock Analysis
# -----------------------------
def analyze_stock(data):
    if data.empty or len(data) < 200:
        return None

    data["SMA_20"] = data["Close"].rolling(20).mean()
    data["SMA_50"] = data["Close"].rolling(50).mean()
    data["SMA_100"] = data["Close"].rolling(100).mean()
    data["SMA_200"] = data["Close"].rolling(200).mean()
    data["Momentum_20"] = (data["Close"] / data["Close"].shift(20) - 1) * 100
    data["Momentum_50"] = (data["Close"] / data["Close"].shift(50) - 1) * 100
    data["Volume_MA_20"] = data["Volume"].rolling(20).mean()

    latest = data.iloc[-1]
    prev = data.iloc[-2] if len(data) >= 2 else latest

    if any([pd.isna(latest["SMA_50"]).item(), pd.isna(latest["SMA_200"]).item(),
             pd.isna(latest["Momentum_20"]).item(), pd.isna(latest["Volume_MA_20"]).item()]):
        return None
    if any([pd.isna(prev["SMA_50"]).item(), pd.isna(prev["SMA_200"]).item()]):
        return None

    l_close = latest["Close"].item()
    l_sma20 = latest["SMA_20"].item()
    l_sma50 = latest["SMA_50"].item()
    l_sma100 = latest["SMA_100"].item()
    l_sma200 = latest["SMA_200"].item()
    l_mom20 = latest["Momentum_20"].item()
    l_mom50 = latest["Momentum_50"].item()
    l_vol20 = latest["Volume_MA_20"].item()
    p_sma50 = prev["SMA_50"].item()
    p_sma200 = prev["SMA_200"].item()
    p_vol20 = data["Volume_MA_20"].shift(1).iloc[-1] if not pd.isna(data["Volume_MA_20"].shift(1).iloc[-1]) else l_vol20

    golden_cross = (l_sma50 > l_sma200) and (p_sma50 <= p_sma200)
    SMA_50_above_200 = l_sma50 > l_sma200
    SMA_20_above_50 = l_sma20 > l_sma50
    SMA_50_above_100 = l_sma50 > l_sma100
    SMA_20_above_200 = l_sma20 > l_sma200
    volume_uptrend = l_vol20 > p_vol20
    uptrend = l_close > l_sma200
    momentum_valid = l_mom20 > 5
    perfect_setup = all([golden_cross, SMA_20_above_50, uptrend, momentum_valid, volume_uptrend])

    return {
        "Price": l_close, "SMA_20": l_sma20, "SMA_50": l_sma50, "SMA_100": l_sma100, "SMA_200": l_sma200,
        "Momentum_20": l_mom20, "Momentum_50": l_mom50, "Volume_Uptrend": volume_uptrend,
        "Golden_Cross": golden_cross, "SMA_50_above_200": SMA_50_above_200, "SMA_20_above_50": SMA_20_above_50,
        "SMA_50_above_100": SMA_50_above_100, "SMA_20_above_200": SMA_20_above_200,
        "Perfect_Setup": perfect_setup, "CloseSeries": data["Close"].iloc[-180:].values.tolist()
    }

# -----------------------------
# Compute Returns
# -----------------------------
def compute_returns(price_series, benchmark_series):
    price_series = np.array(price_series)
    benchmark_series = np.array(benchmark_series)

    def pct_change_safe(series, days):
        if len(series) < days:
            return np.nan
        try:
            current_price = series[-1].item()
            past_price = series[-days].item()
        except (ValueError, TypeError, IndexError):
            return np.nan
        if past_price == 0:
            return np.nan
        return (current_price / past_price - 1) * 100

    abs_30 = pct_change_safe(price_series,30)
    abs_90 = pct_change_safe(price_series,90)
    abs_180 = pct_change_safe(price_series,180)
    bench_30 = pct_change_safe(benchmark_series,30)
    bench_90 = pct_change_safe(benchmark_series,90)
    bench_180 = pct_change_safe(benchmark_series,180)

    rel_30 = abs_30 - bench_30
    rel_90 = abs_90 - bench_90
    rel_180 = abs_180 - bench_180
    
    return abs_30, abs_90, abs_180, rel_30, rel_90, rel_180

# -----------------------------
# Sparkline Generator
# -----------------------------
def sparkline(data):
    fig, ax = plt.subplots(figsize=(2,0.5))
    ax.plot(data, color="blue")
    ax.axis('off')
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=70, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return f'<img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode("utf-8")}" alt="Sparkline">'

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan Nifty stocks for Golden Cross")
    parser.add_argument("timeframe", choices=["day","weekly","monthly"], help="Timeframe to scan")
    parser.add_argument("--index-scope", type=int, choices=[50, 100, 200, 500], default=500, 
                        help="Nifty index scope (50, 100, 200, or 500). Defaults to 500.")
    args = parser.parse_args()
    timeframe = args.timeframe
    index_scope = args.index_scope

    interval_map = {"day":"1d", "weekly":"1wk", "monthly":"1mo"}
    period_map = {"day":"1y", "weekly":"5y", "monthly":"10y"}

    tickers = get_nifty_tickers(index_scope)
    if not tickers:
        print("❌ No tickers found.")
        exit()

    print(f"Scanning Nifty {index_scope} for Golden Cross ({timeframe})...")
    results = []

    bench_data = download_data("^NSEI", period_map[timeframe], interval_map[timeframe])
    bench_close = bench_data["Close"].values.tolist() if not bench_data.empty else []

    for ticker in tqdm(tickers, desc="Scanning stocks"):
        data = download_data(ticker, period=period_map[timeframe], interval=interval_map[timeframe])
        analysis = analyze_stock(data)
        if analysis and bench_close:
            abs_30, abs_90, abs_180, rel_30, rel_90, rel_180 = compute_returns(analysis["CloseSeries"], bench_close)
            analysis.update({
                "Abs_30d": abs_30, "Abs_90d": abs_90, "Abs_180d": abs_180,
                "Rel_30d": rel_30, "Rel_90d": rel_90, "Rel_180d": rel_180,
                "Sparkline": sparkline(analysis["CloseSeries"])
            })
            analysis["Ticker"] = ticker
            results.append(analysis)

    if results:
        df_res = pd.DataFrame(results)
        df_res.drop(columns=["CloseSeries"], inplace=True)
        
        # We sort by Perfect_Setup here, but client-side JS will re-sort on load
        df_res.sort_values(by="Perfect_Setup", ascending=False, inplace=True)

        # Format numeric and percent columns with data-order attribute for JS sorting
        def fmt_pct(val):
            return f'<span data-order="{val:.2f}">{val:.2f}%</span>' if pd.notna(val) else ""
        for col in ["Abs_30d","Abs_90d","Abs_180d","Rel_30d","Rel_90d","Rel_180d"]:
            df_res[col] = df_res[col].apply(fmt_pct)

        def fmt_num(val):
            return f'<span data-order="{val:.2f}">{val:.2f}</span>' if pd.notna(val) else ""
        for col in ["Price","SMA_20","SMA_50","SMA_100","SMA_200","Momentum_20","Momentum_50"]:
            df_res[col] = df_res[col].apply(fmt_num)

        df_res_csv = df_res.copy()
        df_res_csv.drop(columns=["Sparkline"], inplace=True)
        csv_filename = f"golden_cross_scan_Nifty{index_scope}_{timeframe}.csv"
        df_res_csv.to_csv(csv_filename, index=False)
        print(f"📁 Saved CSV to {csv_filename}")

        # HTML view setup
        df_html = df_res[[
            "Ticker","Sparkline","Price","SMA_50","SMA_200",
            "Perfect_Setup","Golden_Cross","SMA_20_above_50","SMA_50_above_200",
            "Momentum_20","Volume_Uptrend","Rel_30d","Rel_90d"
        ]].copy()
        df_html.rename(columns={"SMA_50_above_200":"50>200","SMA_20_above_50":"20>50"}, inplace=True)

        # Apply signal formatting for boolean columns (Crucial for numeric sorting in JS)
        for col in ["Perfect_Setup","Golden_Cross","50>200","20>50","Volume_Uptrend"]:
            df_html[col] = df_html[col].apply(lambda x: '<span data-order="1" class="signal green">✔</span>' if 'True' in str(x) or x else '<span data-order="0" class="signal red">✖</span>')
        
        # --- Manual HTML Table Generation for Sortability ---
        
        header_names = df_html.columns.tolist()
        
        # Define ALL columns that use numeric sorting (prices, returns, and 0/1 booleans)
        numeric_columns = ["Price", "SMA_50", "SMA_200", "Momentum_20", "Rel_30d", "Rel_90d", 
                           "Perfect_Setup", "Golden_Cross", "50>200", "20>50", "Volume_Uptrend"]

        header_row = ""
        for i, name in enumerate(header_names):
            if name == "Sparkline":
                header_row += f'<th class="no-sort">{name}</th>'
            else:
                # Add data-type attribute for JS sorting
                data_type = "numeric" if name in numeric_columns else "string"
                header_row += f'<th onclick="sortTable({i})" data-type="{data_type}">{name}<span class="sort-indicator"></span></th>'

        table_rows = ""
        for index, row in df_html.iterrows():
            # Highlight perfect setup rows using inline style (based on pre-sorting/content)
            row_style = 'style="background-color:#f0fdf4;"' if 'green' in row['Perfect_Setup'] else ''
            
            table_rows += f'<tr {row_style}>'
            for key in df_html.columns:
                cell_content = row[key]
                if key == "Ticker":
                    # The value in row[key] is like 'RELIANCE.NS'
                    full_ticker = cell_content 
                    display_ticker = full_ticker.replace(".NS", "")
                    
                    # UPDATED LINK: Constructing the Finology Ticker URL
                    finology_link = f'https://ticker.finology.in/company/{display_ticker}'
                    
                    cell_content = f'<a href="{finology_link}" target="_blank" rel="noopener noreferrer" class="ticker-link">{display_ticker}</a>'
                
                table_rows += f'<td>{cell_content}</td>'
            table_rows += '</tr>'
        
        html_content = f"""
<table id="stockTable" class="styled-table">
    <thead>
        <tr>{header_row}</tr>
    </thead>
    <tbody>
        {table_rows}
    </tbody>
</table>
"""
        # --- End of HTML Generation ---

        html_filename = f"golden_cross_scan_Nifty{index_scope}_{timeframe}.html"
        with open(html_filename,"w",encoding="utf-8") as f:
            f.write(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Golden Cross Scan - Nifty {index_scope} - {timeframe.capitalize()}</title>
<style>
/* Pure CSS Styling (Replaces Tailwind and DataTables) */
html, body {{ 
    margin: 0; 
    padding: 0; 
    overflow-x: hidden; /* FIX: Prevents page-level horizontal scrollbar */
}}
body {{ 
    font-family: 'Arial', sans-serif; 
    background-color: #f4f4f9; 
    padding: 20px; 
}}
.container {{ 
    max-width: 100%; /* FIX: Fluid width */
    width: 98%; /* FIX: Take up most of the screen */
    margin: 0 auto; 
    background-color: white; 
    padding: 15px 20px; 
    border-radius: 8px; 
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); 
}}
h2 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; font-size: 28px; font-weight: bold; }}
p {{ color: #7f8c8d; margin-bottom: 25px; font-size: 16px; }}

/* Table Styling - Ensuring Borders and Interactivity */
.styled-table {{
    width: 100%;
    min-width: 900px; /* Ensures the wide table is visible in the wrapper scroll area */
    border-collapse: collapse; 
    font-size: 14px;
    text-align: center;
    margin: 0; /* Remove margin, keep it clean */
}}
.styled-table thead th {{ /* FIX: Target thead th specifically for sticky header */
    position: sticky; /* FIX: Make header sticky */
    top: 0; /* Stick to the top of the scrollable container/viewport */
    z-index: 10; 
    background-color: #eef4f9; /* Re-apply background to prevent transparent stickiness */
    box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.1); /* Subtle shadow for visual separation */
    cursor: pointer; 
    font-weight: bold;
    text-transform: uppercase;
    border-top: 2px solid #3498db;
    border-bottom: 2px solid #3498db;
    padding: 10px 12px;
    white-space: nowrap;
}}
.styled-table td {{
    padding: 10px 12px;
    border: 1px solid #c7d5e8; 
    white-space: nowrap;
    vertical-align: middle;
}}

.styled-table tr:nth-child(even) {{
    background-color: #f7f7fa; 
}}
.styled-table tr:hover {{
    background-color: #e8f6ff;
}}

td img {{ display: block; margin: auto; height: 30px; }}
.signal {{ font-weight: 800; font-size: 1.1em; }}
.green {{ color: #27ae60; }}
.red {{ color: #e74c3c; }}

/* Ticker link styling */
.ticker-link {{
    font-weight: bold;
    color: #3498db;
    text-decoration: none; /* Remove underline */
}}
.ticker-link:hover {{
    text-decoration: underline;
}}


/* Sort Indicators */
.sort-indicator {{
    margin-left: 5px;
    display: inline-block;
    width: 0;
    height: 0;
    vertical-align: middle;
}}
.asc .sort-indicator::after {{ content: ' ▲'; }}
.desc .sort-indicator::after {{ content: ' ▼'; }}
.styled-table th.active {{ background-color: #d4eaf7; }}


/* Wrapper for table responsiveness */
.table-wrapper {{
    overflow-x: auto; /* MUST keep this to allow wide table viewing */
    max-height: 70vh; /* Optional: Constrain height for better sticky effect */
    border: 1px solid #c7d5e8;
    border-radius: 6px;
}}
</style>
</head>
<body>
<div class="container">
<h2 class="header-title">NSE Golden Cross Scan - Nifty {index_scope} ({timeframe.capitalize()})</h2>
<p>Filter criteria: Golden Cross (SMA50>SMA200) + SMA20>SMA50 + Price>SMA200 + Momentum 20d > 5% + Volume Uptrend. Click on column headers to sort the table. **The Ticker links now open on the Finology Ticker page.**</p>

<div class="table-wrapper">
{html_content}
</div>

</div>

<script>
let currentSortColumn = -1;
let sortDirection = "asc";

/**
 * Retrieves the value used for sorting from a table cell.
 * Prioritizes the 'data-order' attribute for accurate numeric/percent/boolean sorting.
 * @param {{Element}} tr - The table row element.
 * @param {{number}} idx - The index of the column/cell.
 * @returns {{number|string}} The sortable value.
 */
function getCellValue(tr, idx) {{
    const cell = tr.children[idx];
    
    // Check for <a> tag for Ticker column (index 0)
    if (idx === 0) {{
        const link = cell.querySelector('a');
        return link ? link.textContent.trim() : (cell.textContent || cell.innerText).trim();
    }}
    
    const span = cell.querySelector('span[data-order]');
    
    // 1. Numeric/Percent/Boolean check (uses data-order)
    if (span) {{
        const value = parseFloat(span.getAttribute('data-order'));
        // Use -Infinity for NaN to push missing values to the bottom in ascending order
        return isNaN(value) ? -Infinity : value;
    }}
    
    // 2. Default to text content
    return (cell.textContent || cell.innerText).trim();
}}

/**
 * Sorts the HTML table rows based on the clicked column (n).
 * @param {{number}} n - The index of the column to sort.
 */
function sortTable(n) {{
    const table = document.getElementById("stockTable");
    const tbody = table.querySelector("tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));
    const header = table.querySelector("thead tr").children[n];
    const dataType = header.getAttribute('data-type');
    
    // Determine the sorting direction
    if (currentSortColumn === n) {{
        sortDirection = sortDirection === "asc" ? "desc" : "asc";
    }} else {{
        // Reset direction and active class for new column
        // Default to descending for numbers/booleans, ascending for strings (Ticker)
        sortDirection = (dataType === 'numeric') ? 'desc' : 'asc'; 
        
        // Remove active class and indicator from old column
        if (currentSortColumn !== -1) {{
            const oldHeader = table.querySelector("thead tr").children[currentSortColumn];
            oldHeader.classList.remove("asc", "desc", "active");
        }}
        currentSortColumn = n;
    }}

    // Add active class and indicator to the current column
    header.classList.remove("asc", "desc");
    header.classList.add(sortDirection, "active");


    const sortedRows = rows.sort((rowA, rowB) => {{
        let valA = getCellValue(rowA, n);
        let valB = getCellValue(rowB, n);
        let comparison = 0;

        // Perform comparison based on data type
        if (dataType === 'numeric') {{
            // Direct numeric comparison
            if (valA < valB) comparison = -1;
            if (valA > valB) comparison = 1;
        }} 
        else {{
            // Standard string comparison (case-insensitive for 'Ticker')
            const strA = String(valA).toLowerCase();
            const strB = String(valB).toLowerCase();
            if (strA < strB) comparison = -1;
            if (strA > strB) comparison = 1;
        }}
        
        // Apply direction multiplier
        return sortDirection === "asc" ? comparison : comparison * -1;
    }});

    // Reappend the sorted rows to the tbody
    tbody.innerHTML = ''; // Clear existing content
    sortedRows.forEach(row => tbody.appendChild(row));
    
}}

// Initial sort on 'Perfect_Setup' column (Index 5) descending.
// Ticker(0), Sparkline(1), Price(2), SMA_50(3), SMA_200(4), Perfect_Setup(5)
document.addEventListener('DOMContentLoaded', () => {{
    // Automatically trigger initial sort on 'Perfect Setup' (index 5) descending
    sortTable(5); 
}});
</script>

</body>
</html>
""")
        print(f"📁 Saved HTML to {html_filename}")
    else:
        print("❌ No stocks analyzed successfully.")
