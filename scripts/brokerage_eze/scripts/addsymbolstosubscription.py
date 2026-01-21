import market_data_pb2
from emsxapilibrary import EMSXAPILibrary


class AddSymbolsToSubscription:  # set username, password, domain, locale, port number and server address details
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def add(self):
        try:
            self.xapiLib.login()
            print('User token: '+self.xapiLib.userToken)

            req_addsym = market_data_pb2.AddSymbolsRequest()
            req_addsym.UserToken = self.xapiLib.userToken
            req_addsym.Symbols.extend([r"IBM", "MSFT"])
            req_addsym.MarketDataLevel = "Level1"
            resp_addsym = self.xapiLib.get_market_data_service_stub().AddSymbols(req_addsym)
            print(resp_addsym.ServerResponse)

            self.xapiLib.login()
            self.xapiLib.close_channel()

        except Exception as e:
            print(e)


if __name__ == "__main__":
    add_symbols_to_subscription = AddSymbolsToSubscription()  # password
    add_symbols_to_subscription.add()
