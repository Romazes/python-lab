import utilities_pb2 as util
import utilities_pb2_grpc as util_grpc
from emsxapilibrary import EMSXAPILibrary

class GetUserRouteProperties: 
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_user_route_properties(self):
        self.xapiLib.login()
        request = util.GetUserRoutePropsRequest()
        request.UserToken = self.xapiLib.userToken
        request.FilterRoutesList = "CITI-ALGO"  # specify the route name to filter the Route
        request.FilterRoutePropsList = "AlgoType" # specify the route property to filter the Route Properties
        response = self.xapiLib.get_utility_service_stub().GetUserRouteProps(request)
        if response:
            print(response.Acknowledgement.ServerResponse)
            if len(response.UserRouteProps) > 0:
                for key, value in response.UserRouteProps.items():
                    print(f"Route:: {key} ")
                    print(f"Route-Properties :: \n {value}")
            else:
                print("No Route Properties found")
        self.xapiLib.logout()

if __name__ == "__main__":
    get_user_route_prop_demo = GetUserRouteProperties()
    get_user_route_prop_demo.get_user_route_properties()