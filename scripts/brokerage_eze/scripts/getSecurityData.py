from emsxapilibrary import EMSXAPILibrary
import market_data_pb2 as mkt

class GetSecurityData: # set username, password, domain, locale, port number and server address details
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.symbol = 'VOD.LSE'

    def get_security_data(self):
        self.xapiLib.login()
        request = mkt.SecurityDataRequest()
        request.Symbol = self.symbol
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_market_data_service_stub().GetSecurityData(
            request)  # API call to fetch data
        print(response)  # accessing response object
        self.xapiLib.logout()

if __name__ == "__main__":
    get_security_data_example = GetSecurityData()
    get_security_data_example.get_security_data()