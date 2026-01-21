from emsxapilibrary import EMSXAPILibrary
import market_data_pb2_grpc
import market_data_pb2 as mkt
from threading import Event


class GetDailyWeeklyMonthlyBars:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_daily_weekly_monthly_bars(self):
        self.xapiLib.login()
        request = mkt.DailyWeeklyMonthlyBarsRequest()  # create daily weekly monthly bars request object
        request.Symbol = 'M'  # The ticker symbol
        request.Interim.BarIntervalOption = 1  # Bar Interval Enum. 0: Daily, 1: Weekly or 2: Monthly
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_market_data_service_stub().GetDailyWeeklyMonthlyBars(request)  # API call to fetch dailyweeklymonthlybars
        print(response.Acknowledgement.ServerResponse)  # accessing response object
        print(response.BarFields.AcVol1)
        print(response.BarFields.High1)
        print(response.BarFields.Low1)

        self.xapiLib.logout()

if __name__ == "__main__":
    bars_example = GetDailyWeeklyMonthlyBars()  # password
    bars_example.get_daily_weekly_monthly_bars()

