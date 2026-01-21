import time
from threading import Event, Thread
import utilities_pb2
from emsxapilibrary import EMSXAPILibrary

class SubscribeHeartbeat:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapilib = EMSXAPILibrary.get()

    def _send_heartbeat_request(self):
        try:
            self.xapilib.login()
            subscribe_request = utilities_pb2.SubscribeHeartBeatRequest()
            subscribe_request.UserToken = self.xapilib.userToken
            subscribe_request.TimeoutInSeconds = 15
            subscribe_response = self.xapilib.utilitySvcStub.SubscribeHeartBeat(subscribe_request)
            self.ready.set()

            for resp in subscribe_response:
                print(resp.Acknowledgement.ServerResponse)

        except Exception as e:
            print(e)

if __name__ == '__main__':
    try:
        subscribe_to_heartbeat = SubscribeHeartbeat()
        subscribe_to_heartbeat.xapilib.login()
        subscribe_to_heartbeat.xapilib.start_listening_heartbeat(5)

        time.sleep(15)  # time in seconds to wait before logging out
        subscribe_to_heartbeat.xapilib.suspend_heartbeat_thread()
        subscribe_to_heartbeat.xapilib.logout()
        subscribe_to_heartbeat.xapilib.close_channel()
    except Exception as e:
        print(e)
