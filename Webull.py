import json
import sched
import time
import pandas as pd
from trendln import calc_support_resistance, get_extrema, plot_sup_res_date
import matplotlib.pyplot as plt
from paper_webull import paper_webull  # Assuming paper_webull 

# Constants
TOKEN_FILE = "token.txt"

# Initialize Webull connection
def init_webull():
    wb = paper_webull()
    try:
        with open(TOKEN_FILE, "r") as f:
            login_info = json.load(f)
    except FileNotFoundError:
        print("First time login.")
        login_info = None

    if not login_info:
        login_info = first_time_login(wb)
    else:
        wb.refresh_login()
        wb.login_with_credentials(login_info)

    return wb

# First time Webull login
def first_time_login(wb):
    wb.get_mfa('your_email@email.com')
    code = input('Enter MFA Code: ')
    login_info = wb.login('your_email@email.com', 'your_password', 'Your_Device', code)
    with open(TOKEN_FILE, "w") as f:
        f.write(json.dumps(login_info))
    return login_info

# Draw support and resistance chart
def draw_chart(hist, symbol):
    mins, maxs = calc_support_resistance((hist[-1000:].low, hist[-1000:].high))
    support = mins[1][1]
    resistance = maxs[1][1]

    fig = plot_sup_res_date((hist[-1000:].low, hist[-1000:].high), hist[-1000:].index)
    fig.canvas.set_window_title(symbol.upper() + " Bot")
    fig.suptitle(symbol.upper() + " Support/Resistance Lines")
    plt.draw()
    return support, resistance

# Execute trading logic
def execute_trading_logic(wb, hist, symbol, support, resistance, entered_trade):
    low = hist.iloc[-1, 2]
    high = hist.iloc[-1, 1]

    if low <= support and not entered_trade:
        wb.place_order(symbol, 'BUY')
        entered_trade = True
    elif high >= resistance and entered_trade:
        wb.place_order(symbol, 'SELL')
        entered_trade = False

    return entered_trade

# Main function
def main():
    wb = init_webull()
    scheduler = sched.scheduler(time.time, time.sleep)
    symbol = input("Enter the symbol in uppercase letters you want to trade: ")
    timeframe = input("Enter the timeframe in minutes to trade on (e.g. 1,5,15,60): ")
    period = input("Enter the period in days for support/resistance calculation (e.g. 1,5,30): ")
    hist = wb.get_historical_data(symbol, timeframe, period)
    entered_trade = False

    def run(sc):
        nonlocal hist, entered_trade
        support, resistance = draw_chart(hist, symbol)
        entered_trade = execute_trading_logic(wb, hist, symbol, support, resistance, entered_trade)
        scheduler.enter(60, 1, run, (sc,))

    scheduler.enter(1, 1, run, (scheduler,))
    scheduler.run()

if __name__ == "__main__":
    main()
