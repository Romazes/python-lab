import grpc
import time
from datetime import datetime, timedelta
from threading import Event, Thread
from uuid import uuid4
from srp import *
import hashlib
import order_pb2 as ord
import order_pb2_grpc as ord_grpc
import utilities_pb2 as util
import utilities_pb2_grpc as util_grpc

class CreateParentThenRouteChildOrderExample:
    def __init__(self):
        self.user               =  'USERNAME'
        self.domain             =  'DOMAIN'
        self.locale             =  'LOCALE'  
        self.password           =  'PASSWORD'    
        self.server             =  'HOST_ADDRESS' 
        self.parent_child_info  = {
            'SYMBOL1': {
            'Parent_Quantity'   : parent_quantity1,                     #example: 1000
            'Side'              : 'BUY/SELL',
            'Parent_Price'      : '',                                   #NULL if MARKET
            'USSO'              : number_of_parent_orders,              #example: 40
            'Child_Quantity'    : [child_quantities],                   #example:  [500,500]
            'Route_Child'       : 'child_route_name1',                  
            'Child_Account'     : 'BANK,BRANCH,CUSTOMER,DEPOSIT',       #separated by comma
            'Saved_Strategy'    : 'USERNAME@DOMAIN:USER_FIRMNAME:ATDL_TYPE:SAVED_STRATNAME',              
            'Child_Price'       : ''                                    #NULL if MARKET
            },

            'SYMBOL2': {
            'Parent_Quantity'   : parent_quantity2,                     #example: 2000
            'Side'              : 'BUY/SELL',
            'Parent_Price'      : 'parent_price',                       #NULL if MARKET #example:'120'
            'USSO'              : number_of_parent_orders,              #example: 40
            'Child_Quantity'    : [child_quantities],                   #example:  [500,500,600,400]
            'Route_Child'       : 'child_route_name2',
            'Child_Account'     : 'BANK,BRANCH,CUSTOMER,DEPOSIT',       #separated by comma
            'Saved_Strategy'    : 'USERNAME@DOMAIN:USER_FIRMNAME:ATDL_TYPE:SAVED_STRATNAME,             
            'Child_Price'       : 'child_price'                         #example:'0.66'
            },
        }

        #Route is STAGED or broker route, depending on NEUTRAL V Broker acc
        self.route_parent             = 'NONE'
        #self.staged will determine if Parent or not
        self.staged_parent            =  True
        self.claim_req_parent         =  False
        self.parent_account           = 'BANK;BRANCH;CUSTOMER;DEPOSIT'  
        self.staged_child             = False
        self.port                     = 9000
        self.ready                    = Event()
        self.order_live               = False
        self.store_order_tag          = []

    def setup(self):
        if not self.connect(): # Establish a secure channel to server
            print("Error establishing secure channel to server!")
            return False
        else:
            if not self.srp_login(): # Login via SRP
                print("Error in SRP Login!")
                return False
            else:
                return True
    
    def connect(self):
        try:
            with open(r'roots.pem', 'rb') as f:  # path to roots.pem file
                cert_data = f.read()

            credentials = grpc.ssl_channel_credentials(root_certificates=cert_data)
            options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
            channel = grpc.secure_channel('{0}:{1}'.format(self.server, self.port), credentials, options) # connecting to server
                                                                                                 # via secure channel
        
            self.util_stub = util_grpc.UtilityServicesStub(channel) # creating client stubs needed to invoke the APIs
            self.ord_stub = ord_grpc.SubmitOrderServiceStub(channel)
            print("Established secure channel to server...")

            return True
        except Exception as e:
            print(e)
            return False
    
    def start_listening(self):
        # start thread to listen to updates from the server about our orders        
        self.thread = Thread(target=self.subscribe_order_info)
        self.thread.start()
        # wait for the subscription thread to signal ready
        self.ready.wait()
    
    def srp_login(self):
        try:
            srp_login = util.StartLoginSrpRequest(UserName=self.user,
                                                  Domain=self.domain) # create request object for StartLoginSrp API

            print('Connecting...')
            resp_Startloginsrp = self.util_stub.StartLoginSrp(srp_login) # step1 of SRP Login process

            if resp_Startloginsrp.Response == 'success':
                ############################# regionSRPcalculations Begin
                u_name = self.user
                domain_connect = self.domain
                identity = "@".join([u_name.upper(), domain_connect.upper()])
                pswrd_connect = self.password
                locale_connect = self.locale

                srp_transactid = resp_Startloginsrp.srpTransactId
                srp_g = resp_Startloginsrp.srpg
                srp_n = resp_Startloginsrp.srpN
                srp_b = resp_Startloginsrp.srpb
                srp_salt = resp_Startloginsrp.srpSalt
                srp_salt_byte = bytes.fromhex(srp_salt)
                int_b = int('0' + srp_b)
                srp_b_bytes = int_b.to_bytes(128, 'big')
                int_n = int('0' + srp_n)
                bytes_n = int_n.to_bytes(128, 'big')
                hex_s_n = bytes_n.hex()
                int_g = int('0' + srp_g)
                bytes_g = int_g.to_bytes(128, 'big')
                hex_g = bytes_g.hex()
                if hex_s_n and srp_g:
                    usr = _pysrp.User(identity, pswrd_connect, hash_alg=SHA256, ng_type=NG_CUSTOM, n_hex=hex_s_n,
                                      g_hex=hex_g)
                    concate_ng = bytes_n + bytes_g
                    k_ng = hashlib.sha256(concate_ng).hexdigest()
                    k_bytes = bytes.fromhex(k_ng)
                    usr.k = int.from_bytes(k_bytes, 'big')
                    uname, A = usr.start_authentication()
                if A is None:
                    print("Failed")
                srp_Ax = int.from_bytes(A, 'big')
                # Server => Client: s, B
                M = usr.process_challenge(srp_salt_byte, srp_b_bytes)
                if M is None:
                    print("Failed")
                srp_M_hex = M.hex()
                ############################# regionSRPcalculations End

                srp_complogin = util.CompleteLoginSrpRequest(Identity=identity,
                                                             srpTransactId=srp_transactid,
                                                             strEphA=str(srp_Ax),
                                                             strMc=srp_M_hex,
                                                             UserName=u_name, Domain=domain_connect.upper(),
                                                             Locale=locale_connect.upper()) # step2 of SRP Login process
                connect_response = self.util_stub.CompleteLoginSrp(srp_complogin)
                if not connect_response.Response == 'success':
                    print(connect_response.Response)
                    return False
                print('Connected!')
                self.token = connect_response.UserToken # user token received from server
                return True
            else:
                print('Failed to fetch UserToken')
                return False
        except Exception as e:
            print(e)
            return False
    
    # this is the thread func for the order listener
    def subscribe_order_info(self):
            subscribe_request = ord.SubscribeOrderInfoRequest()
            subscribe_request.Level = 0
            subscribe_request.UserToken = self.token
            
            subscribe_response = self.ord_stub.SubscribeOrderInfo(subscribe_request)
            self.ready.set()
            
            while True:
                try:
                    if subscribe_response:
                        order_info = next(subscribe_response)
                        print('sym:{0} vol:{1} status:{2} oid:{3} tid:{4} r:{5} ot:{6} otype:{7}'.format(order_info.Symbol,
                                                                                                order_info.Volume,
                                                                                                order_info.CurrentStatus,
                                                                                                order_info.OrderId,
                                                                                                order_info.TicketId,
                                                                                                order_info.ExtendedFields['Reason'],
                                                                                                order_info.ExtendedFields['OrderTag'],
                                                                                                order_info.Type))
                                                            
                        # if this is our parent order and it's live, signal to continue
                        if order_info.ExtendedFields['OrderTag'] in self.store_order_tag and order_info.CurrentStatus == 'LIVE' and order_info.Type == 'UserSubmitStagedOrder':
                            print('Parent order is live.')
                            self.send_child_order(order_info.Symbol, order_info.OrderId)
                            self.store_order_tag.remove(order_info.ExtendedFields['OrderTag'])  #remove ordertag once parent qunatity fully traded
                except Exception as e:
                    print(e)
    def wait_for_parent_live(self):
        while not self.order_live:
            time.sleep(1)
    
    def send_parent_order(self):
        # create staged order  
        for p_id,p_info in self.parent_child_info.items():
            count = self.parent_child_info[p_id]['USSO']
            for b in range(count):
                self.my_order_tag                               = 'XAP-{0}'.format(str(uuid4()))
                parent_order                                    = ord.SubmitSingleOrderRequest()
                parent_order.Symbol                             = p_id
                parent_order.Side                               =  self.parent_child_info[p_id]['Side']
                parent_order.Quantity                           = self.parent_child_info[p_id]['Parent_Quantity']                                     
                parent_order.Staged                             = self.staged_parent    
                parent_order.Route                              = self.route_parent
                #parent_order.ExtendedFields['EXIT_VEHICLE'] = 'NONE'
                parent_order.ClaimRequire                       = self.claim_req_parent
                parent_order.UserToken                          = self.token
                parent_order.Account                            = self.parent_account
                parent_order.ExtendedFields['ORDER_TAG']        = self.my_order_tag 
                if self.parent_child_info[p_id]['Parent_Price']:
                    parent_order.ExtendedFields['PRICE']        = self.parent_child_info[p_id]['Parent_Price']
                    parent_order.ExtendedFields['PRICE_TYPE']   = 'LIMIT'    
                parent_submit_response                          = self.ord_stub.SubmitSingleOrder(parent_order)
                print('Parent Order Response:',parent_submit_response)
                self.store_order_tag.append(self.my_order_tag)

    def send_child_order(self,sym,order_id):
        # route child on the staged parent
        count = len(self.parent_child_info[sym]['Child_Quantity'])
        for orderid_run in range(count) :
            child_order                                             = ord.SubmitSingleOrderRequest()
            child_order.ExtendedFields['TICKET_ID']                 = order_id
            child_order.Symbol                                      = sym
            child_order.Side                                        =  self.parent_child_info[sym]['Side']
            child_order.Quantity                                    = self.parent_child_info[sym]['Child_Quantity'][orderid_run]                                   
            child_order.Route                                       = self.parent_child_info[sym]['Route_Child']
            child_order.ExtendedFields['ROUTING_BBCD']              = self.parent_child_info[sym]['Child_Account']
            child_order.ExtendedFields['SAVED_STRATEGY_STRING_ID']  =  self.parent_child_info[sym]['Side'] 
            if self.parent_child_info[sym]['Child_Price']:
                child_order.ExtendedFields['PRICE']                 = self.parent_child_info[sym]['Child_Price']
                child_order.ExtendedFields['PRICE_TYPE']            = 'LIMIT'                    
            child_order.Staged                                      = self.staged_child
            child_order.UserToken                                   = self.token
            child_order.Account                                     = self.parent_account
            #child_order.ExtendedFields['EXIT_VEHICLE'] = 'STAGE'
            #child_order.ExtendedFields['DEST_ROUTE'] = 'DEMOEUR'
            child_submit_response                                  = self.ord_stub.SubmitSingleOrder(child_order)
            print('Child Order Response', child_submit_response)
        return True
            
    
if __name__ == "__main__":
    submit_order = CreateParentThenRouteChildOrderExample()  
    result = submit_order.setup()
    if result: #on success call order blotter streaming and API
        submit_order.start_listening()
        submit_order.send_parent_order()        #calling parent staged order
            
    while True:
        time.sleep(1)

    
    


		
		