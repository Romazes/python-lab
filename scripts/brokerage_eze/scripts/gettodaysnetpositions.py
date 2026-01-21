from emsxapilibrary import EMSXAPILibrary
import utilities_pb2 as util


class GetTodaysNetPositions:
    def __init__(self):  # set username, password, domain, locale, port number and server address details
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_todays_net_positions(self):
        self.xapiLib.login()  

        request = util.TodaysNetPositionsRequest()  # create today's net positions request object
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_utility_service_stub().GetTodaysNetPositions(request)  # API call to fetch today's net positions
        print(response.Acknowledgement.ServerResponse)  # accessing response object
        if(len(response.AggregatePositionsList)>0):
            print(response.AggregatePositionsList[0])
        else:
            print('No position found')

        self.xapiLib.logout()  

if __name__ == "__main__":
    todays_net_positions_example = GetTodaysNetPositions()
    todays_net_positions_example.get_todays_net_positions()
