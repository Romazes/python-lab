import xapi_client_support as imp

''''Function for Todays Balance Accounts'''
def gettodaysbalances(self):
        try:
            req_Bal = imp.uPb2.TodaysBalancesRequest()  
            if not self.userToken:
                imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
                return False 

            req_Bal.UserToken = self.userToken          #UserToken          
            self.resp_reqBal = self.utility_stub.GetTodaysBalances(req_Bal)

            if self.resp_reqBal.Acknowledgement.ServerResponse:
                if self.resp_reqBal.Acknowledgement.ServerResponse == self.success:
                    imp.tk.messagebox.showinfo("Message","Successfully Fetched Today's Balances")
                else:
                    imp.tk.messagebox.showinfo("Message", self.resp_reqBal.Acknowledgement.ServerResponse)
            else:
                self.resp_msg = self.resp_reqBal.Acknowledgement.OptionalFields["ErrorMessage"]
                imp.tk.messagebox.showinfo("Message", self.resp_msg)
             
            return self.resp_reqBal

        except Exception as e:
            imp.tk.messagebox.showinfo("Message", str(e))

''''Function for Todays Activity Accounts'''
def gettodaysactivity(self):
        try:
            req_Act = imp.uPb2.TodaysActivityRequest()  
            if not self.userToken:
                imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
                return False 

            req_Act.UserToken = self.userToken      #UserToken 
            self.resp_reqAct = self.utility_stub.GetTodaysActivity(req_Act)

            if self.resp_reqAct.Acknowledgement.ServerResponse:
                if self.resp_reqAct.Acknowledgement.ServerResponse == self.success:
                    imp.tk.messagebox.showinfo("Message","Successfully Fetched Today's Activity")
                else:
                    imp.tk.messagebox.showinfo("Message", self.resp_reqAct.Acknowledgement.ServerResponse) 
            else:
                self.resp_msg = self.resp_reqAct.Acknowledgement.OptionalFields["ErrorMessage"]
                imp.tk.messagebox.showinfo("Message", self.resp_msg) 
            
            return self.resp_reqAct

        except Exception as e:
            imp.tk.messagebox.showinfo("Message", str(e))

''''Function for Todays BrokenDown Positions Accounts'''
def gettodaysbrokendownpositions(self):
        try:
            req_Pos = imp.uPb2.TodaysBrokenDownPositionsRequest()  
            if not self.userToken:
                imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
                return False 
            
            req_Pos.UserToken = self.userToken        #UserToken
            self.resp_reqPos = self.utility_stub.GetTodaysBrokenDownPositions(req_Pos)
    
            if self.resp_reqPos.Acknowledgement.ServerResponse:
                if self.resp_reqPos.Acknowledgement.ServerResponse == self.success:
                    imp.tk.messagebox.showinfo("Message","Successfully Fetched Today's Broken Down Positions")
                else:
                    imp.tk.messagebox.showinfo("Message", self.resp_reqPos.Acknowledgement.ServerResponse)  
            else:
                self.resp_msg = self.resp_reqPos.Acknowledgement.OptionalFields["ErrorMessage"]
                imp.tk.messagebox.showinfo("Message", self.resp_msg) 

            return self.resp_reqPos

        except Exception as e:
            imp.tk.messagebox.showinfo("Message", str(e))

''''Function for Todays Net Positions Accounts'''
def gettodaysnetpositions(self):
        try:
            req_Netpos = imp.uPb2.TodaysNetPositionsRequest()  
            if not self.userToken:
                imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
                return False 

            req_Netpos.UserToken = self.userToken      #UserToken
            self.resp_reqNetpos = self.utility_stub.GetTodaysNetPositions(req_Netpos) 

            if self.resp_reqNetpos.Acknowledgement:               
                if self.resp_reqNetpos.Acknowledgement.ServerResponse == self.success:
                    imp.tk.messagebox.showinfo("Message","Successfully Fetched Today's Net Positions")
                else:
                    imp.tk.messagebox.showinfo("Message", self.resp_reqNetpos.Acknowledgement.ServerResponse) 
            else:
                self.resp_msg = self.resp_reqNetpos.Acknowledgement.OptionalFields["ErrorMessage"]
                imp.tk.messagebox.showinfo("Message", self.resp_msg) 

            return self.resp_reqNetpos

        except Exception as e:
            imp.tk.messagebox.showinfo("Message", str(e))








            




    
                              
            

