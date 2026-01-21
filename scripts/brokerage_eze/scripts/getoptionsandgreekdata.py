from emsxapilibrary import EMSXAPILibrary
import market_data_pb2 as mkt


class GetOptionsAndGreekData:  # set username, password, domain, locale, port number and server address details
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_options_and_greek_data(self):
        self.xapiLib.login()

        request = mkt.OptionsAndGreekDataRequest()  # create optionsandgreekdatarequest object
        request.Symbols.extend([r"M", r"+AAPL\15B9\223", r"+IBM\09D9\150"])  # list of ticker symbols
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_market_data_service_stub().GetOptionsAndGreekData(request)  # API call to fetch options and greek data
        print(response.Acknowledgement.ServerResponse)  # accessing response object
        print(response.OptionsList)

        self.xapiLib.logout()

if __name__ == "__main__":
    options_and_greek_data_example = GetOptionsAndGreekData()  # password
    options_and_greek_data_example.get_options_and_greek_data()
