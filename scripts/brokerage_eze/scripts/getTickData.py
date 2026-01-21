from emsxapilibrary import EMSXAPILibrary
import market_data_pb2 as mkt
from datetime import datetime
from datetime import timedelta
import uuid


class CTickData:
    def __init__(self): # set username, password, domain, locale, port number and server address details
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()


    def getTickData(self):
        self.xapiLib.login()

        data = {
             "Symbol"   : 'symbol',
             "TickTypes": [{"TickOption": 0}, {"TickOption": 1}, {"TickOption": 2}]  #TRADE = 0;BID = 1;ASK = 2;REGIONAL_BID = 3;REGIONAL_ASK = 4;DELETED = 11;INSERTED = 12;IRREGULAR_DELETE = 44;FORM_T_TRADE = 32;
             }

        request = mkt.TickDataRequest(**data) # create getTickData request object
        request.UserToken = self.xapiLib.userToken
        request.Date.FromDatetime(datetime.now()) #The end date for the query, i.e. the most recent date for which Ticks should be retrieved.  If null, defaults to the current date.
        request.StartTime.FromTimedelta(timedelta(hours=12, minutes=10, seconds=50)) 	#Records earlier in the day than this start time will be excluded.  If null, there is no restriction.
        request.StopTime.FromTimedelta(timedelta(hours=20, minutes=30, seconds=40))  	#Records later in the day than this stop time will be excluded.  If null, there is no restriction.
        # Generate unique request ID using UUID (limited to 31-bit positive integer to fit protocol constraints)
        # NOTE: This reduces the UUID from 128-bit to 31-bit randomness, creating ~2.1 billion possible values
        # In high-volume scenarios (>1000 requests/second), there's a small but non-zero collision probability
        # Consider using a counter-based approach or full UUID if protocol constraints allow
        # Collision probability formula: P = 1 - e^(-k(k-1)/(2N)) where k=requests, N=2^31
        request.RequestId.value = uuid.uuid4().int & (1<<31)-1
        response = self.xapiLib.get_market_data_service_stub().GetTickData(request) # API call to fetch tickdata
        print(response)
        print(response.Acknowledgement.ServerResponse) # accessing response object

        self.xapiLib.logout()

if __name__ == "__main__":
    tick_data_example = CTickData()  # password
    tick_data_example.getTickData()


