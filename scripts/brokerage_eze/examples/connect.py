import xapi_client_support as imp

'''Function to fetch the GLX2 token from server'''
def connect(self):
    try:
        tkConnect = imp.uPb2.ConnectRequest()
        if self.list_Start[0].get():
            user_name = self.list_Start[0].get() 
        if self.list_Start[1].get():
            domain_connect = self.list_Start[1].get()
        if self.list_Start[2].get():
            pswrd_connect = self.list_Start[2].get()
        if self.list_Start[3].get():
            locale_connect = self.list_Start[3].get()
            
        tkConnect.UserName = user_name.upper()
        tkConnect.Domain = domain_connect.upper()
        tkConnect.Password = pswrd_connect
        tkConnect.Locale = locale_connect.upper()

        self.resp_tkConnect = self.utility_stub.Connect(tkConnect)
        
        if self.resp_tkConnect.Response:
            if self.resp_tkConnect.Response == self.success:
                self.userToken = self.resp_tkConnect.UserToken
                imp.tk.messagebox.showinfo("Message", "Successfully Fetched UserToken")
                self.top_Start.destroy()
                self.top_Start = False
            else:
                imp.tk.messagebox.showinfo("Message", self.resp_tkConnect.Response)
                return False 
        else:
            imp.tk.messagebox.showinfo("Message", "Failed To Fetch  UserToken")
            return False
        return True
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))
