from emsxapilibrary import EMSXAPILibrary
import utilities_pb2 as util


class GetTodaysBrokenDownPositions:
    def __init__(self):  # set username, password, domain, locale, port number and server address details
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.BBCDFilter = ""  # "BANK;BRANCH;CUSTOMER;DEPOSIT"
        self.TickerFilter = ""  # "Ticker1;Ticker2;Ticker3...."

    def get_todays_brokendown_positions(self):
        self.xapiLib.login()

        request = util.TodaysBrokenDownPositionsRequest()  # create today's broken down positions request object
        request.UserToken = self.xapiLib.userToken
        request.BBCDFilter = self.BBCDFilter
        request.TickerFilter = self.TickerFilter
        response = self.xapiLib.get_utility_service_stub().GetTodaysBrokenDownPositions(request)  # API call to fetch today's broken down positions
        print(response.Acknowledgement.ServerResponse)  # accessing response object
        # Sample script to Aggregate Long Positions from the filtered response
        # Similar can be done for ShortPos etc...
        position_records = response.PositionRecords
        numOfRecords = 0
        ticker_dic_for_bought_qty = {}  # Creating Dictionary
        for pos in position_records:
            numOfRecords = numOfRecords + 1
            print('-------------------------------------------------------')
            print(' ORDER NUMBER - ', numOfRecords, '\n')
            print(pos)
            if pos.DispName not in ticker_dic_for_bought_qty:
                ticker_dic_for_bought_qty[pos.DispName] = 0
            ticker_dic_for_bought_qty[pos.DispName] = ticker_dic_for_bought_qty[
                                                          pos.DispName] + pos.Longpos + pos.Longpos0
            print('-------------------------------------------------------')
        print(' TOTAL ORDERS FETCHED - ', numOfRecords)
        print('AGGREGATE LONG POSITIONS')
        print(ticker_dic_for_bought_qty)

        self.xapiLib.logout()


if __name__ == "__main__":
    todays_brokendown_positions_example = GetTodaysBrokenDownPositions()  # password
    todays_brokendown_positions_example.get_todays_brokendown_positions()