from thetadata import ThetaClient, OptionReqType, OptionRight, DateRange, DataType, StockReqType
from dotenv import load_dotenv
import os
load_dotenv('secrets.env')
PASSWORD = os.getenv('PASSWORD')
print(PASSWORD)
USERNAME = 'kumarshan25@gmail.com'
client = ThetaClient(username=USERNAME, passwd=PASSWORD, jvm_mem=4, timeout=15)

    # Connect to the Terminal
with client.connect():

    # Make the request
    data = client.get_expirations(
        root='MSFT',
    )