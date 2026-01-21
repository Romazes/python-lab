import xapi_client_support as imp


def getuserstrategies(self):
    try:
        strat_request = imp.uPb2.StrategyListRequest()
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False
        strat_request.FirmName = self.list_strat[0].get()
        strat_request.UserToken = self.userToken
        self.resp_stratData = self.utility_stub.GetStrategyList(strat_request)

        if self.resp_stratData.Acknowledgement.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message", "Successfully Fetched Strategy List")
            return self.resp_stratData
        else:
            self.msg_stratData = self.resp_stratData.Acknowledgement.Message
            if self.msg_stratData:
                imp.tk.messagebox.showinfo("Message", self.msg_stratData)
            else:
                imp.tk.messagebox.showinfo("Message", "Failed to Fetch Strategy List")
            return False

    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))