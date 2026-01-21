import time
from threading import Event, Thread
import utilities_pb2 as util
from emsxapilibrary import EMSXAPILibrary


class SubscribeNetPositions:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ready = Event()

    def start_listening(self):
        # start thread to listen to updates from the server about our orders
        self.thread = Thread(target=self.subscribe_net_position)
        self.thread.start()

        # wait for the subscription thread to signal ready
        self.ready.wait()

    # this is the thread func for the Position listener
    def subscribe_net_position(self):

        subscribe_request = util.SubscribeNetPositionsRequest()
        subscribe_request.UserToken = self.xapiLib.userToken
        subscribe_response = self.xapiLib.get_utility_service_stub().SubscribeTodaysNetPositions(subscribe_request)
        self.ready.set()

        try:
            i = 0
            for positon_info in subscribe_response:
                i = i + 1
                print("---------------- " + str(i) + " ------------------")
                print(positon_info)
                print("----------------------------------")
        except Exception as e:
            print(e)


if __name__ == '__main__':
    position_info = SubscribeNetPositions()
    position_info.xapiLib.login()
    position_info.start_listening()
    time.sleep(1000)
    position_info.xapiLib.logout()
