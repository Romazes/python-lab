from emsxapilibrary import EMSXAPILibrary
import utilities_pb2


class GetTodaysActivity:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_todays_activity(self):
        self.xapiLib.login()

        request = utilities_pb2.TodaysActivityRequest() # create today's activity request object
        request.UserToken = self.xapiLib.userToken

        # To Filter based on Order Type - set to True
        # request.IncludeUserSubmitOrder = False
        # request.IncludeUserSubmitStagedOrder = False
        # request.IncludeUserSubmitCompoundOrder = False
        # request.IncludeForeignExecution = False
        # request.IncludeUserSubmitChange = False
        # request.IncludeUserSubmitCancel = False
        # request.IncludeExchangeAcceptOrder = False
        # request.IncludeExchangeTradeOrder = False
        # request.IncludeUserSubmitTradeReport = False
        # request.IncludeUserSubmitAllocation = False
        # request.IncludeUserSubmitAllocationEx = False
        # request.IncludeClerkReject = False

        # To Filter based on CurrentStatus as Completed - set to True
        # request.IncludeOnlyCompleted = False

        # To Filter based UserSubmitStagedOrder and its child - set to True
        # request.UserSubmitStagedOrderFullInfo = False

        response = self.xapiLib.get_utility_service_stub().GetTodaysActivity(request)  # API call to fetch today's activity
        print('Server Response: '+response.Acknowledgement.ServerResponse + ' | Message: '+response.Acknowledgement.Message)
        i = 0
        for order_record in response.OrderRecordList:
            print("--------------- Order Num: ", i, " START ---------------")
            print(order_record)
            print("--------------- Order Num: ", i, " END ---------------")
            i = i + 1
        self.xapiLib.logout()
        self.xapiLib.close_channel()

if __name__ == "__main__":
    todays_activity_example = GetTodaysActivity()
    todays_activity_example.get_todays_activity()
