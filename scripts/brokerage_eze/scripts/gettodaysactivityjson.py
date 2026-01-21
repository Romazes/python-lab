from emsxapilibrary import EMSXAPILibrary
import utilities_pb2 as util
import json


class GetTodaysActivityJson:
    def __init__(self):  # set username, password, domain, locale, port number and server address details
       EMSXAPILibrary.create()
       self.xapiLib = EMSXAPILibrary.get()

    def get_todays_activity_json(self):
        self.xapiLib.login()

        request = util.TodaysActivityJsonRequest()  # create today's activity_json request object
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_utility_service_stub().GetTodaysActivityJson(request)  # API call to fetch today's activity in JSON format
        response_json = json.loads(response.TodaysActivityJson)
        if len(response_json) == 0 or response_json is None :
            print('No data returned')
        elif not response_json[0] is None:
            print(response_json[0])

        self.xapiLib.logout()


if __name__ == "__main__":
    todays_activity_json_example = GetTodaysActivityJson()  # password
    todays_activity_json_example.get_todays_activity_json()
