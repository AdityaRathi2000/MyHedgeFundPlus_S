import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import pandas_datareader.data as web
import requests
import streamlit as st
import altair as alt
import plotly.figure_factory as ff
import time

def get_data_df(ticker, start_year, start_month):
    ### CHECKING TIINGO FIRST
    headers = {'Content-Type': 'application/json'}
    requestResponse = requests.get(
        "https://api.tiingo.com/tiingo/daily/{}/prices?startDate={}&token=66cc23ed792a78402a46586158164db2ca4b24a5".format(ticker, dt.datetime(start_year, start_month, 1)), headers=headers)
    test_df = pd.json_normalize(requestResponse.json())

    # editing
    test_df = test_df#[::-1]

    if (test_df.empty):
        current_date = dt.datetime.now()
        test_df = web.DataReader(ticker, 'stooq', dt.datetime(start_year, start_month, 1), current_date)
        return test_df

    test_df = test_df[['date', 'open', 'high', 'low', 'close', 'volume']]
    test_df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    test_df["Date"] = test_df["Date"].apply(lambda x: x.split('T')[0])
    test_df["Date"] = test_df["Date"].apply(lambda x: dt.datetime.strptime(x, '%Y-%m-%d').date())

    return test_df

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ SMA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def smaMaker(df, numDay, type):
  smaPeriod = numDay;
  smaList = []

  running_sma = 0;
  for i in range(0,df.Date.count()):
    for p in range(i-smaPeriod, i):
      if (i-smaPeriod < 0):
        running_sma = running_sma + df.loc[i,type];
      else:
        running_sma = running_sma + df.loc[p,type];
    smaList.append(running_sma/smaPeriod)
    running_sma =0;

  return smaList
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ SMA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def sma_crossover(ticker, df, smaller, bigger, num_shares, start_year, start_month):

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  SMA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  df["SMA_{}_day".format(smaller)] = smaMaker(df, smaller, "Close");
  df["SMA_{}_day".format(bigger)] = smaMaker(df, bigger, "Close");
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  SMA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Buy/Sell ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  df["Indicator"] = (df["SMA_{}_day".format(smaller)] > df["SMA_{}_day".format(bigger)]).astype(int)
  df["Order_Indicator"] = df["Indicator"].diff()
  df.loc[df.Order_Indicator == 1, "Order"] = 1 #buy
  df.loc[df.Order_Indicator == -1, "Order"] = 2 #sell
  df["Order"] = df["Order"].fillna(0)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Buy/Sell ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  PLOTTING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  running_Buy = 0;
  running_Sell = 0;

  shares_bought = 0;
  shares_sold = 0;

  fig = plt.figure(25)

  for idx, i in df.iterrows():
    date_diff_max = i.Date - dt.datetime(start_year, start_month, 1).date()

    if (date_diff_max.days > 0):
      if (i.Order == 1):
        plt.scatter(i.Date, i.Close , c='g', s=50, marker='^')
        running_Buy += (i.Close * num_shares) # bought on this day at close price
        shares_bought = shares_bought + num_shares;
      elif (i.Order == 2 and shares_bought > shares_sold):
        plt.scatter(i.Date, i.Close , c='r', s=50, marker='v')
        running_Sell += (i.Close * num_shares) # sold on this day at close price
        shares_sold = shares_sold + num_shares;

  ############# TO SEE THE ACTUAL INDICATOR, UNCOMMENT THIS: ##########################################################
  #print("({}, {}) *** ".format(smaller, bigger) + " Total Bought: {}, Total Sold: {}, Net: {}".format(running_Buy, running_Sell, running_Sell - running_Buy))
  #plt.plot(df['Date'], df["SMA_{}_day".format(smaller)],'r', label=watchList[0] + " SMA_{}_day".format(smaller))
  #plt.plot(df['Date'], df["SMA_{}_day".format(bigger)],'g', label=watchList[0] + " SMA_{}_day".format(bigger))
  #plt.legend(loc='upper left')
  #####################################################################################################################

  plt.plot(df['Date'], df['Close'],'black', label=ticker)
  plt.title("SMA Crossover Stoch", fontsize=14)
  plt.xlabel('Time (YYYY/MM)')
  plt.ylabel('Price ($)')
  #plt.savefig("SMA Crossover Stoch.png", transparent=True)
  plt.close()
  st.write(fig)


  df["Order"] = 0;
  return smaller, bigger, shares_bought, shares_sold, (running_Sell - running_Buy)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  PLOTTING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ STOCHASTIC SIGNAL ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def stochastic(df, numDay):
  stochasticPeriod = numDay;
  stochasticList = [];

  highPeriod = 0;
  lowPeriod = 0;
  counter=0;
  for i in range(0,df.Date.count()):
    if (counter%stochasticPeriod == 0):
        if (highPeriod - lowPeriod != 0):
            kValue = (df.loc[i,"Close"] - lowPeriod)/(highPeriod - lowPeriod) * 100
        else:
            kValue = 0
        stochasticList.append(kValue);
    else:
      highPeriod = pd.DataFrame(df.loc[i-stochasticPeriod:i,"High"]).max().High
      lowPeriod = pd.DataFrame(df.loc[i-stochasticPeriod:i,"Low"]).min().Low
      kValue = (df.loc[i,"Close"] - lowPeriod)/(highPeriod - lowPeriod) * 100
      stochasticList.append(kValue);
    counter+=1;

  return stochasticList
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ STOCHASTIC SIGNAL ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def rsi_stoch(ticker, df, smaller, bigger, num_shares, start_year, start_month):
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  stoch RSI ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    stochasticPeriod = 10;
    df["stochastic"] = stochastic(df, stochasticPeriod);
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  stoch RSI ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Buy/Sell ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    df.loc[df.stochastic > bigger, "Order"] = -1  # sell
    df.loc[df.stochastic < smaller, "Order"] = 1  # buy
    df["Order"] = df["Order"].fillna(0)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Buy/Sell ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  PLOTTING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    running_Buy = 0;
    running_Sell = 0;

    shares_bought = 0;
    shares_sold = 0;

    fig = plt.figure(25)

    for idx, i in df.iterrows():
        date_diff_max = i.Date - dt.datetime(start_year, start_month, 1).date()
        if (date_diff_max.days > 0):
            if (i.Order == 1):
                plt.scatter(i.Date, i.Close, c='g', s=50, marker='^')
                running_Buy += (i.Close)  # bought on this day at close price
                shares_bought = shares_bought + num_shares;
            elif (i.Order == -1 and shares_bought > shares_sold):
                plt.scatter(i.Date, i.Close, c='r', s=50, marker='v')
                running_Sell += (i.Close)  # sold on this day at close price
                shares_sold = shares_sold + num_shares;

    ############# TO SEE THE ACTUAL INDICATOR, UNCOMMENT THIS: ##########################################################
    # mainPLT.plot(df['Date'], [smaller]*df.Date.count(),'g', label=watchList[0] + " stoch(Oversold)")
    # mainPLT.plot(df['Date'], [bigger]*df.Date.count(),'r', label=watchList[0] + " stoch(Overbought)")
    # mainPLT.plot(df['Date'], df["stochastic"],'m', label=watchList[0] + " stoch")
    #####################################################################################################################

    plt.plot(df['Date'], df['Close'], 'black', label=ticker)
    plt.title("RSI Stoch", fontsize=14)
    plt.xlabel('Time (YYYY/MM)')
    plt.ylabel('Price ($)')
    #plt.savefig("RSI Stoch.png", transparent=True)
    plt.close()
    st.write(fig)

    df["Order"] = 0;
    return smaller, bigger, shares_bought, shares_sold, (running_Sell - running_Buy)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  PLOTTING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ EMA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def emaMaker(df, numDay, smoothness, type):
  multiplier = smoothness/(1+numDay);
  emaList = [];

  ema_yesterday = df.loc[0, type];
  for i in range(0,df.Date.count()):
    ema_today = (df.loc[i, type] * multiplier) + (ema_yesterday * (1-multiplier))
    ema_yesterday = ema_today;
    emaList.append(ema_today);

  return emaList
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ EMA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def macd_analysis(ticker, df, lower, signal, higher, smoothness, num_shares, start_year, start_month):
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  SMA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  df["MACD"] = pd.DataFrame(emaMaker(df, lower, smoothness, "Close")) - pd.DataFrame(emaMaker(df, higher, smoothness, "Close"));
  df["MACD_Signal"] = emaMaker(df, signal, smoothness, "MACD");
  df["Order_Indicator"] = df["MACD"]-df["MACD_Signal"];
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  SMA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Buy/Sell ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  above = False;
  order_list = []
  threshold = 0
  for idx, i in df.iterrows():
    if (i.Order_Indicator > threshold and not above):
      above = True;
      order_list.append(1)
    elif (i.Order_Indicator < -threshold and above):
      above = False;
      order_list.append(-1)
    else:
      order_list.append(0)
  df["Order"] = pd.DataFrame(order_list);
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Buy/Sell ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  PLOTTING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  ############# TO SEE THE ACTUAL INDICATOR, UNCOMMENT THIS: ##########################################################
  #mainPLT.plot(df['Date'], seriesDifference,'r', label=watchList[0] + " MACD-Signal")
  #mainPLT.plot(df['Date'], [0]*df.Date.count(),'b', label=watchList[0] + " MACD 0")
  #mainPLT.show()
  #mainPLT.figure(figsize=(25,10))
  #####################################################################################################################

  running_Buy = 0;
  running_Sell = 0;

  shares_bought = 0;
  shares_sold = 0;

  fig = plt.figure(25)

  for idx, i in df.iterrows():
    date_diff_max = i.Date - dt.datetime(start_year, start_month, 1).date()
    if (date_diff_max.days > 0):
      if (i.Order == 1):
        plt.scatter(i.Date, i.Close , c='g', s=50, marker='^')
        running_Buy += (i.Close * num_shares) # bought on this day at close price
        shares_bought = shares_bought + num_shares;
      elif (i.Order == -1 and shares_bought > shares_sold):
        plt.scatter(i.Date, i.Close , c='r', s=50, marker='v')
        running_Sell += (i.Close * num_shares) # sold on this day at close price
        shares_sold = shares_sold + num_shares;

  df["Order"] = 0;
  plt.plot(df['Date'], df['Close'],'black', label=ticker)
  plt.title("MACD", fontsize=14)
  plt.xlabel('Time (YYYY/MM)')
  plt.ylabel('Price ($)')
  #plt.savefig("MACD.png", transparent=True)
  plt.close()
  st.write(fig)

  return lower, signal, higher, smoothness, shares_bought, shares_sold, (running_Sell - running_Buy)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  PLOTTING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ STDev ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def stdCalc(df, numDay):
  stdList = []

  for i in range(0,df.Date.count()):
    if (i < numDay):
      tempDf = df.loc[0:numDay,"Close"]
      stdList.append(tempDf.std())
    else:
      tempDf = df.loc[(i-numDay):i,"Close"]
      stdList.append(tempDf.std())

  return stdList
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ STDev ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ TRUE RANGE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def trueRange(df):
  trueRangeList = []

  for i in range(0,df.Date.count()):
    tempList = []
    if (i == 0):
      tempList.append(df.loc[i, "High"] - df.loc[i, "Low"])
    else:
      tempList.append(df.loc[i, "High"] - df.loc[i, "Low"])
      tempList.append(abs(df.loc[i, "High"] - df.loc[i-1, "Close"]))
      tempList.append(abs(df.loc[i, "Low"] - df.loc[i-1, "Close"]))

    trRange = max(tempList)
    trueRangeList.append(trRange)

  return trueRangeList
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ TRUE RANGE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def ttm_squeeze_indicator(ticker, df, std_period, sma_ema_period, multiplier, smoothness, num_shares, start_year, start_month):
  is_in_squeeze = False

  sma_ttmS = "SMA{}".format(sma_ema_period)
  std_ttmS = "STD{}".format(std_period)
  ema_ttmS = "EMA{}".format(sma_ema_period)
  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Bollinger Bands ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  df[sma_ttmS] = smaMaker(df, sma_ema_period, "Close");
  df[std_ttmS] = stdCalc(df, std_period);

  df["BollingerBands_Upper"] = df[sma_ttmS]+(multiplier*df[std_ttmS]);
  df["BollingerBands_Lower"] = df[sma_ttmS]-(multiplier*df[std_ttmS]);

  fig = plt.figure(25)

  #mainPLT.plot(df['Date'], df["BollingerBands_Upper"],'g', label="BB UpperBand")
  #mainPLT.plot(df['Date'], df["BollingerBands_Lower"],'g', label="BB LowerBand")
  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Bollinger Bands ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Keltner Channel ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  df["trueRange"] = trueRange(df);
  df["averageTrueRange"] = smaMaker(df, sma_ema_period, "trueRange");
  df[ema_ttmS] = emaMaker(df, sma_ema_period, smoothness, "Close");

  df["KeltnerChannel_Upper"] = df[ema_ttmS]+(multiplier*df["averageTrueRange"]);
  df["KeltnerChannel_Lower"] = df[ema_ttmS]-(multiplier*df["averageTrueRange"]);

  #mainPLT.plot(df['Date'], df["KeltnerChannel_Upper"],'m', label="KC UpperBand")
  #mainPLT.plot(df['Date'], df["KeltnerChannel_Lower"],'m', label="KC LowerBand")

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Keltner Channel ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Buy/Sell ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  order_lst = []
  for idx, i in df.iterrows():
    if (i.BollingerBands_Upper < i.KeltnerChannel_Upper and i.BollingerBands_Lower > i.KeltnerChannel_Lower):
      order_lst.append(1) #buy
    else:
      order_lst.append(-1) #sell
  df["Order"] = pd.DataFrame(order_lst)
  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Buy/Sell ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  running_Buy = 0;
  running_Sell = 0;

  shares_bought = 0;
  shares_sold = 0;

  for idx, i in df.iterrows():
    date_diff_max = i.Date - dt.datetime(start_year, start_month, 1).date()
    if (date_diff_max.days > 0):
      if (i.Order == 1 and ((shares_bought - shares_sold) < 5)):
        plt.scatter(i.Date, i.Close , c='g', s=50, marker='^')
        running_Buy += (i.Close * num_shares) # bought on this day at close price
        shares_bought = shares_bought + num_shares;
      elif (i.Order == -1 and shares_bought > shares_sold):
        plt.scatter(i.Date, i.Close , c='r', s=50, marker='v')
        running_Sell += (i.Close * num_shares) # sold on this day at close price
        shares_sold = shares_sold + num_shares;

  df["Order"] = 0;
  plt.plot(df['Date'], df["Close"],'black', label="KC LowerBand")
  plt.xlabel('Time (YYYY/MM)')
  plt.ylabel('Price ($)')
  plt.title("TTM Squeeze Indicator", fontsize=14)
  #plt.savefig("TTM Squeeze.png", transparent=True)
  plt.close()
  st.write(fig)

  return is_in_squeeze, std_period, sma_ema_period, multiplier, smoothness, shares_bought, shares_sold, (running_Sell - running_Buy)