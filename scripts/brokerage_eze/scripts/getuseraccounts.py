import order_pb2
from emsxapilibrary import EMSXAPILibrary


class GetUserAccounts:
    def __init__(self):  # set username, password, domain, locale, port number and server address details
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_user_accounts(self):
        self.xapiLib.login()

        request = order_pb2.UserAccountsRequest()  # create user accounts request object
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_order_service_stub().GetUserAccounts(request)  # API call to fetch user accounts
        print(response.Acknowledgement.ServerResponse)  # accessing response object
        print(response.Accounts)

        self.xapiLib.logout()


if __name__ == "__main__":
    user_accounts_example = GetUserAccounts()  # password
    user_accounts_example.get_user_accounts()