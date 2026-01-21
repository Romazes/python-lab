from emsxapilibrary import EMSXAPILibrary
import market_data_pb2
import logging


class GetLevel1DelayQuote:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        # Set up logging
        logging.basicConfig(filename='GetLevel1DelayQuote.log', level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')

    def get_level1_delay_quote(self):
        try:
            self.xapiLib.login()
            print('User token: '+self.xapiLib.userToken)
            request = market_data_pb2.Level1MarketDataRecordRequest()  # create Level1 market data record request object
            request.UserToken = self.xapiLib.userToken
            request.Symbols.extend(["VOD.LSE", "BARC.LSE", "GSK.LSE"])  # List of ticker symbols
        # Level1MarketDataRecordRequest supports FieldSelection
        # NOTE: Field selection is commented out as this example demonstrates basic usage
        # without custom field filtering. Uncomment and modify the field_selection code below
        # to request specific fields instead of all available fields.
        # Optional: Configure field selection to retrieve only specific market data fields
        # This improves performance by reducing data transfer and processing overhead
        # Uncomment the following code to enable custom field selection instead of retrieving all available fields
        #
        # Example usage:
        # field_selection = market_data_pb2.Level1FieldOptions()
        # field_selection.RequestedFields.extend([
        #     market_data_pb2.Level1FieldOptions.Fields.DISP_NAME,      # Display name
        #     market_data_pb2.Level1FieldOptions.Fields.TRDPRC1,        # Last trade price
        #     market_data_pb2.Level1FieldOptions.Fields.BID,            # Bid price
        #     market_data_pb2.Level1FieldOptions.Fields.ASK,            # Ask price
        # ])
        # request.FieldSelection.CopyFrom(field_selection)
        #
        # For extended fields (custom FIDs), also uncomment:
        # field_selection.RequestedExtendedFields.extend([
        #     "Sedol",        # SEDOL identifier
        #     "Cusip",        # CUSIP identifier
        #     "Dividend",     # Dividend amount
        # ])

        # ALTERNATIVE FIELD SELECTION EXAMPLE:
        # The following is a more comprehensive field selection example that requests
        # many common Level 1 fields including display name, prices, timestamps, and
        # extended fields. Uncomment this block instead of the basic example above
        # for more detailed market data retrieval.
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
            logging.info(f'Server Response: {response.Acknowledgement.ServerResponse} | Message: {response.Acknowledgement.Message}')

            for data in response.DataRecord:
                print(data)
                logging.info(f'Data: {data}')
                    
        except Exception as e:
            error_msg = f'Error during API call: {str(e)}'
            print(error_msg)
            logging.error(error_msg, exc_info=True)
            raise
    # self.xapiLib.logout()
    # self.xapiLib.close_channel()


if __name__ == "__main__":
    get_level1_delay_quote_example = GetLevel1DelayQuote()
    get_level1_delay_quote_example.get_level1_delay_quote()
