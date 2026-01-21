from emsxapilibrary import EMSXAPILibrary
import market_data_pb2
from threading import Event, Thread
import time

class RequestAndWatchLevel1Data:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ready = Event()
        self.stop = Event()

    def start_listening(self):
        # start thread to listen to updates from the server about our orders
        self.thread = Thread(target=self._request_and_watch_level1_data)
        self.thread.start()

        # wait for the subscription thread to signal ready
        self.ready.wait()
    def _request_and_watch_level1_data(self):
        request = market_data_pb2.Level1MarketDataRequest()  # create Level1 market data request object
        request.UserToken = self.xapiLib.userToken
        request.Symbols.extend(["AAPL", "VOD.LSE", "BARC.LSE", "GSK.LSE"])  # List of ticker symbols
        request.Advise = True  # If true, real-time updates from the server will be registered for.
        request.Request = True  # If true, a current snapshot of the data will be retrieved
        response = self.xapiLib.get_market_data_service_stub().SubscribeLevel1Ticks(request)  # API call to fetch Level1 market data
        self.ready.set()

        for data in response:
            if (self.stop.is_set()):
                print('time to stop reading responses')
                break
            try:
                if data.Acknowledgement.ServerResponse == "success":
                    if not data.Ask.Isnull and data.Ask.DecimalValue != 0.0:
                        print('DispName:{0} SymbolDesc:{1} Ask:{2} '.format(data.DispName, data.SymbolDesc,
                                                                            data.Ask.DecimalValue))
                    if not data.Bid.Isnull and data.Bid.DecimalValue != 0.0:
                        print('DispName:{0} SymbolDesc:{1} Bid:{2}'.format(data.DispName, data.SymbolDesc,
                                                                           data.Bid.DecimalValue))

                    #print('NasFarIndClearing : {0}'.format(get_value_in_scalar_map_by_key(data.ExtendedFields, 'NasFarIndClearing')))
                    #print('NasNearIndClearing : {0}'.format(get_value_in_scalar_map_by_key(data.ExtendedFields, 'NasNearIndClearing')))
                    #print('NysPaired : {0}'.format(get_value_in_scalar_map_by_key(data.ExtendedFields, 'NysPaired')))
                    #print('NysReferencePrice : {0}'.format(get_value_in_scalar_map_by_key(data.ExtendedFields, 'NysReferencePrice')))
                    #print('NysClearing : {0}'.format(get_value_in_scalar_map_by_key(data.ExtendedFields, 'NysClearing')))
                    #print('NysBookClearing : {0}'.format(get_value_in_scalar_map_by_key(data.ExtendedFields, 'NysBookClearing')))
                    #print('ExpirDate : {0}'.format(get_value_in_scalar_map_by_key(data.ExtendedFields, 'ExpirDate')))
                    if data.ExtendedFields is not None:
                        print('DispName:{0} SymbolDesc:{1} Ask:{2} '.format(data.DispName, data.SymbolDesc,
                                                                            data.Ask.DecimalValue))
                else:
                    print('Server Response: {0} Error Message : {1} '.format(data.Acknowledgement.ServerResponse
                                                                             , data.Acknowledgement.Message))

            except Exception as e:
                print(e)

def get_value_in_scalar_map_by_key(extended_field_map, key='NysPaired'):
    """
    Function to retrieve and print the value for a given key from a ScalarMapContainer.

    Parameters:
    scalar_map (dict-like): The ScalarMapContainer or dictionary-like object.
    key (str): The key to look up in the extended_field_map (default is 'NysPaired').

    Returns:
    The value associated with the key if found, otherwise None.
    """
    # Get the value associated with the key, or None if the key doesn't exist
    value = extended_field_map.get(key, None)

    # Print the result based on whether the value is found
    #if value is not None:
    #    print(f"Value for '{key}': {value}")
    #else:
    #   print(f"'{key}' does not exist or has no value")

    return value

# Example usage:
# extended_field_map = data.ExtendedFields
# get_value_in_scalar_map_by_key(extended_field_map,'key')


if __name__ == "__main__":
    request_and_watch_level1_data_example = RequestAndWatchLevel1Data()  # password
    request_and_watch_level1_data_example.xapiLib.login()
    request_and_watch_level1_data_example.start_listening()
    time.sleep(10)
    request_and_watch_level1_data_example.stop.set()
    request_and_watch_level1_data_example.xapiLib.logout()
    request_and_watch_level1_data_example.xapiLib.close_channel()


