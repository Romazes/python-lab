from emsxapilibrary import EMSXAPILibrary
import market_data_pb2 as mkt

class GetOptionChainForUnderlier:  # set username, password, domain, locale, port number and server address details
    def __init__(self):
        self.market_tub = None
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_optionchain_for_underlier(self):
        self.xapiLib.login()
        request = mkt.OptionChainRequest()  # create option chain request object
        request.UserToken = self.xapiLib.userToken
        request.SymbolRoot = 'M'  # The underlier symbol, e.g. a stock symbol or future root
        response = self.xapiLib.get_market_data_service_stub().GetOptionChainForUnderlier(request)  # API call to fetch option chain for underlier
        print(response.Acknowledgement.ServerResponse)  # accessing response object
        print(response.Derivative)

        self.xapiLib.logout()


if __name__ == "__main__":
    option_chain_for_underlier_example = GetOptionChainForUnderlier()  # password
    option_chain_for_underlier_example.get_optionchain_for_underlier()
