import pandas as pd
import numpy as np
from yahooquery import Ticker
import yfinance as yf
import datetime as dt

# function to fetch fundamental data using yahooquery
def fundamental_data_process(ticker,freq):

    data = Ticker(ticker)

    try:
        df = data.balance_sheet(frequency=freq)[['asOfDate','TotalAssets','TotalDebt',
                                                 'CurrentAssets','CurrentLiabilities','Inventory',
                                                 'WorkingCapital','RetainedEarnings','LongTermDebt']]
    except:
        df = data.balance_sheet(frequency=freq)[['asOfDate','TotalAssets','TotalDebt',
                                                 'CurrentAssets','CurrentLiabilities','Inventory',
                                                 'WorkingCapital','RetainedEarnings','LongTermDebtAndCapitalLeaseObligation']]
        df.rename(columns={'LongTermDebtAndCapitalLeaseObligation':'LongTermDebt'},inplace=True)

    df_1 = data.income_statement(frequency=freq)[['asOfDate','OperatingIncome','NetIncome','TotalRevenue','CostOfRevenue']]

    try:
        df_2 = data.cash_flow(frequency=freq)[['asOfDate','OperatingCashFlow']]
    except:
        df_2 = data.cash_flow(frequency=freq)[['asOfDate','CashFlowsfromusedinOperatingActivitiesDirect']]
        df_2.rename(columns={'CashFlowsfromusedinOperatingActivitiesDirect':'OperatingCashFlow'},inplace=True)

    # drop rows with NaNs & duplicates
    df.dropna(axis=0,inplace=True)
    df_1.dropna(axis=0,inplace=True)
    df_2.dropna(axis=0,inplace=True)

    # drop duplicated dates (keep last)
    df.drop_duplicates(subset='asOfDate',keep='last',inplace=True)
    df_1.drop_duplicates(subset='asOfDate',keep='last',inplace=True)
    df_2.drop_duplicates(subset='asOfDate',keep='last',inplace=True)

    # set the date as index
    df.set_index('asOfDate',inplace=True)
    df_1.set_index('asOfDate',inplace=True)
    df_2.set_index('asOfDate',inplace=True)

    # merge data from balance_sheet & income_statement
    df_3 = pd.concat([df_1,df_2],axis=1,join='outer')

    # merge data from df_3 with cashflow statement
    df_4 = pd.concat([df,df_3],axis=1,join='outer')

    # calculate ratios & other parameters
    df_4['BookValueEquity'] = df_4['TotalAssets'] - df_4['TotalDebt']
    df_4['ROA'] = df_4['NetIncome']/df_4['TotalAssets']
    df_4['Debt-to-Equity Ratio'] = df_4['TotalDebt']/df_4['BookValueEquity']
    df_4['Quick Ratio'] = (df_4['CurrentAssets']-df_4['Inventory'])/df_4['CurrentLiabilities']
    df_4['Current Ratio'] = df_4['TotalAssets']/df_4['TotalDebt']
    df_4['CF-to-Debt Ratio'] = df_4['OperatingCashFlow']/df_4['TotalDebt']
    df_4['GrossMargin'] = (df_4['TotalRevenue']-df_4['CostOfRevenue'])/df_4['NetIncome']
    df_4['AssetTurnoverRatio'] = df_4['TotalRevenue']/df_4['TotalAssets']

    # initiate an empty list
    z_list = []

    # calculate Altman Z-score for every period
    for i in range(len(df_4)):
        z = altman_z_score(df_4,i)
        z_list.append(z)

    # merge Z-scores with original dataframe
    df_4['Altman Z-score'] = z_list

    # Assign an estimate of credit rating based on Z-scores (Altman, 2005)
    df_4['Credit Rating'] = credit_rating(df_4['Altman Z-score'])

    # calculate differences for Piotroski score calculation
    df_4['NetIncomeDiff'] = df_4['NetIncome'].diff()
    df_4['ROADiff'] = df_4['ROA'].diff()
    df_4['OperatingCFDiff'] = df_4['OperatingCashFlow'].diff()
    df_4['CashFlow-NetIncome'] = df_4['OperatingIncome']-df_4['NetIncome']
    df_4['LTDebtDiff'] = df_4['LongTermDebt'].diff()
    df_4['CurrRDiff'] = df_4['Current Ratio'].diff()
    df_4['GrossMDiff'] = df_4['GrossMargin'].diff()
    df_4['AssTDiff'] = df_4['AssetTurnoverRatio'].diff()

    # Now to see if there's been stock splits within the last year
    end = dt.datetime.today()
    start = end - dt.timedelta(365)
    price_data = yf.download(ticker,start,end)[['Close','Adj Close']]
    
    # initiate an empty list
    f_list = []

    # calculate Altman Z-score for every period
    for i in range(len(df_4)):
        f = piotroski_f_score(df_4.iloc[i,:])
        f_list.append(f)

    # merge Z-scores with original dataframe
    if price_data['Close'].equals(price_data['Adj Close']) == 1:
        df_4['Piotroski F-score'] = [x+1 for x in f_list]
    else:
        df_4['Piotroski F-score'] = f_list

    return df_4

