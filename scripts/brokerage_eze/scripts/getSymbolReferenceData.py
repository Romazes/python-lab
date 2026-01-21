from emsxapilibrary import EMSXAPILibrary
import market_data_pb2 as mkt

class GetSymbolReferenceData: # set username, password, domain, locale, port number and server address details
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.symbol = 'VOD.LSE'

    def get_symbol_reference_data(self):
        self.xapiLib.login()
        request = mkt.SymbolReferenceDataRequest()
        request.Symbol = self.symbol
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_market_data_service_stub().GetSymbolReferenceData(
            request)  # API call to fetch data
        print(response)  # accessing response object
        self.xapiLib.logout()

if __name__ == "__main__":
    get_symbol_reference_data_example = GetSymbolReferenceData()
    get_symbol_reference_data_example.get_symbol_reference_data()