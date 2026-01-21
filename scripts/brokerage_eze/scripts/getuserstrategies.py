import utilities_pb2 as util
import utilities_pb2_grpc as util_grpc
from emsxapilibrary import EMSXAPILibrary
from threading import Event

class GetUserStrategies:  # set username, password, domain, locale, port number and server address details
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()


    def get_user_strategies(self):
        self.xapiLib.login()

        request = util.StrategyListRequest()  # create strategy list request object
        request.FirmName = 'ABC@DOMAIN'  # Firm Name
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_utility_service_stub().GetStrategyList(request)  # API call to fetch list of strategies for given user

        if response:
            print(response.Acknowledgement.ServerResponse)  # accessing response object
            if(len(response.StrategyList) > 0):
                sym = response.StrategyList[0]
                print("Firmname:" + sym.FirmName + " Username:" + sym.UserName + " AlgoName:" + sym.AlgoName + " StrategyName:" + sym.StrategyName)

        self.xapiLib.logout()

if __name__ == "__main__":
    get_User_Strategies = GetUserStrategies()
    get_User_Strategies.get_user_strategies()