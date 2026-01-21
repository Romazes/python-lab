from emsxapilibrary import EMSXAPILibrary
import market_data_pb2


class GetLevel1MarketData:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def get_level1_market_data(self):
        self.xapiLib.login()
        print('User token: '+self.xapiLib.userToken)
        request = market_data_pb2.Level1MarketDataRecordRequest()  # create Level1 market data record request object
        request.UserToken = self.xapiLib.userToken
        request.Symbols.extend(["VOD.LSE", "BARC.LSE", "GSK.LSE"])  # List of ticker symbols
        # Level1MarketDataRecordRequest supports FieldSelection
        # field_selection = market_data_pb2.Level1FieldOptions()
        # field_selection.RequestedFields.extend([
        #     market_data_pb2.Level1FieldOptions.Fields.DISP_NAME,
        #     market_data_pb2.Level1FieldOptions.Fields.TRDPRC1,
        #     market_data_pb2.Level1FieldOptions.Fields.TRDTIM1,
        #     market_data_pb2.Level1FieldOptions.Fields.SYMBOL_DESC,
        #     market_data_pb2.Level1FieldOptions.Fields.COMPANY_NAME,
        #     market_data_pb2.Level1FieldOptions.Fields.ARCA_IMBALANCE_VOLUME,
        #     market_data_pb2.Level1FieldOptions.Fields.ARCA_MATCH_VOLUME,
        #     market_data_pb2.Level1FieldOptions.Fields.SALE_CONDITION_VOLUME,
        #     market_data_pb2.Level1FieldOptions.Fields.INTRADAY_HIGH_COUNT,
        #     market_data_pb2.Level1FieldOptions.Fields.VWAP_VOL,
        #     market_data_pb2.Level1FieldOptions.Fields.VWAP,
        #     market_data_pb2.Level1FieldOptions.Fields.BID,
        #     market_data_pb2.Level1FieldOptions.Fields.ASK,
        #     market_data_pb2.Level1FieldOptions.Fields.CHANGE_LAST,
        #     market_data_pb2.Level1FieldOptions.Fields.HIGH1,
        #     market_data_pb2.Level1FieldOptions.Fields.HIGH52,
        #     market_data_pb2.Level1FieldOptions.Fields.LOW1,
        #     market_data_pb2.Level1FieldOptions.Fields.LOW52,
        #     market_data_pb2.Level1FieldOptions.Fields.EXTENDED_FIELDS
        # ])
        # Add specific extended fields (FIDs) to test
        # field_selection.RequestedExtendedFields.extend([
        #     "Sedol",        # SEDOL identifier
        #     "Cusip",        # CUSIP identifier
        #     "Dividend",     # Dividend amount
        #     "Peratio",      # Price-to-earnings ratio
        #     "ExchName",     # Exchange name
        #     "Currency"      # Currency
        # ])
        # request.FieldSelection.CopyFrom(field_selection)

        response = self.xapiLib.get_market_data_service_stub().GetLevel1MarketData(request)  # API call to fetch Level1 market data
        print('Server Response: '+response.Acknowledgement.ServerResponse + ' | Message: '+response.Acknowledgement.Message)

        for data in response.DataRecord:
            print(data)
    # self.xapiLib.logout()
    # self.xapiLib.close_channel()


if __name__ == "__main__":
    get_level1_market_data_example = GetLevel1MarketData()
    get_level1_market_data_example.get_level1_market_data()
    
