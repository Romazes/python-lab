import xapi_client_support as imp

def start_Level2(self):
    thread_mktMakers = imp.threading.Thread(target=resp_MM, args=[self])
    thread_mktMakers.name = 'L2Thread'
    thread_mktMakers.daemon = True
    thread_mktMakers.start()

'''Function for RequestAndWatchLevel2'''
def requestandwatchlevel2(self):
    try:
        req_MktMakers = imp.md.Level2MarketDataRequest()
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False

        req_MktMakers.UserToken = self.userToken
        req_MktMakers.Symbols.extend(self.Sym_ip)
        #req_MktMakers.RequestId = None
        #req_MktMakers.MarketSource.extend([]) #notsending..soitconsiderasNull
        req_MktMakers.Request = self.req_Mkt
        req_MktMakers.Advise = self.adv_Mkt

        self.resp_reqMktMakers = self.market_stub.SubscribeLevel2Ticks(
            req_MktMakers)
        
        start_Level2(self)
        
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))
    
def resp_MM(self):
    self.label_MktMakers = imp.tk.Label(self.lstbx_mkt,  text='-----------------------------------------------',
                    background="black", foreground="green")
    self.label_MktMakers.pack()
    self.label1_MktMakers = imp.tk.Label(self.lstbx_mkt, text='Watching Level2 Data',
                    background="black", foreground="green")
    self.label1_MktMakers.config(font=("Courier", 11))
    self.label1_MktMakers.pack()
    self.lstbx_mkt.update()

    for item in self.resp_reqMktMakers:
        seconds_ask = item.MktMkrAskTime.seconds #AskTime
        conversion_ask = imp.datetime.timedelta(seconds=seconds_ask)
        converted_ask = str(conversion_ask)  # hr:mm:ss format

        seconds_bid = item.MktMkrBidTime.seconds #BidTime
        conversion_bid =imp.datetime.timedelta(seconds=seconds_bid)
        converted_bid = str(conversion_bid)

        str_Mktmakers = item.DispName + ' ' + item.MktMkrId + ' ' + \
            str(item.MktMkrAsk.DecimalValue) + ' ' + converted_ask + \
            ' ' + str(item.MktMkrBid.DecimalValue) + ' ' + converted_bid
    
        self.label2_MktMakers = imp.tk.Label(self.lstbx_mkt)
        self.label2_MktMakers.config(text=str_Mktmakers)
        self.label2_MktMakers.config(background="black", foreground="green")
        self.label2_MktMakers.config(font=("Courier", 10))
        self.label2_MktMakers.pack()
        self.lstbx_mkt.update()
 
