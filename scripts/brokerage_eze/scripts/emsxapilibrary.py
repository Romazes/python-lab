import datetime
import enum
import hashlib
import grpc
import threading
import time
import os
import socket
from LoginFailedException import LoginFailedException
from NetworkFailedException import NetworkFailedException
from ServerNotAvailableException import ServerNotAvailableException
from SessionNotFoundException import SessionNotFoundException
from SingletonMeta import SingletonMeta
from StreamingAlreadyExistsException import StreamingAlreadyExistsException
from emsxapiconfig import EMSXAPIConfig
from srp import *
from srp import _pysrp

# Import your Python gRPC generated files here, without any package name
# For example:
import utilities_pb2
import utilities_pb2_grpc
import market_data_pb2_grpc
import order_pb2_grpc


class EMSXAPILibrary(metaclass=SingletonMeta):
    def __init__(self, config_file_name = 'config.cfg'):
        self.config = EMSXAPIConfig(config_file_name)
        self._channel = None
        self._utility_svc_stub = None
        self._mkt_data_svc_stub = None
        self._order_service_stub = None
        self.heartbeat_thread = None
        self.is_logged_in = False
        self.heartbeat_exit_signal = False
        self.logged_in_lock = threading.Lock()
        self.error_handler = None
        self.userToken = ''
        self.retry_count = 0
        #self.create_channel(self.config.server, self.config.port)
        self.open_channel()

    instance_lock = threading.Lock()
    instance = None

    @staticmethod
    def create(config_file_name:str = 'config.cfg'):
        with EMSXAPILibrary.instance_lock:
            if EMSXAPILibrary.instance is None:
                EMSXAPILibrary.instance = EMSXAPILibrary(config_file_name)

    @staticmethod
    def get() :
        return EMSXAPILibrary.instance

    def get_is_logged_in(self):
        with self.logged_in_lock:
            return self.is_logged_in

    def set_is_logged_in(self, value):
        with self.logged_in_lock:
            self.is_logged_in = value

    def get_utility_service_stub(self):
        return self._utility_svc_stub

    def get_market_data_service_stub(self):
        return self._mkt_data_svc_stub

    def get_order_service_stub(self):
        return self._order_service_stub
      

    def create_channel(self, host_name, port):
        channel_options = [
            ('grpc.keepalive_time_ms', self.config.keepAliveTime),
            ('grpc.keepalive_timeout_ms', self.config.keepAliveTimeout),
            ('grpc.keepalive_permit_without_calls', 1),
            ('grpc.max_receive_message_length', self.config.maxMessageSize),
            ('grpc.enable_http_proxy', 0)
        ]
        if self.config.ssl and self.config.certFilePath is not None:
            cert_file = self.config.certFilePath
            if not os.path.exists(cert_file):
                raise RuntimeError("Certificate file " + cert_file + " does not exist")
            
            # channel_options.append(('grpc.ssl_target_name_override', 'localhost'))
            with open(cert_file, 'rb') as f:  # path to roots.pem file
                cert_data = f.read()
            credentials = grpc.ssl_channel_credentials(root_certificates=cert_data)
            self._channel = grpc.secure_channel(f"{host_name}:{port}", credentials, channel_options)
        else:
            self._channel = grpc.insecure_channel(f"{host_name}:{port}", options=channel_options)

    def init_stubs(self):
        self._utility_svc_stub = utilities_pb2_grpc.UtilityServicesStub(self._channel)
        self._mkt_data_svc_stub = market_data_pb2_grpc.MarketDataServiceStub(self._channel)
        self._order_service_stub = order_pb2_grpc.SubmitOrderServiceStub(self._channel)

    def _connect(self):
        try:
            connect_request = utilities_pb2.ConnectRequest(
                UserName=self.config.user,
                Domain=self.config.domain,
                Password=self.config.password,
                Locale=self.config.locale
            )
            connect_response = self.get_utility_service_stub().Connect(connect_request)
            if not connect_response.UserToken:
                raise LoginFailedException("Login failed: No user token received")
            self.userToken = connect_response.UserToken
            return True
        except grpc.RpcError as rpc_error:
            raise LoginFailedException(rpc_error.details(), rpc_error)

    def login(self):
        try:
            self.set_is_logged_in(False)
            if(self.config.srpLogin):
                self.set_is_logged_in(self._srp_login())
            else:
                self.set_is_logged_in(self._connect())
            
            if(self.get_is_logged_in() == False):
                raise LoginFailedException('Failed to login')

        except grpc.RpcError as rpc_error:
            raise LoginFailedException(rpc_error.details(), rpc_error)
                
    def _srp_login(self):
        try:
            # create request object for StartLoginSrp API
            srp_login = utilities_pb2.StartLoginSrpRequest(UserName=self.config.user,
                                                  Domain=self.config.domain)

            print('Connecting...')
            resp_start_login_srp = self.get_utility_service_stub().StartLoginSrp(srp_login)  # step1 of SRP Login process

            if resp_start_login_srp.Response == 'success':
                # regionSRPcalculations Begin
                u_name = self.config.user
                domain_connect = self.config.domain
                identity = "@".join([u_name.upper(), domain_connect.upper()])
                pswrd_connect = self.config.password
                locale_connect = self.config.locale

                self.srp_transactid = resp_start_login_srp.srpTransactId
                srp_g = resp_start_login_srp.srpg
                srp_n = resp_start_login_srp.srpN
                srp_b = resp_start_login_srp.srpb
                srp_salt = resp_start_login_srp.srpSalt
                srp_salt_byte = bytes.fromhex(srp_salt)
                int_b = int('0' + srp_b)
                srp_b_bytes = int_b.to_bytes(128, 'big')
                int_n = int('0' + srp_n)
                bytes_n = int_n.to_bytes(128, 'big')
                hex_s_n = bytes_n.hex()
                int_g = int('0' + srp_g)
                bytes_g = int_g.to_bytes(128, 'big')
                hex_g = bytes_g.hex()
                usr = None
                a = None

                if hex_s_n and srp_g:
                    usr = _pysrp.User(identity, pswrd_connect, hash_alg=SHA256, ng_type=NG_CUSTOM, n_hex=hex_s_n,
                                      g_hex=hex_g)
                    concate_ng = bytes_n + bytes_g
                    k_ng = hashlib.sha256(concate_ng).hexdigest()
                    k_bytes = bytes.fromhex(k_ng)
                    usr.k = int.from_bytes(k_bytes, 'big')
                    uname, a = usr.start_authentication()
                if a is None:
                    print("Failed")
                srp_ax = int.from_bytes(a, 'big')
                # Server => Client: s, B
                m = usr.process_challenge(srp_salt_byte, srp_b_bytes)
                if m is None:
                    print("Failed")
                srp_m_hex = m.hex()

                self.kc = usr.K
                self.strEpha = str(srp_ax)
                # regionSRPcalculations End

                # step2 of SRP Login process
                srp_complogin = utilities_pb2.CompleteLoginSrpRequest(Identity=identity,
                                                             srpTransactId=self.srp_transactid,
                                                             strEphA=str(srp_ax),
                                                             strMc=srp_m_hex,
                                                             UserName=u_name, Domain=domain_connect.upper(),
                                                             Locale=locale_connect.upper())
                connect_response = self.get_utility_service_stub().CompleteLoginSrp(srp_complogin)
                if not connect_response.Response == 'success':
                    print(connect_response.Response)
                    return False
                if not connect_response.UserToken:
                    print("Login failed: No user token received")
                    return False
                print('Connected!')
                self.userToken = connect_response.UserToken  # user token received from server
                return True
            else:
                print('Failed to fetch UserToken')
                print(resp_start_login_srp.Response)
                return False
        except Exception as e:
            print(e)
            return False


    def logout(self):
        if not self.get_is_logged_in() or not self.userToken:
            print("Not logged in, skipping logout")
            return
        try:
            dis_conn_req = utilities_pb2.DisconnectRequest(UserToken=self.userToken)

            disconnect_response = self.get_utility_service_stub().Disconnect(dis_conn_req)

            if disconnect_response.ServerResponse == "success":
                print("Logged out")
            else:
                error_message = disconnect_response.OptionalFields["ErrorMessage"]
                print(error_message)
        except grpc.RpcError as rpc_error:
            rpc_error.details()
            rpc_error.code()
        finally:
            self.userToken = ''
            self.set_is_logged_in(False)

    def close_channel(self):
        if self._channel is not None :
            try:
                self._channel._channel.close()
                self._channel._channel.wait_for_state_change(grpc.ChannelConnectivity.IDLE, 5)
            except:
                pass

    def open_channel(self):
        if not self.can_connect_to_internet():
            raise NetworkFailedException("Network not available")
        if self.can_connect_to_server():
            self.close_channel()
            self.create_channel(self.config.server, self.config.port)
            self.init_stubs()
            return
        raise ServerNotAvailableException(f"Server {self.config.server} not responding, might be down.")

    def start_listening_heartbeat(self, req_timeout):
        if not self.get_is_logged_in():
            raise Exception("User needs to login first")

        self.suspend_heartbeat_thread()

        self.heartbeat_exit_signal = False
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_thread_function, args=(req_timeout,))
        self.heartbeat_thread.start()

    def _heartbeat_thread_function(self, req_timeout):
        try:    
            self.heartbeat_exit_signal = False
            refresh_channel = False
            refresh_login = False
            self.retry_count = 0
            while self.get_is_logged_in() and self.retry_count < self.config.maxRetryCount:
                try:
                    if self.heartbeat_exit_signal:
                        break
                    self.retry_count += 1
                    if refresh_channel:
                        self.close_channel()
                        self.open_channel()
                    if refresh_login:
                        self.set_is_logged_in(False)
                        self.login()
                    refresh_channel = False
                    refresh_login = False
                    self.exec_subscribe_heart_beat(req_timeout)
                except grpc.RpcError  as run_ex:
                    # need to initialize the channel again but same token can be re-used
                    delay_ms = self.calculate_delay_millis(self.retry_count)
                    self.write_to_log(f"Error: Runtime IO issue has happened. Attempting again({self.retry_count}) in {delay_ms} ms...")
                    refresh_channel = True
                    refresh_login = False
                    self.sleepMS(delay_ms)
                except SessionNotFoundException as ssn_ex:
                    # need to login again
                    refresh_login = True
                    refresh_channel = False
                    delay_ms = self.calculate_delay_millis(self.retry_count)
                    self.write_to_log(f"Error: User session not found. Attempting login again({self.retry_count}) in {delay_ms} ms...")
                    self.sleepMS(delay_ms)
                except StreamingAlreadyExistsException:
                    # need to login again
                    refresh_login = False
                    refresh_channel = False
                    delay_ms = self.calculate_delay_millis(self.retry_count)
                    self.write_to_log(f"Error: Previous streaming has still not ended on server. Attempting again({self.retry_count}) in {delay_ms} ms...")  # Printing the exception message
                    self.sleepMS(delay_ms)
                except ServerNotAvailableException:
                    # need to login again
                        refresh_channel = True
                        refresh_login = True
                        delay_ms = self.calculate_delay_millis(self.retry_count)
                        self.write_to_log(f"Error: Server seems to be unavailable at the moment. Attempting again({self.retry_count}) in {delay_ms} ms...")  # Printing the exception message
                        self.sleepMS(delay_ms)
                except NetworkFailedException:
                    # need to login again
                        refresh_channel = True
                        refresh_login = False
                        delay_ms = self.calculate_delay_millis(self.retry_count)
                        self.write_to_log(f"Error: Network issues detected on client side. Attempting again({self.retry_count}) in {delay_ms} ms...")  # Printing the exception message
                        self.sleepMS(delay_ms)
                except Exception as ex:
                    self.write_to_log(ex)
                    break

            if(self.retry_count >= self.config.maxRetryCount):
                raise Exception("Fatal: Could not succeed even after multiple retries. Aborting the operation")
                     
        except Exception as ex:
            self.write_to_log(ex)
            if self.error_handler is not None:
                self.error_handler.on_error(ex)

    def sleepMS(self,longDelayMS):
        time.sleep(longDelayMS/1000)

    def exec_subscribe_heart_beat(self, req_timeout):
        subscribe_request = utilities_pb2.SubscribeHeartBeatRequest(
            UserToken=self.userToken,
            TimeoutInSeconds=req_timeout
        )

        hb_response_it = self.get_utility_service_stub().SubscribeHeartBeat(subscribe_request)

        try:
            for response in hb_response_it:
                if self.heartbeat_exit_signal:
                    break
                
                res_status = response.Status
                server_msg = response.Acknowledgement.ServerResponse

                current_time = self.get_current_time()
                log_msg = f"[{current_time}] HeartBeat status: {res_status} | {server_msg}"
                self.write_to_log(log_msg)

                if res_status == HeartBeatStatus.DEAD:
                    raise SessionNotFoundException(f"Session not found for user token {self.userToken}")
                elif res_status == HeartBeatStatus.UNKNOWN:
                    raise RuntimeError(f"Status received as {res_status}")
                elif server_msg == "Error: Active streaming subscription already exists.":
                    raise StreamingAlreadyExistsException("Heartbeat subscription already exists")
                
                self.retry_count = 1
        except grpc.RpcError as err:
            hb_response_it.cancel()
            raise grpc.RpcError(err)
    
    def write_to_log(self, msg):
        print(msg)
    
    @staticmethod
    def get_current_time():
        now = datetime.datetime.now()
        formatter = "%Y-%m-%d %H:%M:%S"
        return now.strftime(formatter)

    def calculate_delay_millis(self, retry_count):
        return int(pow(2, retry_count) * self.config.retryDelayMS)

    def suspend_heartbeat_thread(self):
        if self.heartbeat_thread is not None:
            self.heartbeat_exit_signal = True
            while self.heartbeat_thread.is_alive():
                self.write_to_log("Waiting for heartbeat thread to stop")
                self.sleep(self.config.retryDelayMS)
            self.heartbeat_thread = None
            
    def sleep(self, delayMs):
        time.sleep(delayMs/1000)

    def can_connect_to_internet(self):
        try:
            host = "www.google.com"
            port = 80
            timeout_ms = 3000
            socket.setdefaulttimeout(timeout_ms / 1000.0)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except (socket.gaierror, socket.timeout):
            return False

    def can_connect_to_server(self):
        host = self.config.server
        port = self.config.port
        timeout_ms = 3000

        try:
            socket.setdefaulttimeout(timeout_ms / 1000.0)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except (socket.gaierror, socket.timeout, ConnectionRefusedError):
            return False

    def __del__(self):
        self.suspend_heartbeat_thread()
        self.close_channel()

class HeartBeatStatus(enum.Enum):
    LIVE = 0
    DEAD = 1
    UNKNOWN = 2
# You'll need to implement the EMSXAPIConfig class and import the necessary modules for the code to work correctly.
# Also, make sure to add proper error handling, as exceptions in Python are not the same as in Java.
