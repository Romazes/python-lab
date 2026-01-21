import xapi_client_support as imp

''''Function for User Accounts'''
def getuseraccounts(self):
        try:
            user_Acc = imp.ob.UserAccountsRequest() 
            if not self.userToken:
                imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
                return False 
            user_Acc.UserToken = self.userToken 
            self.resp_userAcc = self.stub.GetUserAccounts(user_Acc)
            acct = self.resp_userAcc.Accounts
            if acct:
                self.combobox_values =   list(acct.values())
                self.TCombobox1['values'] = self.combobox_values  
                self.TCombobox1.current(0)
                self.aSelection = self.TCombobox1.get()

            if self.resp_userAcc.Acknowledgement.ServerResponse:
                if self.resp_userAcc.Acknowledgement.ServerResponse == self.success:
                    imp.tk.messagebox.showinfo("Message","Successfully Fetched User Accounts")
                else:
                    imp.tk.messagebox.showinfo("Message", self.resp_userAcc.Acknowledgement.ServerResponse)
            else:
                self.resp_msg = self.resp_userAcc.Acknowledgement.OptionalFields["ErrorMessage"]
                imp.tk.messagebox.showinfo("Message", self.resp_msg)
             
            return self.resp_userAcc

        except Exception as e:
            imp.tk.messagebox.showinfo("Message", str(e))