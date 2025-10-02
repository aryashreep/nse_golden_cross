# NSE Golden Cross & Swing Trading Scanner

This Python project scans Nifty stocks for swing trading opportunities using technical indicators such as Golden Cross, momentum, and volume. It generates both a CSV file and an interactive HTML report for easy review.

---

## Prerequisites

- Python 3.8 or higher

---

## Dependencies

Install all required packages using:

```sh
pip install -r requirements.txt
```

**Packages Used:**

- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **yfinance**: Fetching historical stock data from Yahoo Finance
- **requests**: HTTP requests for data retrieval
- **tqdm**: Progress bars for loops
- **tenacity**: Retry logic for robust data fetching
- **matplotlib**: Plotting sparklines in HTML reports
- **jinja2**: Templating for generating HTML reports

---

## What is a Golden Cross?

A **Golden Cross** is a bullish technical pattern that occurs when a short-term moving average (typically the 50-period SMA) crosses above a long-term moving average (typically the 200-period SMA). This crossover signals a potential shift from a downtrend to an uptrend and is widely used by traders to identify buying opportunities.

---

## Usage

Run the script from the command line with one argument for the analysis timeframe: `day`, `weekly`, or `monthly`.

### Timeframes

| Timeframe | Interval Used | Period Scanned | Description                                |
| --------- | ------------- | -------------- | ------------------------------------------ |
| day       | 1-day (1d)    | 1 year (1y)    | Best for short-term swing trading.         |
| weekly    | 1-week (1wk)  | 5 years (5y)   | Suitable for medium-term position trading. |
| monthly   | 1-month (1mo) | 10 years (10y) | Ideal for long-term investment analysis.   |

### Running the Scan

```sh
# Scan only Nifty 50 stocks on a daily timeframe
python nse_golden_cross.py day --index-scope 50

# Scan Nifty 100 stocks on a weekly timeframe
python nse_golden_cross.py weekly --index-scope 100

# The default remains Nifty 500
python nse_golden_cross.py monthly
```

---

## Scan Criteria (Perfect Setup)

A stock is flagged as a **Perfect Setup** if it meets **all** the following technical conditions:

1. **Golden Cross**: The 50-period Simple Moving Average (SMA 50) is crossing above the 200-period SMA.
2. **Short-Term Momentum**: The 20-period SMA is above the 50-period SMA (SMA 20 > SMA 50).
3. **Long-Term Uptrend**: The current price is above the 200-period SMA (Price > SMA 200).
4. **Price Momentum**: The 20-period price change is greater than 5% (Momentum 20d > 5%).
5. **Volume Confirmation**: The 20-period Average Volume is greater than the previous 20-period Average Volume (Volume Uptrend).

---

## Output

Two files will be generated in the same directory, named based on the timeframe used:

- `golden_cross_scan_{timeframe}.csv`: Spreadsheet file containing all metrics for all scanned stocks.
- `golden_cross_scan_{timeframe}.html`: Interactive, sortable HTML table report with price sparklines and conditional color-coding.

---

## Output Columns Explained

| Column Name               | Description                                                                           |
| ------------------------- | ------------------------------------------------------------------------------------- |
| **Symbol**                | Stock ticker symbol                                                                   |
| **Name**                  | Company name                                                                          |
| **Price**                 | Latest closing price                                                                  |
| **SMA 20**                | 20-period Simple Moving Average (short-term trend)                                    |
| **SMA 50**                | 50-period Simple Moving Average (medium-term trend)                                   |
| **SMA 200**               | 200-period Simple Moving Average (long-term trend)                                    |
| **Golden Cross**          | Indicates if SMA 50 has crossed above SMA 200 (Yes/No)                                |
| **Momentum 20d (%)**      | Percentage price change over the last 20 periods                                      |
| **Volume (Avg 20d)**      | Average trading volume over the last 20 periods                                       |
| **Prev Volume (Avg 20d)** | Average trading volume over the previous 20 periods (for volume uptrend confirmation) |
| **Volume Uptrend**        | Indicates if current avg volume > previous avg volume (Yes/No)                        |
| **Perfect Setup**         | Flags stocks meeting all criteria above (Yes/No)                                      |
| **Sparkline**             | Mini chart showing recent price movement (HTML report only)                           |

These columns help you quickly identify stocks that meet the Golden Cross and other swing trading criteria.

---

## AUTHOR

Created by: Aryashree Pritikrishna  
Principal Architect | Full Stack, DevOps, Security  
LinkedIn: https://www.linkedin.com/in/aryashreep  
GitHub: https://github.com/aryashreep

---

## License

MIT License