# function to calculate Altman Z-score
def altman_z_score(data,index):

    X1 = data['WorkingCapital'].iloc[index]/data['TotalAssets'].iloc[index]
    X2 = data['RetainedEarnings'].iloc[index]/data['TotalAssets'].iloc[index]
    X3 = data['OperatingIncome'].iloc[index]/data['TotalAssets'].iloc[index]
    X4 = data['BookValueEquity'].iloc[index]/data['TotalDebt'].iloc[index]

    z_score = (6.56*X1) + (3.26*X2) + (6.72*X3) + (1.05*X4) + 3.25
    
    return z_score

# function to estimate credit rating based on Altman Z-score
def credit_rating(z_score):

    # list credit rating categories
    rating_list = ['AAA','AA+','AA','AA-','A+','A','A-',
                'BBB+','BBB','BBB-','BB+','BB','BB-','B+','B','B-',
                'CCC+','CCC','CCC-','D']

    rating_reversed = list(reversed(rating_list))

    # define the cut-off Z-score values for each rating category (Altman, 2005)
    bin = [0,1.75,2.5,3.2,3.75,4.15,4.5,4.75,4.95,5.25,5.65,5.85,
            6.25,6.4,6.65,6.85,7,7.3,7.6,8.15,np.inf]

    # Assign an estimate of credit rating based on Z-scores (Altman, 2005)
    rating = pd.cut(x=z_score,bins=bin,labels=rating_reversed)

    return rating

# a function to calculate Piotroski's F-score
def piotroski_f_score(df):
    
    F_score = 0
    
    # keep adding the F-score if criteria are met
    if df['NetIncomeDiff'] > 0:
        F_score += 1
    if df['ROADiff'] > 0:
        F_score += 1
    if df['OperatingCFDiff'] > 0:
        F_score += 1
    if df['CashFlow-NetIncome'] > 0:
        F_score += 1
    if df['LTDebtDiff'] > 0:
        F_score += 1
    if df['CurrRDiff'] > 0:
        F_score += 1
    if df['GrossMDiff'] > 0:
        F_score += 1
    if df['AssTDiff'] > 0:
        F_score += 1
    
    return F_score

# main function
def main():

    # define the ticker symbol for the stock of interest
    print('')
    ticker = input('Type the ticker symbol: ')
    freq = input('Type "a" for "Annual" or "q" for "Quarterly": ')
    df = fundamental_data_process(ticker,freq)
    
    # print results
    print('')
    print(f'Ticker Symbol: {ticker}')
    print('---------------------------------------------------------------------------------------------------------------------------------')
    print(df[['Quick Ratio','Debt-to-Equity Ratio',
              'Current Ratio','CF-to-Debt Ratio',
              'Altman Z-score','Credit Rating','Piotroski F-score']].iloc[1:])
    print('')

if __name__ == "__main__":
    main()