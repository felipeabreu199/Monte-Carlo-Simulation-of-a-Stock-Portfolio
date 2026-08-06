import pandas as pd
import numpy as np
import matplotlib
import tkinter as tk

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import datetime as dt
import yfinance as yf


def center_window(fig):
    # grab the tk window behind the matplotlib canvas
    window = fig.canvas.manager.window
    window.update_idletasks()

    # screen and window sizes for center math
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    ww = window.winfo_width()
    wh = window.winfo_height()

    # place window in the exact middle of the monitor
    x = (sw - ww) // 2
    y = (sh - wh) // 2
    window.geometry(f"+{x}+{y}")


def get_data(stocks, start, end):
    # download historical prices from yahoo finance
    stockdata = yf.download(stocks, start=start, end=end, progress=False, auto_adjust=True)

    # extract closing prices, handle single or multiple tickers
    if isinstance(stockdata.columns, pd.MultiIndex):
        stockdata = stockdata['Close']
    else:
        stockdata = stockdata[['Close']]

    # calculate daily returns and key statistics
    returns = stockdata.pct_change().dropna()
    meanreturns = returns.mean()
    covmatrix = returns.cov()
    return meanreturns, covmatrix


# list of tickers to simulate
stocklist = ['nvda', 'sndk', 'goog', 'ltm', 'tls']

# append .ax for australian stocks
stocks = [stock + '.ax' if stock == 'tls' else stock for stock in stocklist]

# define simulation time window (approx 1 year of data)
enddate = dt.datetime.now()
startdate = enddate - dt.timedelta(days=366)

meanreturns, covmatrix = get_data(stocks, startdate, enddate)

# random portfolio weights that sum to 1 (100%)
weights = np.random.random(len(meanreturns))
weights /= np.sum(weights)

# simulation parameters
mc_sims = 300
t = 120
initialportfolio = 10000

# prepare mean return matrix for vectorized math
meanm = np.full(shape=(t, len(weights)), fill_value=meanreturns.values)
meanm = meanm.T

# store all simulation paths
portfolio_sims = np.full(shape=(t, mc_sims), fill_value=0.0)

for m in range(mc_sims):
    # generate correlated random returns using cholesky decomposition
    z = np.random.normal(size=(t, len(weights)))
    l = np.linalg.cholesky(covmatrix)
    dailyreturns = meanm + np.inner(l, z)
    portfolio_sims[:, m] = np.cumprod(np.inner(weights, dailyreturns.T) + 1) * initialportfolio

# grab final values from last day of all simulations
final_values = portfolio_sims[-1, :]

# compute summary statistics
stats = {
    "mean final": np.mean(final_values),
    "median final": np.median(final_values),
    "best case": np.max(final_values),
    "worst case": np.min(final_values),
    "percentile 5%": np.percentile(final_values, 5),
    "percentile 95%": np.percentile(final_values, 95),
}

# calculate profit metrics for beginners
profit = stats["mean final"] - initialportfolio
profit_pct = (profit / initialportfolio) * 100

# simulation figure (square and centered)
fig, ax = plt.subplots(figsize=(8, 6))
ax.set_xlim(0, t)
ax.set_ylim(np.min(portfolio_sims) * 0.95, np.max(portfolio_sims) * 1.05)
ax.set_xlabel("Days")
ax.set_ylabel("Portfolio Value ($)")
ax.set_title("MC Simulation of Portfolio Returns")
ax.axhline(initialportfolio, color="gray", linestyle="--", alpha=0.4)

plt.show(block=False)
center_window(fig)

# draw each simulation path one by one
for i in range(mc_sims):
    ax.plot(range(t), portfolio_sims[:, i], lw=0.8, alpha=0.6)
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.01)

plt.show()

# dashboard figure (square and centered)
fig2, ax2 = plt.subplots(figsize=(8, 6))
ax2.axis("off")

# build the text dashboard
text = "stocks and weights\n"
for ticker, w in zip(stocks, weights):
    text += f"{ticker:<12} {w * 100:5.1f}%\n"

# total weight line so you can verify it adds to 100%
text += f"{'total':<12} {np.sum(weights) * 100:5.1f}%\n"

text += "\nsimulation settings\n"
text += f"simulations:      {mc_sims}\n"
text += f"horizon:          {t} days\n"
text += f"initial capital:  ${initialportfolio:,.0f}\n"

text += "\nprediction summary\n"
for k, v in stats.items():
    text += f"{k:<18} ${v:,.0f}\n"

# beginner friendly profit lines
text += "\nprofit overview\n"
text += f"expected profit:    ${profit:,.0f}\n"
text += f"profit percentage:  {profit_pct:5.1f}%\n"

text += "\nquick interpretation\n"
text += f"in 95% of cases the value stayed above ${stats['percentile 5%']:,.0f}\n"
text += f"expected average value: ${stats['mean final']:,.0f}\n"

ax2.text(0.05, 0.95, text, transform=ax2.transAxes,
         fontsize=11, verticalalignment="top", fontfamily="monospace")

# mini pie chart showing portfolio allocation in the top right corner
ax_pie = fig2.add_axes([0.55, 0.55, 0.4, 0.4])
ax_pie.pie(weights, labels=stocks, autopct='%1.1f%%', startangle=90,
           textprops={'fontsize': 9})
ax_pie.set_title("allocation", fontsize=10)

plt.tight_layout()
plt.show(block=False)
center_window(fig2)

plt.show()