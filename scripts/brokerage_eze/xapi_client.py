import xapi_client_support as imp


def start_gui():
    '''Calling GUI'''
    imp.vp_start_gui()


def establishserverconnection(self):
    ''' Function to establish connection for gRPC server '''
    try:
        host = 'EMSUATXAPI.taltrade.com'
        server_port = 9000
        imp.grpc.max_message_length = (1024 * 1024 * 1024)
        options = [('grpc.max_receive_message_length', imp.grpc.max_message_length)]
        useSSL = True
        if useSSL:
            with open(r'roots.pem', 'rb') as f:  # pathforpemfile
                fin = f.read()
                creds = imp.grpc.ssl_channel_credentials(root_certificates=fin)
            channel = imp.grpc.secure_channel('{}:{}'.format(host, server_port), creds, options)
        else:
            channel = imp.grpc.insecure_channel('{}:{}'.format(host, server_port), options=options)

        self.stub = imp.ob_grpc.SubmitOrderServiceStub(channel)
        self.utility_stub = imp.uPb2_grpc.UtilityServicesStub(channel)
        self.market_stub = imp.mktPb2_grpc.MarketDataServiceStub(channel)
        return True
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", e)
        return False


def btnok_connect(self):
    '''Function to connect(glx2 token)'''
    imp.sSrp.srpconnect(self)

def btnok_changePasswordSRP(self):
   imp.sChangePasswordSRP.changePasswordSRP(self)


def fid_func(self):
    '''Function shows fidlist file required for ExtendedFields/OptionalFields'''
    readme = "fidlist.txt"
    if imp.sys.platform == 'win32':				#windows	
    	imp.os.startfile(readme)   
    elif imp.sys.platform == 'linux':			 #linux
    	imp.os.system('gedit "{0}"'.format(readme))


def btnsubmit(self):
    '''Function to invoke submitsingleorder/submitpair APIs'''
    if self.bselection == 'Submit Single Order':
        imp.sOrder.submitsingleorder(self)  # callingsubmitsingleorderapi
    elif self.bselection == 'Submit Pair Order':
        imp.sPairOrder.submitpairorder(self)  # callingsubmitpairorderapi
    elif self.bselection == 'Submit Seed Data':
        imp.sSeed.submitseeddata(self)  # callingsubmitseeddataapi
    elif self.bselection == 'Submit Basket Order':
        imp.sBasketOrder.submitbasketorder(self)  # callingbasketorderapi
    elif self.bselection == 'Get User Accounts':
        imp.sXpermsAccounts.getuseraccounts(self)  # callinggetuseraccountsapi
    elif self.bselection == 'Subscribe Order Info':
        imp.sSubscribe.init_respStream(self)  # callingorderstreamingthread
    elif self.bselection == 'Submit Trade Report':
        imp.sTradeReport.submittradereport(self)
    elif self.bselection == 'Subscribe to HeartBeats':
        imp.sHeartBeat.init_HeartBeatStream(self)            
    else:
        if self.bselection:
            self.requestapi_grid()  # respective gui for requested api
            self.requestapiresponse()  # callingapi


def submitallocationorder(self):
    '''Function to invoke Submit Allocation Order API'''
    imp.sAllocorder.submitallocationorder(self)


def changesingleorder(self):
    '''Function to invoke Change Single Order API'''
    imp.sChange.changesingleorder(self)  # Callingchange


def changepairorder(self):
    '''Function to invoke Change Pair Order API'''
    imp.sPairChange.changepairorder(self)  # Callingpairchange


def cancelorder(self):
    '''Function to invoke cancelsingleorder/cancelpairorder API'''
    if self.Ordertypecol == '':
        pass
    elif self.Orderlinkedid == '' and self.symcol != '!Pair':
        imp.sCancel.cancelsingleorder(self)
    else:
        imp.sPairCancel.cancelpairorder(self)


def marketdata(self):
    '''Function to invoke Market data APIs'''
    if self.mktSelection == 'Subscribe Level1 Ticks':
        imp.sLQTableExample.requestandwatchlevel1(self)  # callingrequestandwatchlevel1api
    elif self.mktSelection == 'UnSubscribe Level1 Data':
        imp.sUnsubLevel1.unsubscribelevel1data(self)  # callingunsubscribelevel1dataapi
    elif self.mktSelection == 'Subscribe Level2 Ticks':
        imp.sMktMakers.requestandwatchlevel2(self)  # callingrequestandwatchlevel2api
    elif self.mktSelection == 'UnSubscribe Level2 Data':
        imp.sUnsubLevel2.unsubscribelevel2data(self)  # callingunsubscribelevel2dataapi
    elif self.mktSelection == 'Add Symbols':
        imp.sAddsymbols.addsymbols(self)  # callingaddsymbolspi
    elif self.mktSelection == 'Remove Symbols':
        imp.sRemovesymbols.removesymbols(self)  # callingremovesymbolsapi


def viewsourcecode(self):
    '''Function to view selected api source code in notepad'''
    if self.bselection:
        if self.bselection == 'Submit Single Order':
            filename = 'Examples/submitsingleorder.py'
            if imp.sys.platform == 'win32':	          #windows
            	imp.os.system('notepad ' + filename)  #Openinnotepad
            elif imp.sys.platform == 'linux':		  #linux
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.bselection == 'Subscribe Order Info':
            filename = 'Examples/subscribeorderinfo.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.bselection == 'Submit Pair Order':
            filename = 'Examples/submitpairorder.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.bselection == 'Submit Seed Data':
            filename = 'Examples/submitseeddata.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.bselection == 'Submit Basket Order':
            filename = 'Examples/submitbasketorder.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename) 
            elif imp.sys.platform == 'linux':			  	
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.bselection == 'Get User Accounts':
            filename = 'Examples/getuseraccounts.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  	
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.bselection == 'Get Symbols From Company Name':
            filename = 'Examples/getsymbolsfromcompanyname.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  	
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.bselection == 'Get Symbol From SEDOL, ISIN, CUSIP, etc':
            filename = 'Examples/getsymbolfromalternatesymbology.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  	
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.bselection == 'Submit Trade Report':
            filename = 'Examples/submittradereport.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  	
            	imp.os.system('gedit "{0}"'.format(filename))
        else:  # TodayApis
            filename = 'Examples/miscellaneous_apis.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  	
            	imp.os.system('gedit "{0}"'.format(filename))
    if self.mktSelection:
        if self.mktSelection == 'Subscribe Level1 Ticks':
            filename = 'Examples/requestandwatchlevel1.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  	
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.mktSelection == 'UnSubscribe Level1 Data':
            filename = 'Examples/unsubscribe_level1data.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  	
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.mktSelection == 'Subscribe Level2 Ticks':
            filename = 'Examples/requestandwatchlevel2.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  	
            	imp.os.system('gedit "{0}"'.format(filename))
        elif self.mktSelection == 'UnSubscribe Level2 Data':
            filename = 'Examples/unsubscribe_level2data.py'
            if imp.sys.platform == 'win32':	
            	imp.os.system('notepad ' + filename)  
            elif imp.sys.platform == 'linux':			  	
            	imp.os.system('gedit "{0}"'.format(filename))
    
def disconnect(self):
    '''Function to invoke Disconnect API'''
    imp.sDisconnect.disconnect(self)
    self.credentials.clear()


if __name__ == '__main__':
    start_gui()
