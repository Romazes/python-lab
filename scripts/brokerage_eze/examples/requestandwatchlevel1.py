import xapi_client_support as imp

def start_Level1(self):
    thread_object = imp.threading.Thread(target=resp_LQ, args=[self])
    thread_object.daemon=True
    thread_object.name="L1Thread"
    thread_object.start()


'''Function for RequestAndWatchLevel1'''
def requestandwatchlevel1(self):
    try:
        req_LQTable = imp.md.Level1MarketDataRequest()
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False
        req_LQTable.UserToken = self.userToken
        req_LQTable.Symbols.extend(self.Sym_ip)
        # req_LQTable.RegionalExchangeIds.extend([' '])      #notsendinganyregionalexchangeIds..soitconsiderasNULL
        req_LQTable.Request = self.req_Mkt
        req_LQTable.Advise = self.adv_Mkt

        self.resp_reqLQTable = self.market_stub.SubscribeLevel1Ticks(
            req_LQTable)
        
        start_Level1(self)
  
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))
    
def resp_LQ(self):
    self.label_LQ = imp.tk.Label(self.lstbx_mkt,  text='-----------------------------------------------',
                    background="black", foreground="green")
    self.label_LQ.pack()

    self.label1_LQ = imp.tk.Label(self.lstbx_mkt, text='Watching Level1 Data',
                        background="black", foreground="green")
    self.label1_LQ.config(font=("Courier", 11))
    self.label1_LQ.pack()
    self.lstbx_mkt.update()
             
    for item in self.resp_reqLQTable:
        self.label2_LQ = imp.tk.Label(self.lstbx_mkt)

        trdpc = str(item.Trdprc1.DecimalValue)  #TradePrc

        seconds_trdtime = item.Trdtim1.seconds  #TradeTime
        conversion_trdtime = imp.datetime.timedelta(seconds=seconds_trdtime)
        converted_trdtime = str(conversion_trdtime)  # hr:mm:ss format 

        if trdpc != '0.0':  #displaynonzerovalues
            self.str_LQ = 'For Symbol' + '  ' + item.DispName + \
            '  ' + 'at' + ' ' + trdpc + '  ' + converted_trdtime

            self.label2_LQ.config(background="black", foreground="green")
            self.label2_LQ.config(text=self.str_LQ)
            self.label2_LQ.config(font=("Courier", 10))
            self.label2_LQ.pack()
            self.lstbx_mkt.update()
   
