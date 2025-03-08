import pandas as pd
import ib_insync
from ib_insync import *
import logging

# Set up logging to log real-time trade updates
logging.basicConfig(filename='rt_trades.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# create logger
#logger = logging.getLogger()
logging.info('start log')

util.startLoop()  # only use in interactive environments (i.e. Jupyter Notebooks)

ib = IB()
ib.disconnect()

# ib.connect(clientId=1)
ib.connect(host='127.0.0.1', port=7497, clientId=5)

# init dataframe
df = pd.DataFrame(columns=['date', 'last', 'vol'])
df.set_index('date', inplace=True)


def new_data(tickers):
    ''' process incoming data and check for trade entry '''
    
    global df

    for ticker in tickers:
        df.loc[ticker.time] = ticker.last
        current_volume = ticker.volume

    five_mins_ago = df.index[-1] - pd.Timedelta(minutes=3)

    if df.index[0] < five_mins_ago:
        df = df[five_mins_ago:]
        
        #pricing analysis
        price_min = df['last'].min()
        print("price_min =",price_min)
        logging.info('price_min' + str(price_min))
        price_max = df['last'].max()
        print("price_max =",price_max)
        logging.info('price_max' + str(price_max))
        
        #volume analysis
        vol_min = df['vol'].min()
        print("vol_min =",vol_min)
        vol_max = df['vol'].max()
        print("vol_max =",vol_max)

        '''
        If the current price is more than 5% higher than the lowest price over the last 5 minutes, we will execute a buy order. Otherwise, if the current price is more than 5% lower than the highest price in the past 5 minutes, we will send a sell order.
        '''

        if df['last'].iloc[-1] > price_min * 1.01:
            submit_order('BUY')
            print('BUY ==', df['last'].iloc[-1])
            logging.info('BUY ==' + df['last'].iloc[-1])
        elif df['last'].iloc[-1] < price_max * 0.599:
            submit_order('SELL')
            logging.info('SELL ==' + df['last'].iloc[-1])


def submit_order(direction):
    ''' place order with IB - exit if order gets filled '''
    generic_order = MarketOrder(direction, 5)
    trade = ib.placeOrder(generic_contract, generic_order)
    ib.sleep(3)
    if trade.orderStatus.status == 'Filled':
        ib.disconnect()
        quit()

# Function to log trade updates
def log_trade_update(trade, fill):
    logging.info(f"Trade Updated: {trade}, Fill Price: {fill.price}, Quantity: {fill.shares}, "
                 f"Order Status: {trade.status}")
    
# Function to handle account summary updates
def handle_account_summary(account_summary):
    for item in account_summary:
        # Split the string data (it might look like: 'BuyingPower 10000 USD')
        parts = item.split()
    
        # Extract the Tag, Value, and Currency from the split data
        if len(parts) == 4:
            # Assuming the first part is the account ID
            account_id = parts[0]
            
            # Extract the tag, value, and currency
            tag = parts[1]
            value = parts[2]
            currency = parts[3]
            
            # Store the data in a dictionary using the tag as the key
            account_data[tag] = {'value': value, 'currency': currency}
    
    # Print out the account summary data
    for tag, data in account_data.items():
        print(f"Tag: {tag}, Value: {data['value']}, Currency: {data['currency']}")
            

# Request the account summary to begin receiving updates
# Initialize variables for parsing
account_data = {}
account_id = '5'  # Default account
tags = ['BuyingPower', 'CashBalance', 'NetLiquidation']  # Tags to request
ib.accountSummary()

# Subscribe to account summary updates
ib.accountSummaryEvent += handle_account_summary

# Create contracts
tick = 'F'
generic_contract = Stock(tick, 'SMART', 'USD')
#visa_contract = Stock('AAPL', 'SMART', 'USD')

ib.qualifyContracts(generic_contract)
#ib.qualifyContracts(visa_contract)

# Request market data for generic stock
ib.reqMarketDataType(3)
ib.reqMktData(generic_contract)


# Set callback function for tick data
ib.pendingTickersEvent += new_data
# Subscribe to order status updates
ib.orderStatusEvent += log_trade_update

# Run infinitely
ib.run()