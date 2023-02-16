from alpha_vantage.timeseries import TimeSeries
import pandas as pd
from pandas import Timestamp
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
API_KEY = 'VRK4OXG1AMFMC0HX'
ts = TimeSeries(key=API_KEY)
class ScriptData:
    def __init__(self) -> None:
        self.scripts = {}
    def fetch_intraday_data(self,script):
        self.data,self.metadata = ts.get_intraday(script)
        self.scripts[script] = None
    def convert_intraday_data(self,script):
        # self.data,self.metadata = ts.get_intraday(script)
        
        self.dataframe = pd.DataFrame.from_dict(self.data)

        self.dataframe = self.dataframe.transpose()
        self.dataframe.columns = ['open', 'high', 'low', 'close', 'volume']
        timestamp = list(self.data.keys())
        for i in range(len(timestamp)):
            timestamp[i] = pd.Timestamp(timestamp[i])
        values = list(self.data.values())
        self.dataframe.insert(0, "timestamp", timestamp, True)
        self.dataframe.index = range(0,len(self.dataframe))
        convert_dict = {'open': float,'high': float,'low': float,'close': float,'volume': int}
        self.dataframe = self.dataframe.astype(convert_dict)
        self.scripts[script] = self.dataframe
    def __contains__(self,key):
        if key in self.scripts:
            print(True)
        else:
            print(False)
    def __getitem__(self,key):
        if key in self.scripts:
            print(self.scripts[key])
            return self.scripts[key]
        else:
            print("Not Found")

    def __setitem__(self,key,value):
        pass

def indicator1(dfr,timeperiod):
    indicator = []
    curr_sum = 0
    
    for i in range(0,len(dfr)):
        if i+1 < timeperiod:
            indicator.append(None)
        else:
            value = (dfr['close'].iloc[i+1-timeperiod:i+1].sum())/timeperiod
            indicator.append(round(value,3))
    dfr["indicator"] = indicator
    new_df = dfr[['timestamp','indicator']]
    
    print(new_df)
    return new_df
class Strategy:
    def __init__(self,script):
        self.script = script
    def get_script_data(self):
        script_data = ScriptData()
        script_data.fetch_intraday_data(self.script)
        script_data.convert_intraday_data(self.script)
        self.df = script_data[self.script]
        
        self.indicators = indicator1(self.df,5)
        self.df['indicators'] = self.indicators['indicator']
        self.indicators = self.indicators.dropna()
        self.df = self.df.dropna()
        close_data = np.array(list(self.df['close']))
        indicators = np.array(list(self.df['indicators']))
        timestamps = np.array(list(self.df['timestamp']))
        idx = np.argwhere(np.diff(np.sign(close_data-indicators))).flatten()
        coordinates = []
        for i in idx:
            coordinates.append(timestamps[i])
        self.result = {}
        for timestamp in timestamps:
            if timestamp not in coordinates:
                self.result[timestamp] = "NO_SIGNAL"
            else:
                
                t1 = timestamp + pd.tseries.frequencies.to_offset("15min")
                query = self.df['timestamp'] == t1
                y1 = list(self.df[query]["close"])[0]
                y2 = list(self.df[query]["indicators"])[0]
                if y1 > y2:
                    self.result[timestamp] = "SELL"
                    
                elif y1 < y2:
                    self.result[timestamp] = "BUY"
    def get_signals(self):
        new_result = {}
        for key,value in self.result.items():
            if value != 'NO_SIGNAL':
                new_result[key] = value
        
        new_df = pd.DataFrame(list(new_result.items()),columns=['timestamp','signal'])
        print(new_df.head(10))
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=self.df["timestamp"], open=self.df["open"],high=self.df["high"], low=self.df["low"],close=self.df["close"],name="Historical Data"))
        fig.add_trace(go.Scatter(x=self.df["timestamp"], y=self.df["indicators"],name="SMA",line=dict(color='grey',width=5)))
        fig.update_xaxes(tickangle=90)
        fig.show()
if __name__ == "__main__":  
    script_data = ScriptData()
    script_data.fetch_intraday_data('NVDA')
    script_data.convert_intraday_data('NVDA')
    indicator1(script_data['NVDA'],5)
    strategy = Strategy('NVDA')
    strategy.get_script_data()
    strategy.get_signals()
