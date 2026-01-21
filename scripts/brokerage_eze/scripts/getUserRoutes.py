import utilities_pb2 as util
import utilities_pb2_grpc as util_grpc
from emsxapilibrary import EMSXAPILibrary

class GetUserRoutesDemo:  # set username, password, domain, locale, port number and server address details
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_user_routes(self):
        self.xapiLib.login()

        request = util.GetUserRoutesRequest()
        request.UserToken = self.xapiLib.userToken
        # Optionally set AccountList:
        # request.AccountList = "BANK;BRANCH;CUSTOMER;ACCOUNT"

        response = self.xapiLib.get_utility_service_stub().GetUserRoutes(request)

        if response:
            print(response.Acknowledgement.ServerResponse)
            if len(response.UserRoutes) > 0:
                for key, value in response.UserRoutes.items():
                    print(f"Account: {key} | Routes: {value}")

        self.xapiLib.logout()

if __name__ == "__main__":
    get_user_routes_demo = GetUserRoutesDemo()
    get_user_routes_demo.get_user_routes()