import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import plotly.figure_factory as ff
import matplotlib.pyplot as plt
import mhfPlus_functions as mhf_f

#streamlit run /Users/adityarathi/PycharmProjects/streamlit_experiment/main.py

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    st.title('Welcome to MyHedgeFund+')

    ticker_input = st.text_input("Please enter ticker symbol of company you are interested in", '')
    start_date_input = st.text_input("Please enter start date in the format MM/DD/YYYY", '')
    num_trades_input = st.text_input("Please enter # of shares you want to enter/exit from a position with", '')

    if (start_date_input != ''):
        date = datetime.strptime(start_date_input, '%m/%d/%Y')

        start_day = int(start_date_input.split('/')[1])
        start_month = int(date.month) #date.strftime("%B")
        start_year = int(date.year)
        if (num_trades_input != ''):
            num_trades = int(num_trades_input)

            st.write("**Ticker Symbol:** {}".format(ticker_input))
            st.write("**Start Day:** {}".format(start_day))
            st.write("**Start Month:** {}".format(start_month))
            st.write("**Start Year:** {}".format(start_year))
            st.write("**Number of Shares per trade:** {}".format(num_trades))

            defined_df = mhf_f.get_data_df(ticker_input, start_year, start_month)

            st.write("# SMA Crossover")
            st.write("Read more [here] (https://www.investopedia.com/terms/c/crossover.asp#:~:text=Moving%20averages%20can%20determine%20a,or%20a%20breakout%20or%20breakdown)")
            s, b, shares_bought_SMA, shares_sold_SMA, net_SMA = mhf_f.sma_crossover(ticker_input, defined_df, 6, 20, num_trades,
                                                                                    start_year, start_month)
            st.write("Net made from strategy: ***${}***, with **{}** shares bought and **{}** shares sold in **{}** days ({} to {})".format(
                round(net_SMA,2), shares_bought_SMA, shares_sold_SMA, (datetime.now() - datetime(start_year, start_month, 1)).days,
                datetime(start_year, start_month, 1).date(), datetime.now().date()
            ))

            st.write("# RSI Stochastic")
            st.write("Read more [here] (https://www.investopedia.com/terms/s/stochrsi.asp#:~:text=The%20Stochastic%20RSI%20(StochRSI)%20is,than%20to%20standard%20price%20data)")
            s_rsi, b_rsi, shares_bought_RSI, shares_sold_RSI, net_RSI = mhf_f.rsi_stoch(ticker_input, defined_df, 10, 40, num_trades, start_year, start_month)
            st.write("Net made from strategy: ***${}***, with **{}** shares bought and **{}** shares sold in **{}** days ({} to {})".format(
                round(net_RSI,2), shares_bought_RSI, shares_sold_RSI, (datetime.now() - datetime(start_year, start_month, 1)).days,
                datetime(start_year, start_month, 1).date(), datetime.now().date()
            ))

            st.write("# MACD ")
            st.write("Read more [here] (https://www.investopedia.com/terms/m/macd.asp)")
            l, s, h, smooth, shares_bought_MACD, shares_sold_MACD, net_MACD = mhf_f.macd_analysis(ticker_input, defined_df, 12, 9, 26, 2, num_trades, start_year, start_month)
            st.write("Net made from strategy: ***${}***, with **{}** shares bought and **{}** shares sold in **{}** days ({} to {})".format(
                round(net_MACD,2), shares_bought_MACD, shares_sold_MACD, (datetime.now() - datetime(start_year, start_month, 1)).days,
                datetime(start_year, start_month, 1).date(), datetime.now().date()
            ))

            st.write("# TTM Squeeze ")
            st.write("Read more [here] (https://www.investopedia.com/articles/technical/04/030304.asp)")
            squeeze, std, sma_ema, multi, smooth, shares_bought_TTM, shares_sold_TTM, net_TTM = mhf_f.ttm_squeeze_indicator(
                ticker_input, defined_df, 20, 20, 2, 2, num_trades, start_year, start_month)
            st.write("Net made from strategy: ***${}***, with **{}** shares bought and **{}** shares sold in **{}** days ({} to {})".format(
                round(net_TTM,2), shares_bought_TTM, shares_sold_TTM, (datetime.now() - datetime(start_year, start_month, 1)).days,
                datetime(start_year, start_month, 1).date(), datetime.now().date()
            ))

        else:
            num_trades = ''
    else:
        start_day = ''
        start_month = ''
        start_year = ''
        num_trades = ''