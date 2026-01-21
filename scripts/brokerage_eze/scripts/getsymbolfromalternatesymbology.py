from emsxapilibrary import EMSXAPILibrary
import market_data_pb2 as mkt


class GetSymbolFromAlternateSymbology:  # set username, password, domain, locale, port number and server address details
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_symbol_from_alternate_symbology(self):
        try:
            self.xapiLib.login()
            print('User token: ' + self.xapiLib.userToken)

            request = mkt.SymbolFromAlternateSymbologyRequest()  # create symbolfromalternatesymbologyrequest
            request.Symbol = '037833100'  # any valid symbol such as Isin, Sedol, RIC, Cusip or BBG id
            request.SymbolInfo.SymbolOption = 3  # alternate symbology enum. Isin = 0, Sedol = 1 , RIC = 2, Cusip = 3 or BBG = 4
            request.UserToken = self.xapiLib.userToken
            
            response = self.xapiLib.get_market_data_service_stub().GetSymbolFromAlternateSymbology(
                request)  # API call to fetch symbol info from alternate symbology
            
            # Validate response
            if hasattr(response, 'Acknowledgement'):
                print('Server Response: ' + response.Acknowledgement.ServerResponse + 
                      ' | Message: ' + response.Acknowledgement.Message)
                
                if response.Acknowledgement.ServerResponse != "success":
                    print(f'API Error: {response.Acknowledgement.Message}')
                    return
            
            # Check if SymbolInfolist exists and has elements
            if hasattr(response, 'SymbolInfolist') and response.SymbolInfolist:
                print(f'Found {len(response.SymbolInfolist)} symbol(s):')
                for i, symbol_info in enumerate(response.SymbolInfolist):
                    print(f'Symbol {i+1}: {symbol_info}')
            else:
                print('No records found - SymbolInfolist is empty or not present')
                
        except Exception as e:
            print(f'Error: {e}')
        finally:
            try:
                self.xapiLib.logout()
            except Exception as e:
                print(f'Logout error: {e}')


if __name__ == "__main__":
    symbol_from_alternate_symbology_example = GetSymbolFromAlternateSymbology()  # password
    symbol_from_alternate_symbology_example.get_symbol_from_alternate_symbology()
