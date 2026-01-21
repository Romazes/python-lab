import xapi_client_support as imp

'''Function to DISCONNECT from server'''
def disconnect(self):
    try:
        disconnect = imp.uPb2.DisconnectRequest()
        disconnect.UserToken = self.userToken      
        self.resp_disConnect = self.utility_stub.Disconnect(disconnect)
        if self.resp_disConnect.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message", "Successfully Disconnected! Please Restart To Connect")
        else:
            self.resp_msg = self.resp_disConnect.OptionalFields[
                "ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.resp_msg)
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))
