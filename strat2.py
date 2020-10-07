import pandas as pd
import time
import dbscrape
import ta
import datetime as dt
import backtrader as bt
import backtrader.indicators as btind

import numpy as np
import logging
import datetime

class SnRfollowup(bt.Strategy):
    

    def __init__(self):


        n1 = 20
        n2 = 10
        n3 = 14
        n4 = 20
        n_dev = 2
        entry_stopLoss = 30
        supportRange = 25
        resistanceRange = 25
        exitRange = 100
        exit_rev = 60
        exitPrice = 0
        support_down_counter = 0
        resistance_up_counter = 0
        init_support_range = 100
        rev_candleRange = 30
        levelPriceRange = 60

        # Precompute the two moving averages
        '''
        self.bollinger_mavg = self.I(ta.volatility.bollinger_mavg, pd.Series(self.data.Close), self.n1) #bollinger_hband
        self.bollinger_lband = self.I(ta.volatility.bollinger_lband, pd.Series(self.data.Close), self.n1, self.n_dev) #bollinger_lband
        self.bollinger_hband = self.I(ta.volatility.bollinger_hband, pd.Series(self.data.Close), self.n1, self.n_dev) #bollinger_lband
        self.ema_10 = self.I(ta.volatility.bollinger_mavg, pd.Series(self.data.Close), self.n2) # EMA
        self.vwap = self.I(ta.volume.volume_weighted_average_price, pd.Series(self.data.High), pd.Series(self.data.Low), pd.Series(self.data.Close), pd.Series(self.data.Volume), self.n3)
        self.rsi = self.I(ta.momentum.rsi, pd.Series(self.data.Close), self.n4)
        '''
        self.bband = bt.indicators.BollingerBands(self.datas[0], period = n1)

        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        self.redLine = False
        self.blueLine = False
        self.supportLine = []
        self.resistanceLine = []
        self.fin_state = "searching"
        self.stopLoss = 0
        # self.daily_data = minuteto.minutetoyear(self.data.df.index[0].month, self.data.df.index[-1].month, self.data.df.index[0].year, self.data.df.index[-1].year)

    def sellCheck(self):
        if not self.position:
            if self.datahigh> self.bband.lines.mid:
                return True
        return False
    
    def buyCheck(self):
        if not self.position:
            if self.datalow < self.bband.lines.mid:
                return True
        return False

    
    def getfractalSupRes(self, timeframe=750): ## timeframe=750 for 2 days ##
        levels = []
        if len(self.data) < timeframe:
            return levels
            
        candle_mean =  np.mean(self.datahigh[-1*timeframe:] - self.datalow[-1*timeframe:])
        for j in range(timeframe-2): ## 2 datapoint padding
            i = - j - 1 ## set the right iterator for direction (Currently backwards)
            if self.datalow[i] < self.datalow[i-1] \
                    and self.datalow[i] < self.datalow[i+1] \
                    and self.datalow[i+1] < self.datalow[i+2] \
                    and self.datalow[i-1] < self.datalow[i-2]:
                if np.sum([abs(self.datalow[i]-x) < candle_mean  for x in levels]) == 0: ## Proximity Check
                    levels.append((i, self.datalow[i])) ## Support Check
            if self.datahigh[i] > self.datahigh[i-1] \
                    and self.datahigh[i] > self.datahigh[i+1] \
                    and self.datahigh[i+1] > self.datahigh[i+2] \
                    and self.datahigh[i-1] > self.datahigh[i-2]:
                if np.sum([abs(self.datahigh[i]-x) < candle_mean  for x in levels]) == 0: ## Proximity Check
                    levels.append((i,self.datahigh[i])) ## Resisitance Check
        return levels

    def createLevels(self, timeframe=800):
        levels = []
        if len(self.data) < timeframe:
            return levels
        levels.append((0, max(self.datahigh[-timeframe:]))) # timeframe High
        levels.append((0, min(self.datalow[-timeframe:]))) # timeframe Low

        for i, price in enumerate(self.dataclose[-timeframe:]):
            thisMax = max(self.datahigh[-i-10:-i-1])
            thisMin = min(self.datalow[-i-10:-i-1])
            if thisMax - thisMin < self.levelPriceRange:
                levels.append((-i-5, (thisMax+thisMin)/2))
        self.plot_all(levels)

        return levels
        # highs in 30 point range level
        # lows in 30 point range level

    def prevdayPrices(self):
        priceList = []
        current_date = self.data.index[-1].date()
        print(str(current_date))
        print(str(current_date - dt.timedelta(days=1)))
        day_mask = self.data.df.index == (current_date - dt.timedelta(days=1))
        prev_data = self.data.df.loc[day_mask]
        # prev_data = self.data.df.index.apply(lambda x: x.date() == (current_date - dt.timedelta(days=1)))
        if prev_data.size == 0:
            print("Previous day data not available: " + str(current_date))
            logging.info("Previous day data not available: " + str(current_date))
            priceList.append(self.dataopen[-1] + self.init_support_range)
            priceList.append(self.dataopen[-1] - self.init_support_range)
        print(prev_data.head())
        return priceList

    def next(self):
        if len(self.dataclose) < 751:
            logging.info("close len is " + str(len(self.dataclose)))
            # print("close len is " + str(len(self.data.Close)))
            return
        ## POPULATE SUPPORT AND RESISTANCES
        inRange = False
        if self.fin_state == "searching":
            self.supportLine = []
            self.resistanceLine = []
            levels = self.createLevels()
            # print(levels)
            for level in levels:
                pos, l  = level
                if l > self.dataclose[-1]:
                    self.resistanceLine.append(l)
                else:
                    self.supportLine.append(l)


        ## CHECK EMPTY SUPPORT/RESISTANCE
        if not len(self.supportLine):
            self.supportLine.append(0)
        if not len(self.resistanceLine):
            self.resistanceLine.append(0)

        averagePrice = (self.dataopen + self.dataclose[-1])/2
        
        ## trailing Constant Stop Loss
        #if self.position.is_long:
        if self.position.is_long:

            if self.dataclose[-1] < self.stopLoss:
                logging.info(str(self.data.index[-1]) + "- Closed long position at " + ", Stop Loss=".join([str(self.dataclose[-1]), str(self.stopLoss)]) + ", Profit=" + str(self.position.pl))
                # print(str(self.data.index[-1]) + "- Closed long position at " + ", Stop Loss=".join([str(self.data.Close[-1]), str(self.stopLoss)]) + ", Profit=" + str(self.position.pl))
                self.position.close()
            else:
                const_stoploss = self.dataclose[-1] - self.entry_stopLoss
                if const_stoploss > self.stopLoss:
                    self.stopLoss = const_stoploss

        if self.position.is_short:
            if self.dataclose[-1] > self.stopLoss:
                logging.info(str(self.data.index[-1]) + "- Closed short position at " + ", Stop Loss=".join([str(self.dataclose[-1]), str(self.stopLoss)]) + ", Profit=" + str(self.position.pl))
                # print(str(self.data.index[-1]) + "- Closed short position at " + ", Stop Loss=".join([str(self.data.Close[-1]), str(self.stopLoss)]) + ", Profit=" + str(self.position.pl))
                self.position.close()
            else:
                const_stoploss = self.dataclose[-1] + self.entry_stopLoss
                if const_stoploss < self.stopLoss:
                    self.stopLoss = const_stoploss
        ## EXIT STRATEGY
        if self.position.is_long:
            if self.dataclose[-1] > self.exitPrice:
                logging.info(str(self.data.index[-1]) + " Exited Position at Price=" + str(self.dataclose[-1]) + ", Profit=" + str(self.position.pl))
                self.position.close()

        if self.position.is_short:
            if self.dataclose[-1] < self.exitPrice:
                logging.info(str(self.data.index[-1]) + " Exited Position at Price=" + str(self.dataclose[-1]) + ", Profit=" + str(self.position.pl))
                self.position.close()

        ## RESISTANCE LINE STRATEGY
        if abs(self.datahigh - self.resistanceLine[-1]) < self.resistanceRange:
            self.fin_state = "resistanceLine"

        elif self.fin_state is not "supportLine":
            self.fin_state = "searching"

        if self.dataclose[-1] < self.dataclose[-2]:
            self.resistance_up_counter = 0

        if self.fin_state is "resistanceLine":
            logging.info(str(self.data.index[-1]) + "- Price at resisitance line=" + str(self.resistanceLine[-1]))
            if ((self.dataopen[-1] - self.dataclose[-1]) > self.rev_candleRange):
            # if (self.ema_10 - self.ema_10[-1]) < 2: ## momentum based reversal #todo Change this method
                if self.sellCheck():
                    self.sell()
                    self.stopLoss = self.dataclose[-1] + self.entry_stopLoss
                    self.exitPrice = self.dataclose[-1] - self.exit_rev
                    logging.info("Short order(Big Rev Candle) at " + str(self.data.index[-1]) + ", Price=" + str(self.dataclose[-1]) + ", Stop Loss=" + str(self.stopLoss))
            ## todo also check that open < close and (High - Close)/(HIgh - Open) > 0.4 Bounce based Reversal
            if self.dataclose[-1] > self.dataclose[-2]: ## Count based breakout
                self.resistance_up_counter = self.resistance_up_counter + 1
                logging.info("res_up_count="+str(self.resistance_up_counter))
            if self.resistance_up_counter >= 3:
                if self.buyCheck():
                    self.buy()
                    self.stopLoss = self.dataclose[-1] - self.entry_stopLoss
                    self.exitPrice = self.dataclose[-1] + self.exitRange
                    logging.info("Long order(Count Breakout) at " + str(self.data.index[-1]) + ", Price=" + str(self.dataclose[-1]) + ", Stop Loss=" + str(self.stopLoss))
            if self.datahigh > (self.resistanceLine[-1] + self.resistanceRange): ## price based breakout
                self.supportLine.append(self.resistanceLine[-1])
                del self.resistanceLine[-1]
                if self.buyCheck():
                    self.buy()
                    self.stopLoss = self.dataclose[-1] - self.entry_stopLoss
                    self.exitPrice = self.dataclose[-1] + self.exitRange
                    logging.info("Long order(Price Breakout) at " + str(self.data.index[-1]) + ", Price=" + str(self.dataclose[-1]) + ", Stop Loss=" + str(self.stopLoss))

        ## SUPPORT LINE STRATEGY
        if abs(self.datalow - self.supportLine[-1]) < self.supportRange:
            self.fin_state = "supportLine"
        elif self.fin_state is not "resistanceLine":
            self.fin_state = "searching"
        if self.dataclose[-1] > self.dataclose[-2]:
            self.support_down_counter = 0
        

        if self.fin_state is "supportLine": ## Candle range reversal
            logging.info(str(self.data.index[-1]) + "- Price at support line=" + str(self.supportLine[-1]))
            if ((self.dataclose[-1] - self.dataopen[-1]) > self.rev_candleRange): # Big Rev Candle
                    # or (self.ema_10 - self.ema_10[-1]) > -2: ## momentum based reversal
                if self.buyCheck():
                    self.buy()
                    self.stopLoss = self.dataclose[-1] - self.entry_stopLoss
                    self.exitPrice = self.dataclose[-1] + self.exit_rev
                    logging.info("Long order(Big Rev Candle) at " + str(self.data.index[-1]) + ", Price=" + str(self.dataclose[-1]) + ", Stop Loss=" + str(self.stopLoss))
            
            ## todo also check that close < open and (Close - Low)/(open - Low) > 0.4 Bounce based Reversal
            if self.dataclose[-1] < self.dataclose[-2]: ## Count based breakout
                self.support_down_counter = self.support_down_counter + 1
                logging.info("sup_down_count="+str(self.support_down_counter))

            if self.support_down_counter >= 3:
                if self.sellCheck():
                    self.sell()
                    self.stopLoss = self.dataclose[-1] + self.entry_stopLoss
                    self.exitPrice = self.dataclose[-1] - self.exitRange
                    logging.info("Short order(Count Breakout) at " + str(self.data.index[-1]) + ", Price=" + str(self.dataclose[-1]) + ", Stop Loss=" + str(self.stopLoss))
            if self.datalow < (self.supportLine[-1] - self.supportRange): ## price based breakout
                self.resistanceLine.append(self.supportLine[-1])
                del self.supportLine[-1]
                if self.sellCheck():
                    self.sell()
                    self.stopLoss = self.dataclose[-1] + self.entry_stopLoss
                    self.exitPrice = self.dataclose[-1] - self.exitRange
                    logging.info("Short order(Price Breakout) at " + str(self.data.index[-1]) + ", Price=" + str(self.dataclose[-1]) + ", Stop Loss=" + str(self.stopLoss))

## SUP/RES Lines:
## OHLC of weekly data/previous day/expiry cycle
## recent data more weightage
## all prev same day of weeks data more weightage (Wed+Thurs)(Mon+Fri)


if __name__ == '__main__':
# Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Add a strategy
    cerebro.addstrategy(SnRfollowup)

    data1 = dbscrape.gettable("db.pikujs.com","ohlcvdata","postgres","timepa$$","banknifty_f2")
    
    # Create a Data Feed
    data = bt.feeds.PandasData(dataname =data1)
    
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)
    
    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
    
    cerebro.addsizer(bt.sizers.FixedSize, stake=1)
    
    # Set the commission
    cerebro.broker.setcommission(commission=0.002)
    
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Run over everything
    cerebro.run()
    
    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
