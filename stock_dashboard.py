# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 13:35:53 2023

@author: Malek Ben Romdhane
"""

#==============================================================================
# Initiating
#==============================================================================


# Libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf
import streamlit as st


#==============================================================================
# HOT FIX FOR YFINANCE .INFO METHOD
# Ref: https://github.com/ranaroussi/yfinance/issues/1729
#==============================================================================


import requests
import urllib

class YFinance:
    user_agent_key = "User-Agent"
    user_agent_value = ("Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/58.0.3029.110 Safari/537.36")
    
    def __init__(self, ticker):
        self.yahoo_ticker = ticker

    def __str__(self):
        return self.yahoo_ticker

    def _get_yahoo_cookie(self):
        cookie = None

        headers = {self.user_agent_key: self.user_agent_value}
        response = requests.get("https://fc.yahoo.com",
                                headers=headers,
                                allow_redirects=True)

        if not response.cookies:
            raise Exception("Failed to obtain Yahoo auth cookie.")

        cookie = list(response.cookies)[0]

        return cookie

    def _get_yahoo_crumb(self, cookie):
        crumb = None

        headers = {self.user_agent_key: self.user_agent_value}

        crumb_response = requests.get(
            "https://query1.finance.yahoo.com/v1/test/getcrumb",
            headers=headers,
            cookies={cookie.name: cookie.value},
            allow_redirects=True,
        )
        crumb = crumb_response.text

        if crumb is None:
            raise Exception("Failed to retrieve Yahoo crumb.")

        return crumb

    @property
    def info(self):
        # Yahoo modules doc informations :
        # https://cryptocointracker.com/yahoo-finance/yahoo-finance-api
        cookie = self._get_yahoo_cookie()
        crumb = self._get_yahoo_crumb(cookie)
        info = {}
        ret = {}

        headers = {self.user_agent_key: self.user_agent_value}

        yahoo_modules = ("assetProfile,"  # longBusinessSummary
                         "summaryDetail,"
                         "financialData,"
                         "indexTrend,"
                         "defaultKeyStatistics")

        url = ("https://query1.finance.yahoo.com/v10/finance/"
               f"quoteSummary/{self.yahoo_ticker}"
               f"?modules={urllib.parse.quote_plus(yahoo_modules)}"
               f"&ssl=true&crumb={urllib.parse.quote_plus(crumb)}")

        info_response = requests.get(url,
                                     headers=headers,
                                     cookies={cookie.name: cookie.value},
                                     allow_redirects=True)

        info = info_response.json()
        info = info['quoteSummary']['result'][0]

        for mainKeys in info.keys():
            for key in info[mainKeys].keys():
                if isinstance(info[mainKeys][key], dict):
                    try:
                        ret[key] = info[mainKeys][key]['raw']
                    except (KeyError, TypeError):
                        pass
                else:
                    ret[key] = info[mainKeys][key]

        return ret


#==============================================================================
# Page title
#==============================================================================

def render_page_title():
    # Set the Streamlit page title and icon
    st.set_page_config(page_title="Stock Dashboard", page_icon="📈")


#==============================================================================
# Header
#==============================================================================

def render_header():    
    # Add dashboard title and description
    st.title("STOCK DASHBOARD")
    st.write("Data source:   Yahoo Finance")


#==============================================================================
# Sidebar
#==============================================================================    

def render_sidebar():
    # Add the ticker selection on the sidebar
    # Get the list of stock tickers 
    global ticker_list
    ticker_list = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol']
        
    # Create a dropdown to select a stock
    global selected_stock
    selected_stock = st.sidebar.selectbox("Select a ticker:", ticker_list)
    
    # Function to fetch stock data
    def fetch_stock_data(stock_symbol, start_date, end_date):
        stock_data = yf.download(stock_symbol, start=start_date, end=end_date)
        return stock_data
    
    # Sidebar for date range selection
    global start_date
    global end_date
    start_date = st.sidebar.date_input("Start Date", pd.to_datetime('2023-01-01'))
    end_date = st.sidebar.date_input("End Date", pd.to_datetime('2023-10-01'))
    
    # Button to fetch data
    global update_button
    update_button= st.sidebar.button("⟳")
    if update_button:
        stock_data = fetch_stock_data(selected_stock, start_date, end_date)
        stock_data
        
        
#==============================================================================
# Tab 1
#==============================================================================

def render_tab1():
  
    # Get the company information
    @st.cache_data
    def GetCompanyInfo(ticker):
        """
        This function get the company information from Yahoo Finance.
        """
        return YFinance(ticker).info
    
    # If the ticker is already selected
    if selected_stock != '':
        # Get the company information in list format
        info = GetCompanyInfo(selected_stock)
        
        
        # Show some statistics as a DataFrame
        st.write('**1. Key Statistics:**')
        info_keys = {'previousClose':'Previous Close',
                     'open'         :'Open',
                     'bid'          :'Bid',
                     'ask'          :'Ask',
                     'dayLow'       : "Day's Range low" ,
                     'dayHigh'      : "Day's Range High",
                     'fiftyTwoWeekLow' : '52 Week Range Low',
                     'fiftyTwoWeekHigh' : '52 Week Range High',
                     'volume'       :'Volume',
                     'averageVolume' : 'Average Volume',
                     'marketCap'    :'Market Cap',
                     'beta'         :'Beta (5Y Monthly)',
                     'peRatio'      : 'PE Ratio (TTM)',
                     'trailingEps'  : 'EPS (TTM)',
                     'dividendYield' : 'Forward Dividend & Yield',	
                     'targetMeanPrice': '1y Target Est'}
        
        #Create two columns layout
        col1, col2 = st.columns(2)          
         
        # Display the table in the first column
        company_stats_left = {}
        for key in list(info_keys.keys())[:len(info_keys) // 2]:
            company_stats_left.update({info_keys[key]: info.get(key, 'Not Available')})
        company_stats_left = pd.DataFrame({'Value': pd.Series(company_stats_left)})
        col1.table(company_stats_left)
         
        # Display the table in the second column
        company_stats_right = {}
        for key in list(info_keys.keys())[len(info_keys) // 2:]:
            company_stats_right.update({info_keys[key]: info.get(key, 'Not Available')})
        company_stats_right = pd.DataFrame({'Value': pd.Series(company_stats_right)})
        
        # Format the 'Forward Dividend & Yield' column        
        dividend_rate = info.get('dividendRate', 'Not provided')         
        dividend_yield = info.get('dividendYield', 'Not provided')         
        dividend_yield_formatted = f'{dividend_rate} ({dividend_yield * 100:.2f}%)'        
        company_stats_right['Value'].loc[company_stats_right.index == 'Forward Dividend & Yield'] = dividend_yield_formatted
        
        col2.table(company_stats_right) 
        
        
        # Show the Chart
        st.write('**2. Chart:**')
        
        #Create two columns layout
        col1, col2 = st.columns(2) 
        
        # Create a list of duration options
        range_options = ['1mo', '3mo', '6mo', 'ytd', '1y', '2y', '5y', '10y', 'max']
        
        # Create a selection box
        time_range = col1.selectbox('Select a time range :', range_options)
        
        # Get historical data
        historical_data = yf.Ticker(selected_stock).history(period=time_range)
        
        # Plot the selected chart type
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=historical_data.index, y=historical_data['Close'], mode='lines', name='Close Price'))
        
        # Update layout
        fig.update_layout(title=f'{selected_stock} Stock Price ({time_range.capitalize()})',
                         xaxis_title='Date',
                         yaxis_title='Stock Price',
                         xaxis_rangeslider_visible=False)
        
        # Show the chart
        st.plotly_chart(fig)    
                           
                    
        
        # Show the company description 
        st.write('**3. Company Profile:**')
        
        # Define keys
        info_keys1 = {'address1':'Address1',
                     'address2'         :'Address 2',
                     'city'          :'City',
                     'state'          :'State',
                     'zip'       : "Zip Code" ,
                     'country'      : "Country",
                     'phone' : 'Phone',
                     'website' : 'Website',
                     'industry'       :'Industry',
                     'sector' : 'Sector',
                     'fullTimeEmployees'    :'FullTimeEmployees'}
        
        # Show Company Profile
        company_profile = {}
        for key in info_keys1:
            company_profile.update({info_keys1[key]: info.get(key, 'Not Available')})
        company_profile = pd.DataFrame({'Information': pd.Series(company_profile)})
        st.table(company_profile)
        
    
        #Show shareholders
        st.write('**4. Shareholders:**')
        
        shareholders= yf.Ticker(selected_stock).get_major_holders()
        shareholders_df = pd.DataFrame(shareholders)
        shareholders_df

        
        # Business summary
        st.write('**5. Business Summary:**')
        
        st.markdown('<div style="text-align: justify;">' + \
                    info['longBusinessSummary'] + \
                    '</div><br>',
                    unsafe_allow_html=True)
        
        st.write('**6. Executives:**')
        # Get the company officers
        company_officers = info["companyOfficers"]
        # Get the company officers
        # Create a DataFrame with only the desired columns
        desired_columns = ['name', 'age', 'title'] 
        company_officers_df = pd.DataFrame(company_officers)[desired_columns]
        company_officers_df
            
      
#==============================================================================
# Tab 2
#==============================================================================

def render_tab2():
    

    #Create two columns layout
    col1, col2, col3 = st.columns(3) 
    
    # Create a list of duration options
    range_options1 = ['1mo', '3mo', '6mo', 'ytd', '1y', '2y', '5y', '10y', 'Max']
    
    # Create a selection box
    time_range1 = col1.selectbox('Select a time range :', range_options1)
    
    # Create a list of time interval options
    time_interval_options = ['1d', '5d', '1wk', '1mo', '3mo']
    
    # Create a selection box
    time_interval = col2.selectbox('Select a time interval:', time_interval_options)

    
    # Create a list of chart options
    chart_options = ['Line Chart', 'Candlestick Chart']
     
    # Create a selection box
    chart_type = col3.selectbox('Select a Chart Type :', chart_options)
    
    
    # Plot based on the selected period    
    if update_button:
        # Get historical data based on user inputs
        historical_data = yf.Ticker(selected_stock).history(period=end_date-start_date, interval=time_interval, start=start_date, end=end_date)
        
        # Plot the selected chart type
        fig = go.Figure()
        
        if chart_type == 'Line Chart':
            fig.add_trace(go.Scatter(x=historical_data.index, y=historical_data['Close'], mode='lines', name='Close Price', yaxis='y1'))
            fig.add_trace(go.Bar(x=historical_data.index, y=historical_data['Volume'], name='Volume', yaxis='y2'))
                   
        if chart_type == 'Candlestick Chart':
            fig = go.Figure(data=[go.Candlestick(x=historical_data.index,
                                                 open=historical_data['Open'],
                                                 high=historical_data['High'],
                                                 low=historical_data['Low'],
                                                 close=historical_data['Close'], yaxis='y1')])
            fig.add_trace(go.Bar(x=historical_data.index, y=historical_data['Volume'], name='Volume', yaxis='y2'))
        
        # Update layout
        fig.update_layout(title=f'{selected_stock} Stock Price from {start_date} to {end_date}',
                         xaxis_title='Date',
                         yaxis_title='Stock Price',
                         xaxis_rangeslider_visible=False,
                         yaxis=dict(title='Close Price', side='left'),
                         yaxis2=dict(title='Volume', side='right', overlaying='y'))
        
        # Show the chart
        st.plotly_chart(fig) 
    
    elif time_range1:
        # Get historical data based on user inputs
        historical_data = yf.Ticker(selected_stock).history(period=time_range1, interval=time_interval)
        
        # Plot the selected chart type
        fig = go.Figure()
        
        if chart_type == 'Line Chart':
            fig.add_trace(go.Scatter(x=historical_data.index, y=historical_data['Close'], mode='lines', name='Close Price', yaxis='y1'))
            fig.add_trace(go.Bar(x=historical_data.index, y=historical_data['Volume'], name='Volume', yaxis='y2'))
                                      
        if chart_type == 'Candlestick Chart':
            fig = go.Figure(data=[go.Candlestick(x=historical_data.index,
                                                 open=historical_data['Open'],
                                                 high=historical_data['High'],
                                                 low=historical_data['Low'],
                                                 close=historical_data['Close'], yaxis='y1')])
            fig.add_trace(go.Bar(x=historical_data.index, y=historical_data['Volume'], name='Volume', yaxis='y2'))
            
        # Update layout
        fig.update_layout(title=f'{selected_stock} Stock Price ({time_range1.capitalize()})',
                         xaxis_title='Date',                   
                         xaxis_rangeslider_visible=False,
                         yaxis=dict(title='Close Price', side='left'),
                         yaxis2=dict(title='Volume', side='right', overlaying='y'))
        
        # Show the chart
        st.plotly_chart(fig) 
        
           
#==============================================================================
# Tab 3
#==============================================================================

def render_tab3():
    
    #Create two columns layout
    col1, col2 = st.columns(2)

    # Create a list of financial statement options
    financial_options = ['Income Statement', 'Balance Sheet', 'Cash Flow']

    # Create a selection box for financial statements
    financial_statement = col1.selectbox('Select a Financial Statement:', financial_options)

    # Create a list of period options
    period_options = ['Yearly', 'Quarterly']

    # Create a selection box for the period
    period = col2.selectbox('Select a Period:', period_options)

    # Fetch financial data based on user inputs
    if financial_statement == 'Income Statement':
        financial_data = yf.Ticker(selected_stock).get_income_stmt(pretty=True, freq=period.lower())
    elif financial_statement == 'Balance Sheet':
        financial_data = yf.Ticker(selected_stock).get_balance_sheet(pretty=True, freq=period.lower())
    elif financial_statement == 'Cash Flow':
        financial_data = yf.Ticker(selected_stock).get_cash_flow(pretty=True, freq=period.lower())

    # Display financial data
    st.write(f'**{selected_stock} {financial_statement} ({period}):**')
    st.write(financial_data)


#==============================================================================
# Tab 4
#==============================================================================

def render_tab4():
    
    st.write('**Monte Carlo Simulation**')
    
    # Create three columns layout
    col1, col2, col3 = st.columns(3)

    # Dropdown for the number of simulations
    num_simulations_options = [200, 500, 1000]
    num_simulations = col1.selectbox('Number of Simulations:', num_simulations_options)

    # Dropdown for the time horizon
    time_horizon_options = [30, 60, 90]
    time_horizon = col2.selectbox('Time Horizon (days):', time_horizon_options)

    # Button to trigger the simulation
    simulate_button = col3.button("Simulate")

    if simulate_button:
        # Get historical data
        historical_data = yf.Ticker(selected_stock).history(period=f"{time_horizon}d")

        # Calculate daily returns
        returns = historical_data['Close'].pct_change().dropna()

        # Calculate standard deviation of returns
        volatility = returns.std()
        
        simulated_df = pd.DataFrame()

        for r in range(num_simulations):
        
            stock_price_list = []
            current_price = historical_data['Close'][-1]
        
            for i in range(time_horizon):
        
                # Generate daily return
                daily_return = np.random.normal(0, volatility, 1)[0]
        
                # Calculate the stock price of next day
                future_price = current_price * (1 + daily_return)
        
                # Save the results
                stock_price_list.append(future_price)
        
                # Change the current price
                current_price = future_price
                
            # Store the simulation results
            simulated_col = pd.Series(stock_price_list)
            simulated_col.name = "Sim" + str(r)
            simulated_df = pd.concat([simulated_df, simulated_col], axis=1)
        
       
            
        # Display the plot in Streamlit
        st.line_chart(simulated_df)

        # Calculate VaR at 95% confidence interval
        ValueatRisk = np.percentile(simulated_df.iloc[-1, ], 5) - historical_data['Close'][-1]
        st.write(f"**Value at Risk at 95% confidence interval: {ValueatRisk}**")


#==============================================================================
# Tab 5
#==============================================================================

def render_tab5():
    
   
    st.write("**Financial Analysis**")
    
    #Display stock comparison
    st.write("**Stock Comparison**")
    selected_stocks_comparison = st.multiselect("Select stocks for comparison:", ticker_list)
    
    if selected_stocks_comparison:
        comparison_data = yf.download(selected_stocks_comparison, start=start_date, end=end_date)['Close']
        
        # Plot stock prices for comparison
        fig_comparison = go.Figure()
        
        for stock in selected_stocks_comparison:
            fig_comparison.add_trace(go.Scatter(x=comparison_data.index, y=comparison_data[stock], mode='lines', name=stock))
        
        # Update layout
        fig_comparison.update_layout(title='Stock Comparison',
                                     xaxis_title='Date',
                                     yaxis_title='Stock Price',
                                     xaxis_rangeslider_visible=False)
        
        # Show the chart
        st.plotly_chart(fig_comparison)

    
#==============================================================================
# Main body
#==============================================================================

# Render the page title
render_page_title()

# Render the header
render_header()

# Render the sidebar
render_sidebar()

# Render the tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Chart", "Financials", "Monte Carlo simulation", "Analysis"])
with tab1:
    render_tab1()
with tab2:
    render_tab2()
with tab3:
    render_tab3()
with tab4:
    render_tab4()
with tab5:
    render_tab5()
    

###############################################################################
# END
###############################################################################


