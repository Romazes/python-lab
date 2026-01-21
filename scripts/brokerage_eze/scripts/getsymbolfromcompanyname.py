from emsxapilibrary import EMSXAPILibrary
import market_data_pb2 as mkt


class GetSymbolFromCompanyName:  # set username, password, domain, locale, port number and server address details
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()


    def get_symbol_from_company_name(self):
        self.xapiLib.login()

        request = mkt.SymbolsFromCompanyNameRequest()  # create symbol from company name request object
        request.CompanyName = 'Microsoft Corporation'  # Company Name
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_market_data_service_stub().GetSymbolsFromCompanyName(
            request)  # API call to fetch symbol info from company name
        print(response.Acknowledgement.ServerResponse)  # accessing response object
        print(response.SymbolDatalist)

        self.xapiLib.logout()


if __name__ == "__main__":
    symbol_from_company_name_example = GetSymbolFromCompanyName()  # password
    symbol_from_company_name_example.get_symbol_from_company_name()
