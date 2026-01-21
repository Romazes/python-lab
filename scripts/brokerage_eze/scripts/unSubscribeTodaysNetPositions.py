
from emsxapilibrary import EMSXAPILibrary
import utilities_pb2

class UnSubscribeTodaysNetPositions:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def un_subscribe_net_positions(self):
        request = utilities_pb2.UnSubscribeNetPositionsRequest()  # create request object
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_utility_service_stub().UnSubscribeTodaysNetPositions(request) # API call to Unsubscribe Position Data
        print(response)

if __name__ == "__main__":
    un_subscribe_net_positions_example = UnSubscribeTodaysNetPositions()  # password
    un_subscribe_net_positions_example.xapiLib.login()
    un_subscribe_net_positions_example.un_subscribe_net_positions()
    un_subscribe_net_positions_example.xapiLib.logout()
    un_subscribe_net_positions_example.xapiLib.close_channel()




