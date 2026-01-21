import xapi_client_support as imp

'''Instantiate the Stream response'''
def init_HeartBeatStream(self):
    thread = imp.threading.Thread(target=subscribeHeartbeat, args=[self])
    thread.name = 'HeartBeatThread'
    thread.daemon = True
    thread.start()

''' Function for streaming response from gRPC server '''
def subscribeHeartbeat(self):
    try:
        heartbeat_request = imp.uPb2.SubscribeHeartBeatRequest()
        
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False
            
        heartbeat_request.UserToken = self.userToken
        self.resp_heartbeat = self.utility_stub.SubscribeHeartBeat(heartbeat_request)

        for resp in self.resp_heartbeat:
            if resp.Status != imp.uPb2.SubscribeHeartBeatResponse.LIVE:
                error_message = resp.Acknowledgement.ServerResponse
                imp.tk.messagebox.showinfo("Message", error_message)

    except StopIteration as er:
        imp.tk.messagebox.showinfo("Message", er)