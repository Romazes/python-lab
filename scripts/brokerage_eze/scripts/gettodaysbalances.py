from emsxapilibrary import EMSXAPILibrary
import utilities_pb2 as util


class GetTodaysBalances:
    def __init__(self):  # set username, password, domain, locale, port number and server address details
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_todays_balances(self):
        self.xapiLib.login()

        request = util.TodaysBalancesRequest()  # create today's activity request object
        request.UserToken = self.xapiLib.userToken

        response = self.xapiLib.get_utility_service_stub().GetTodaysBalances(request)  # API call to fetch today's activity
        print(response.Acknowledgement.ServerResponse)  # accessing response object
        i = 0
        for deposit_record in response.DepositList:
            print("--------------- Deposit Num: ", i, " START ---------------")
            print(deposit_record)
            print("--------------- Deposit Num: ", i, " END ---------------")
            i = i + 1

        self.xapiLib.logout()

if __name__ == "__main__":
    todays_balance_example = GetTodaysBalances()  # password
    todays_balance_example.get_todays_balances()