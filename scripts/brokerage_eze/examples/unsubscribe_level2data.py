import xapi_client_support as imp

'''Function for UnSubscribeLevel2Data'''
def unsubscribelevel2data(self):
    try:
        req_L2Unsub = imp.md.UnSubscribeLevel2DataRequest()  
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False
        req_L2Unsub.UserToken = self.userToken         
       
        self.resp_reqL2Unsub = self.market_stub.UnSubscribeLevel2Data(req_L2Unsub)

        if self.resp_reqL2Unsub.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message", "Successfully Unsubscribed Level2 Data")
        else:
            self.resp_msg = self.resp_reqL2Unsub.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.resp_msg)

    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))