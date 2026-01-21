import sys
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
    from tkinter import *

try:
    import ttk

    py3 = False
except ImportError:
    import tkinter.ttk as ttk

    py3 = True

import grpc
import threading
import os
import re
from tkinter import messagebox
from collections import OrderedDict  # tomaintainspecificorderfordict
from pathlib import Path
from tkinter import filedialog as fd
import datetime
import order_pb2 as ob
import order_pb2_grpc as ob_grpc
import utilities_pb2 as uPb2
import utilities_pb2_grpc as uPb2_grpc
import market_data_pb2 as md
import market_data_pb2_grpc as mktPb2_grpc
import xapi_client as sMain
import Examples.submitsingleorder as sOrder
import Examples.changesingleorder as sChange
import Examples.cancelsingleorder as sCancel
import Examples.submitpairorder as sPairOrder
import Examples.changepairorder as sPairChange
import Examples.cancelpairorder as sPairCancel
import Examples.submitseeddata as sSeed
import Examples.miscellaneous_apis as sMiscellaneous
import Examples.getuseraccounts as sXpermsAccounts
import Examples.requestandwatchlevel1 as sLQTableExample
import Examples.unsubscribe_level1data as sUnsubLevel1
import Examples.requestandwatchlevel2 as sMktMakers
import Examples.unsubscribe_level2data as sUnsubLevel2
import Examples.connect as sConnect
import Examples.dis_connect as sDisconnect
import Examples.addsymbols as sAddsymbols
import Examples.removesymbols as sRemovesymbols
import Examples.srpconnect as sSrp
import Examples.subscribeorderinfo as sSubscribe
import Examples.submitbasketorder as sBasketOrder
import Examples.getsymbolsfromcompanyname as sSymCompanyName
import Examples.getsymbolfromalternatesymbology as sSymbolInfo
import Examples.submitallocationorder as sAllocorder
import Examples.submittradereport as sTradeReport
import Examples.changePasswordSRP as sChangePasswordSRP
import Examples.subscribeheartbeat as sHeartBeat
import Examples.getuserstrategies as sUserStrategies


def vp_start_gui():
    '''Starting point when module is the main routine.'''
    global w, root
    root = tk.Tk()
    set_Tk_var()
    top = Toplevel1(root)
    init(root, top)
    root.mainloop()

w = None

def create_Toplevel1(root, *args, **kwargs):
    '''Starting point when module is imported by another program.'''
    global w, rt
    rt = root
    w = tk.Toplevel(root)
    set_Tk_var()
    top = Toplevel1(w)
    init(w, top, *args, **kwargs)
    return (w, top)


def destroy_Toplevel1():
    global w
    w.destroy()
    w = None


class Toplevel1(object):

    def destroy_window(self):
        root.destroy()
        '''Function to invoke Disconnect API'''
        sDisconnect.disconnect(self)
        self.credentials.clear()
        # Function which closes main window along with child windows
        #     if self.top_Mkt:
        #         if 'normal' == self.top_Mkt.state(): #windowopenedcheck
        #             self.top_Mkt.destroy()
        #     if self.top_Start:
        #         if 'normal' == self.top_Start.state(): 
        #             self.top_Start.destroy()

    def destroy_startwindow(self):
        self.top_Start.withdraw()
        self.top_Start = False

    def treegridselect(self, event):
        ''' Function shows the selection of OrderBlotter grid '''
        self.curItem = self.ord_blotter.item(self.ord_blotter.focus())
        if self.curItem['values'] != '':
            self.valcol = self.curItem['values'][0]  # OrderId
            self.symcol = self.curItem['values'][2]
            self.sidecol = self.curItem['values'][3]
            self.qty_fromorder = self.curItem['values'][4]
            self.prccol = self.curItem['values'][5]
            self.prctypecol = self.curItem['values'][6]
            self.bank_ = self.curItem['values'][9]
            self.branch_ = self.curItem['values'][10]
            self.customer_ = self.curItem['values'][11]
            self.deposit_ = self.curItem['values'][12]
            self.Ordertypecol = self.curItem['values'][13]
            self.Orderlinkedid = self.curItem['values'][14]
            self.exchange = self.curItem['values'][19]
            self.expcol = self.curItem['values'][23]

            # On 'USCO' selection how to fetch the child order ID's
            for self.child_lst in self.orderList:
                if self.child_lst.LinkedOrderId or self.symcol == '!Pair':
                    self.bChange = False
                else:
                    self.bChange = True
                if self.child_lst.LinkedOrderId == self.valcol and self.child_lst.Type == 'UserSubmitOrder' or self.child_lst.Type == 'UserSubmitStagedOrder' and self.child_lst.OrderId not in self.childIds:  # because child-orderid will change for type=exchangetradeorder
                    if self.sidecol == self.child_lst.Buyorsell:  # because side of leg1 will assign to parent order in pairs
                        self.childIds['Leg1 OrderId'] = self.child_lst.OrderId
                    else:
                        self.childIds['Leg2 OrderId'] = self.child_lst.OrderId

                if self.Orderlinkedid == self.child_lst.OrderId and self.child_lst.Type == 'UserSubmitCompoundOrder':
                    self.childIds['Pair OrderId'] = self.child_lst.OrderId
                    self.type_pair = self.child_lst.Buyorsell
                if self.Orderlinkedid == self.child_lst.LinkedOrderId and self.child_lst.Type == 'UserSubmitOrder' or self.child_lst.Type == 'UserSubmitStagedOrder':
                    if self.type_pair == self.child_lst.Buyorsell:
                        self.childIds['Leg1 OrderId'] = self.child_lst.OrderId
                    else:
                        self.childIds['Leg2 OrderId'] = self.child_lst.OrderId

    def orderblotter_grid(self):
        ''' Function shows the implementation of Order Blotter tree grid '''
        self.ord_blotter = ttk.Treeview(self.TPanedwindow1_p1)
        self.ord_blotter["columns"] = ["#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8", "#9", "#10", "#11", "#12", "#13","#14","#15", "#16", "#17", "#18", "#19", "#20", "#21", "#22", "#23", "#24", "#25",
                                       "#26", "#27", "#28", "#29", "#30", "#31",
                                       "#32", "#33", "#34", "#35", "#36"]
        self.ord_blotter['show'] = 'headings'
        orderblotter_data = {"#1": "ORDER ID", "#2": "ORDER TAG", "#3": "SYMBOL", "#4": "SIDE", "#5": "VOLUME","#6": "PRICE", "#7": "PRICE TYPE", "#8": "CURRENT STATUS",
        "#9": "EXIT VEHICLE", "#10": "BANK", "#11": "BRANCH", "#12": "CUSTOMER", "#13": "DEPOSIT","#14": "TYPE", "#15": "LINKED ID",
        "#16": "REFERS TO ID", "#17": "ORIGINAL ORDER ID", "#18": "TRADER ID","#19": "VOLUME TRADED", "#20": "EXCHANGE",
        "#21": "CURRENCY", "#22": "REASON", "#23": "GOOD FORM", "#24": "GOOD UNTIL","#25": "SPREAD NUM LEGS", "#26": "PAIR SPREADTYPE", "#27": "PAIR TARGET",
        "#28": "PAIR SPREAD", "#29": "PAIR RATIO", "#30": "PAIR CASH", "#31": "NEWS DATE","#32": "OMS CLIEN1 TYPE",
        "#33": "GW BOOK SEQNO", "#34": "USER MESSAGE", "#35": "CLAIMED BY CLERK","#36": "TIME STAMP"}

        for ix, y in orderblotter_data.items():
            self.ord_blotter.heading(ix, text=y)

        self.ord_blotter.place(relx=0.009, rely=0.04, relheight=0.891, relwidth=0.96, bordermode='outside')

        vsb = ttk.Scrollbar(orient="vertical", command=self.ord_blotter.yview)
        hsb = ttk.Scrollbar(orient="horizontal", command=self.ord_blotter.xview)
        self.ord_blotter.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        hsb.place(relx=0.0047, rely=0.93, relheight=0.06, relwidth=0.961, bordermode='outside', in_=self.TPanedwindow1_p1)

        vsb.place(relx=0.97, rely=0.047, relheight=0.9, relwidth=0.02, bordermode='outside', in_=self.TPanedwindow1_p1)

        self.ord_blotter.bind('<ButtonRelease-1>', self.treegridselect)

        for col in self.ord_blotter["columns"]:
            sort_column(self.ord_blotter, col, 0)

        self.popup_menu = tk.Menu(self.ord_blotter, tearoff=0)
        self.popup_menu.add_command(label="Allocate",
                                    command=self.btnAlloc)
        self.popup_menu.add_command(label="Change Order",
                                    command=self.btnchange)
        self.popup_menu.add_command(label="Cancel Order",
                                    command=self.btncancel)

        self.ord_blotter.bind("<ButtonPress-1>", bDown)
        self.ord_blotter.bind("<ButtonRelease-1>", bUp, add='+')
        self.ord_blotter.bind("<B1-Motion>", bMove, add='+')
        self.ord_blotter.bind("<Button-3>", self.bRightclick)
        self.ord_blotter.bind("<Shift-ButtonPress-1>", bDown_Shift, add='+')

    def bRightclick(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.popup_menu.grab_release()

    def requestapi_grid(self):
        ''' Function shows the implementation of  Today's API tree grid'''
        self.tree = ttk.Treeview(self.TPanedwindow1_p2)
        if self.bselection == 'Get Today\'s Balances':
            self.tree["columns"] = ["#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8", "#9", "#10", "#11", "#12", "#13","#14",
                                    "#15", "#16", "#17", "#18", "#19", "#20", "#21", "#22", "#23", "#24", "#25", "#26", "#27", "#28",
                                    "#29", "#30", "#31",
                                    "#32", "#33"]
            self.tree['show'] = 'headings'
            request_data = {"#1": "TBO_ACCOUNT_ID", "#2": "BANK", "#3": "BRANCH", "#4": "CUSTOMER", "#5": "DEPOSIT",
                            "#6": "CURRENCY", "#7": "RANK",
                            "#8": "MARKETVALUE_0", "#9": "CASH_BALANCE", "#10": "EQUITY_BALANCE", "#11": "EXTRA_CBP",
                            "#12": "MIN_BALANCE", "#13": "MAX_ORDER_SIZE", "#14": "EXCESS_EQ_0",
                            "#15": "EXCESS_EQ", "#16": "MMR_0", "#17": "MMR", "#18": "SCALPED_PROFIT",
                            "#19": "CASH_BALANCE_ADJ", "#20": "MMR_0_ADJ",
                            "#21": "SMA_0", "#22": "SMA_0_ADJ", "#23": "HOUSE_EXCESS_0", "#24": "ORQ_0",
                            "#25": "CALC_TIME", "#26": "DAYS_BACK", "#27": "COST",
                            "#28": "MMR_0_NON_DAYTRADE_ADJ", "#29": "SRV_PENDING_MARGIN", "#30": "COMMISSION",
                            "#31": "NET_FEES", "#32": "HIST_SCALPED_PROFIT", "#33": "TABLE"}

            for ix, y in request_data.items():
                self.tree.heading(ix, text=y)

        elif self.bselection == 'Get Today\'s Activity' or self.bselection == 'Get Today\'s Activity Book':
            self.tree["columns"] = ["#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8", "#9", "#10", "#11", "#12", "#13",
                                    "#14",
                                    "#15", "#16", "#17", "#18", "#19", "#20", "#21", "#22", "#23", "#24", "#25", "#26",
                                    "#27", "#28", "#29", "#30", "#31",
                                    "#32", "#33", "#34", "#35", "#36", "#37", "#38", "#39", "#40", "#41", "#42", "#43",
                                    "#44", "#45", "#46", "#47", "#48",
                                    "#49", "#50", "#51", "#52", "#53", "#54", "#55", "#56", "#57", "#58", "#59", "#60",
                                    "#61", "#62", "#63", "#64", "#65",
                                    "#66", "#67", "#68", "#69", "#70", "#71", "#72", "#73", "#74"]
            self.tree['show'] = 'headings'

            request_data = {"#1": "BANK", "#2": "BRANCH", "#3": "CUSTOMER", "#4": "DEPOSIT", "#5": "ACCT_TYPE",
                            "#6": "FIX_TRADER_ID", "#7": "TRADER_ID",
                            "#8": "ORIGINAL_TRADER_ID", "#9": "DATE_INDEX", "#10": "TBO_ACCOUNT_ID",
                            "#11": "TIME_STAMP", "#12": "LATENCY_6", "#13": "TYPE", "#14": "DISP_NAME",
                            "#15": "PRICE", "#16": "VOLUME", "#17": "BUYORSELL", "#18": "GOOD_UNTIL",
                            "#19": "VOLUME_TYPE", "#20": "PRICE_TYPE",
                            "#21": "EXIT_VEHICLE", "#22": "EXCHANGE", "#23": "BID", "#24": "ASK", "#25": "STYP",
                            "#26": "BASIS_VALUES", "#27": "LINKED_ORDER_RELATIONSHIP",
                            "#28": "ORDER_FLAGS", "#29": "TRADER_CAPACITY", "#30": "CURRENCY",
                            "#31": "LINKED_ORDER_CANCELLATION", "#32": "LINKED_ORDER_ID",
                            "#33": "SPREAD_LEG_NUMBER", "#34": "GW_BOOK_SEQ_NO", "#35": "ORDER_ID", "#36": "BOOK_ID",
                            "#37": "EXTENDED_STATE_FLAGS_2",
                            "#38": "NEWS_DATE", "#39": "NEWS_TIME", "#40": "UTC_OFFSET", "#41": "RANK",
                            "#42": "CURRENT_STATUS", "#43": "ORIGINAL_VOLUME",
                            "#44": "ORDER_RESIDUAL", "#45": "VOLUME_TRADED", "#46": "ORIGINAL_ORDER_ID",
                            "#47": "REFERS_TO_ID", "#48": "EXTENDED_STATE_FLAGS",
                            "#49": "CLAIMED_BY_CLERK", "#50": "EXTERNAL_ACCEPTANCE_FLAG", "#51": "REMOTE_ID",
                            "#52": "NEW_REMOTE_ID", "#53": "AVG_PRICE",
                            "#54": "TRD_TIME", "#55": "COMMISSION", "#56": "REF_PRICE", "#57": "REF_VOULME",
                            "#58": "TABLE", "#59": "SPREAD_NUM_LEGS",
                            "#60": "ORDER_TAG", "#61": "OMS_CLIENT_TYPE", "#62": "GOOD_FORM", "#63": "STOP_PRICE",
                            "#64": "USER_MESSAGE", "#65": "STRIKE_PRC",
                            "#66": "PAIR_TARGET", "#67": "PAIR_SPREAD_TYPE", "#68": "PAIR_SPREAD", "#69": "PAIR_RATIO",
                            "#70": "PAIR_CASH", "#71": "PAIR_LEG_2_BENCHMARK", "#72": "PAIR_LEG_1_BENCHMARK",
                            "#73": "PAIR_LEG_2_BENCHMARK_TYPE", "#74": "PAIR_LEG_1_BENCHMARK_TYPE"
                            }

            for ix, y in request_data.items():
                self.tree.heading(ix, text=y)

        elif self.bselection == 'Get Today\'s BrokenDownPositions':
            self.tree["columns"] = ["#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8", "#9", "#10", "#11", "#12", "#13",
                                    "#14"
                , "#15", "#16", "#17", "#18", "#19", "#20", "#21", "#22", "#23", "#24", "#25", "#26", "#27", "#28",
                                    "#29", "#30", "#31", "#32", "#33",
                                    "#34"]
            self.tree['show'] = 'headings'

            request_data = {"#1": "TBO_ACCOUNT_ID", "#2": "BANK", "#3": "BRANCH", "#4": "CUSTOMER", "#5": "DEPOSIT",
                            "#6": "CURRENCY", "#7": "ACCT_TYPE",
                            "#8": "DISP_NAME", "#9": "RANK", "#10": "STYP", "#11": "AVERAGE_LONG", "#12": "LONGPOS",
                            "#13": "AVERAGE_LONG0", "#14": "HIST_LONG_PRC_0",
                            "#15": "LONGPOS0", "#16": "ORIG_LONGPOS0", "#17": "AVERAGE_SHORT", "#18": "SHORTPOS",
                            "#19": "AVERAGE_SHORT0", "#20": "HIST_SHORT_PRC_0",
                            "#21": "SHORTPOS0", "#22": "ORIG_SHORTPOS", "#23": "SCALPED_PROFIT", "#24": "MMR",
                            "#25": "TABLE", "#26": "BOUGHT_QTY", "#27": "SOLD_QTY",
                            "#28": "SOLD_SHORT_QTY", "#29": "BOUGHT_AVG_PRC", "#30": "SOLD_AVG_PRC",
                            "#31": "SOLD_SHORT_AVG_PRC", "#32": "COMMISSION", "#33": "NET_FEES",
                            "#34": "HIST_SCALPED_PROFIT"}

            for ix, y in request_data.items():
                self.tree.heading(ix, text=y)

        elif self.bselection == 'Get Today\'s NetPositions':
            self.tree["columns"] = ["#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8", "#9", "#10", "#11", "#12", "#13",
                                    "#14"
                , "#15", "#16", "#17", "#18", "#19", "#20", "#21"]
            self.tree['show'] = 'headings'

            request_data = {"#1": "BANK", "#2": "BRANCH", "#3": "CUSTOMER", "#4": "DEPOSIT", "#5": "DISP_NAME",
                            "#6": "INTRADAY_AVG_PRC", "#7": "INTRADAY_LONG_AVG_PRC",
                            "#8": "INTRADAY_LONG_POS", "#9": "INTRADAY_POS", "#10": "INTRADAY_SHORT_AVG_PRC",
                            "#11": "INTRADAY_SHORT_POS", "#12": "LONG_POS", "#13": "LONG_AVG_PRC",
                            "#14": "SHORT_POS", "#15": "SHORT_AVG_PRC", "#16": "SOLD_AVG_PRC", "#17": "SOLD_QTY",
                            "#18": "SOLD_SHORT_AVG_PRC", "#19": "SOLD_SHORT_QTY", "#20": "TOTAL_AVG_PRC",
                            "#21": "TOTAL_POS"}

            for ix, y in request_data.items():
                self.tree.heading(ix, text=y)

        elif self.bselection == 'Get Symbol From SEDOL, ISIN, CUSIP, etc' or self.bselection == 'Get Symbols From Company Name':
            self.tree["columns"] = ["#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8", "#9", "#10", "#11", "#12", "#13",
                                    "#14"
                , "#15"]
            self.tree['show'] = 'headings'

            request_data = {"#1": "DISP_NAME", "#2": "RIC_CODE", "#3": "BLOOMBERG_CODE", "#4": "BLOOMBERG_CODE_FULL",
                            "#5": "STYP", "#6": "COUNTRY",
                            "#7": "EXCH_NAME", "#8": "SEDOL", "#9": "SYMBOL_DESC", "#10": "CUSIP",
                            "#11": "COMMODITY_NAME", "#12": "ISIN_NO",
                            "#13": "GICS_SECTOR", "#14": "GICS_INDUSTRY", "#15": "GICS_SUBINDUSTRY"}

            for ix, y in request_data.items():
                self.tree.heading(ix, text=y)

        elif self.bselection == 'Get User Strategies':
            self.tree["columns"] = ["#1", "#2", "#3", "#4", "#5"]
            self.tree['show'] = 'headings'

            request_data = {"#1": "FirmName", "#2": "UserName", "#3": "AlgoName", "#4": "StrategyName",
                            "#5": "StratCreateDate"}

            for ix, y in request_data.items():
                self.tree.heading(ix, text=y)

        self.tree.place(relx=0.009, rely=0.04, relheight=0.891, relwidth=0.96, bordermode='outside')

        vsb = ttk.Scrollbar(orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)

        hsb.place(relx=0.0047, rely=0.93, relheight=0.06, relwidth=0.961, bordermode='outside',
                  in_=self.TPanedwindow1_p2)

        vsb.place(relx=0.97, rely=0.047, relheight=0.9, relwidth=0.02, bordermode='outside', in_=self.TPanedwindow1_p2)

        for col in self.tree["columns"]:
            sort_column(self.tree, col, 0)

        self.tree.bind("<ButtonPress-1>", bDown)
        self.tree.bind("<ButtonRelease-1>", bUp, add='+')
        self.tree.bind("<B1-Motion>", bMove, add='+')
        self.tree.bind("<Shift-ButtonPress-1>", bDown_Shift, add='+')

    def requestapiresponse(self):
        ''' This method shows the implementation of  Today's API'''
        if self.bselection == 'Get Today\'s Balances':
            self.sBal = sMiscellaneous.gettodaysbalances(self)  # callinggettodaysbalanceapi
            if self.sBal:
                self.sValues = self.sBal.DepositList
                index = iid = 0
                for sym in self.sValues:
                    self.tree.insert('', index, iid, values=(format(sym.TboAccountId), format(sym.Bank),
                                                             format(sym.Branch), format(sym.Customer),
                                                             format(sym.Deposit),
                                                             format(sym.Currency), format(sym.Rank),
                                                             format(sym.Marketvalue0),
                                                             format(sym.CashBalance), format(sym.EquityBalance),
                                                             format(sym.ExtraCbp),
                                                             format(sym.MinBalance), format(sym.MaxOrderSize),
                                                             format(sym.ExcessEq0),
                                                             format(sym.ExcessEq), format(sym.Mmr0), format(sym.Mmr),
                                                             format(sym.ScalpedProfit),
                                                             format(sym.CashBalanceAdj), format(sym.Mmr0Adj),
                                                             format(sym.Sma0), format(sym.Sma0Adj),
                                                             format(sym.HouseExcess0), format(sym.Orq0),
                                                             format(sym.CalcTime), format(sym.DaysBack),
                                                             format(sym.Cost), format(sym.Mmr0NonDaytradeAdj),
                                                             format(sym.SrvPendingMargin),
                                                             format(sym.Commission), format(sym.NetFees),
                                                             format(sym.HistScalpedProfit), format(sym.Table)))
                    index = iid = index + 1

        elif self.bselection == 'Get Today\'s Activity':
            self.sAct = sMiscellaneous.gettodaysactivity(self)  # callinggettodaysactivityapi
            if self.sAct:
                self.sValues = self.sAct.OrderRecordList
                index = iid = 0
                for sym in self.sValues:
                    self.tree.insert('', index, iid, values=(format(sym.ExtendedFields['Bank']),
                                                             format(sym.ExtendedFields['Branch']),
                                                             format(sym.ExtendedFields['Customer']),
                                                             format(sym.ExtendedFields['Deposit']),
                                                             format(sym.ExtendedFields['AcctType']),
                                                             format(sym.ExtendedFields['FixTraderId']),
                                                             format(sym.ExtendedFields['TraderId']),
                                                             format(sym.ExtendedFields['OriginalTraderId']),
                                                             format(sym.ExtendedFields['DateIndex']),
                                                             format(sym.ExtendedFields['TboAccountId']),
                                                             format(sym.ExtendedFields['TimeStamp']),
                                                             format(sym.ExtendedFields['Latency6']),
                                                             format(sym.ExtendedFields['Type']),
                                                             format(sym.ExtendedFields['DispName']),
                                                             format(sym.ExtendedFields['Price']),
                                                             format(sym.ExtendedFields['Volume']),
                                                             format(sym.ExtendedFields['Buyorsell']),
                                                             format(sym.ExtendedFields['GoodUntil']),
                                                             format(sym.ExtendedFields['VolumeType']),
                                                             format(sym.ExtendedFields['PriceType']),
                                                             format(sym.ExtendedFields['ExitVehicle']),
                                                             format(sym.ExtendedFields['Exchange']),
                                                             format(sym.ExtendedFields['Bid']),
                                                             format(sym.ExtendedFields['Ask']),
                                                             format(sym.ExtendedFields['Styp']),
                                                             format(sym.ExtendedFields['Basisvalue']),
                                                             format(sym.ExtendedFields['LinkedOrderRelationship']),
                                                             #format(sym.BOOKING_TYPE),
                                                             format(sym.ExtendedFields['OrderFlags']),
                                                             format(sym.ExtendedFields['TraderCapacity']),
                                                             format(sym.ExtendedFields['Currency']),
                                                             format(sym.ExtendedFields['LinkedOrderCancellation']),
                                                             format(sym.ExtendedFields['LinkedOrderId']),
                                                             format(sym.ExtendedFields['SpreadLegNumber']),
                                                             format(sym.ExtendedFields['GwBookSeqNo']),
                                                             format(sym.ExtendedFields['OrderId']),
                                                             format(sym.ExtendedFields['BookId']),
                                                             format(sym.ExtendedFields['ExtendedStateFlags2']),
                                                             format(sym.ExtendedFields['NewsDate']),
                                                             format(sym.ExtendedFields['NewsTime']),
                                                             format(sym.ExtendedFields['UtcOffset']),
                                                             format(sym.ExtendedFields['Rank']),
                                                             format(sym.ExtendedFields['CurrentStatus']),
                                                             format(sym.ExtendedFields['OriginalVolume']),
                                                             format(sym.ExtendedFields['OrderResidual']),
                                                             format(sym.ExtendedFields['VolumeTraded']),
                                                             format(sym.ExtendedFields['OriginalOrderId']),
                                                             format(sym.ExtendedFields['RefersToId']),
                                                             format(sym.ExtendedFields['ExtendedStateFlags']),
                                                             format(sym.ExtendedFields['ClaimedByClerk']),
                                                             format(sym.ExtendedFields['ExternalAcceptanceFlag']),
                                                             format(sym.ExtendedFields['RemoteId']),
                                                             format(sym.ExtendedFields['NewRemoteId']),
                                                             format(sym.ExtendedFields['AvgPrice']),
                                                             format(sym.ExtendedFields['TrdTime']),
                                                             format(sym.ExtendedFields['Commission']),
                                                             format(sym.ExtendedFields['AvgPrice']),
                                                             format(sym.ExtendedFields['VolumeTraded']),
                                                             format(sym.ExtendedFields['Table']),
                                                             format(sym.ExtendedFields['SpreadNumLegs']),
                                                             format(sym.ExtendedFields['OrderTag']),
                                                             format(sym.ExtendedFields['OmsClientType']),
                                                             format(sym.ExtendedFields['GoodFrom']),
                                                             format(sym.ExtendedFields['StopPrice']),
                                                             format(sym.ExtendedFields['UserMessage']),
                                                             format(sym.ExtendedFields['StrikePrc']),
                                                             format(sym.ExtendedFields['PairTarget']),
                                                             format(sym.ExtendedFields['PairSpreadType']),
                                                             format(sym.ExtendedFields['PairSpread']),
                                                             format(sym.ExtendedFields['PairRatio']),
                                                             format(sym.ExtendedFields['PairCash']),
                                                             format(sym.ExtendedFields['PairLeg2Benchmark']),
                                                             format(sym.ExtendedFields['PairLeg1Benchmark']),
                                                             format(sym.ExtendedFields['PairLeg2BenchmarkType']),
                                                             format(sym.ExtendedFields['PairLeg1BenchmarkType'])))
                    index = iid = index + 1

        elif self.bselection == 'Get Today\'s BrokenDownPositions':
            self.sDownpos = sMiscellaneous.gettodaysbrokendownpositions(self)  # callinggettodaysbrokendownapi
            if self.sDownpos:
                self.sValues = self.sDownpos.PositionRecords
                index = iid = 0
                for sym in self.sValues:
                    self.tree.insert('', index, iid, values=(format(sym.TboAccountId), format(sym.Bank),
                                                             format(sym.Branch), format(sym.Customer),
                                                             format(sym.Deposit),
                                                             format(sym.Currency), format(sym.AcctType),
                                                             format(sym.DispName),
                                                             format(sym.Rank), format(sym.Styp),
                                                             format(sym.AverageLong),
                                                             format(sym.Longpos), format(sym.AverageLong0),
                                                             format(sym.HistLongPrc0),
                                                             format(sym.Longpos0), format(sym.OrigLongpos0),
                                                             format(sym.AverageShort),
                                                             format(sym.Shortpos), format(sym.AverageShort0),
                                                             format(sym.HistShortPrc0), format(sym.Shortpos0),
                                                             format(sym.OrigShortpos0), format(sym.ScalpedProfit),
                                                             format(sym.Mmr), format(sym.Table),
                                                             format(sym.BoughtQty), format(sym.SoldQty),
                                                             format(sym.SoldShortQty), format(sym.BoughtAvgPrc),
                                                             format(sym.SoldAvgPrc), format(sym.SoldShortAvgPrc),
                                                             format(sym.Commission), format(sym.NetFees),
                                                             format(sym.HistScalpedProfit)))
                    index = iid = index + 1

        elif self.bselection == 'Get Today\'s NetPositions':
            self.sNetpos = sMiscellaneous.gettodaysnetpositions(self)  # callinggettodaysnetapi
            if self.sNetpos:
                self.sValues = self.sNetpos.AggregatePositionsList
                index = iid = 0
                for sym in self.sValues:
                    self.tree.insert('', index, iid, values=(format(sym.Bank),
                                                             format(sym.Branch), format(sym.Customer),
                                                             format(sym.Deposit),
                                                             format(sym.DispName), format(sym.IntradayAvgPrc),
                                                             format(sym.IntradayLongAvgPrc),
                                                             format(sym.IntradayLongPos), format(sym.IntradayPos),
                                                             format(sym.IntradayShortAvgPrc),
                                                             format(sym.IntradayShortPos), format(sym.LongPos),
                                                             format(sym.LongAvgPrc), format(sym.ShortAvgPrc),
                                                             format(sym.ShortPos),
                                                             format(sym.SoldAvgPrc), format(sym.SoldQty),
                                                             format(sym.SoldShortAvgPrc), format(sym.SoldShortQty),
                                                             format(sym.TotalAvgPrc), format(sym.TotalPos)))
                    index = iid = index + 1

        elif self.bselection == 'Get Symbols From Company Name':
            self.sSymData = sSymCompanyName.getsymbolsfromcompanyname(self)
            if self.sSymData:
                self.sValues = self.sSymData.SymbolDatalist
                index = iid = 0
                for sym in self.sValues:
                    self.tree.insert('', index, iid, values=(format(sym.DispName), format(sym.RicCode),
                                                             format(sym.BloombergCode), format(sym.BloombergCodeFull),
                                                             format(sym.Styp.value), format(sym.Country),
                                                             format(sym.ExchName),
                                                             format(sym.Sedol), format(sym.SymbolDesc),
                                                             format(sym.Cusip),
                                                             format(sym.CommodityName), format(sym.IsinNo),
                                                             format(sym.GicsSector),
                                                             format(sym.GicsIndustry), format(sym.GicsSubindustry)))
                    index = iid = index + 1

        elif self.bselection == 'Get Symbol From SEDOL, ISIN, CUSIP, etc':
            self.sSymInfo = sSymbolInfo.getsymbolfromalternatesymbology(self)
            if self.sSymInfo:
                self.sValues = self.sSymInfo.SymbolInfolist
                index = iid = 0
                for sym in self.sValues:
                    self.tree.insert('', index, iid, values=(format(sym.DispName), format(sym.RicCode),
                                                             format(sym.BloombergCode), format(sym.BloombergCodeFull),
                                                             format(sym.Styp.value), format(sym.Country),
                                                             format(sym.ExchName),
                                                             format(sym.Sedol), format(sym.SymbolDesc),
                                                             format(sym.Cusip),
                                                             format(sym.CommodityName), format(sym.IsinNo),
                                                             format(sym.GicsSector),
                                                             format(sym.GicsIndustry), format(sym.GicsSubindustry)))
                    index = iid = index + 1

        elif self.bselection == 'Get User Strategies':
            self.resp_stratData = sUserStrategies.getuserstrategies(self)
            if self.resp_stratData:
                self.sValues = self.resp_stratData.StrategyList
                index = iid = 0
                for sym in self.sValues:
                    self.tree.insert('', index, iid, values=(format(sym.FirmName), format(sym.UserName),
                                                             format(sym.AlgoName), format(sym.StrategyName),
                                                             format(sym.StratCreateDate)))
                    index = iid = index + 1

    def orderentrygrid(self, event):
        '''enable/disable entries for sumbitorder/submitpair'''
        # self.vars_pair.clear()
        self.bselection = self.TCombobox2.get()
        if self.bselection == 'Submit Pair Order':

            for i in range(3):  # OnlyLegParameters
                self.Label8 = tk.Entry(self.frame, width=10)
                self.Label8.grid(row=i + 1, column=2, sticky='nsew', padx=1, pady=1)
                self.Label8.config(font=('Times new roman', 12))
                self.vars_pair.append(self.Label8)

            self.fid_pair = ['Leg1 Extended Fields', 'Leg2 Extended Fields', 'Optional Fields',
                             'For ExtFields/OptFields Example: OPEN_CLOSE:OPEN;EXPIRATION:DAY']

            rows = 10
            lgt = len(self.fid_pair)

            for en_fid in self.fid_pair:  # FIDS_DICT
                self.fid_entry = tk.Entry(self.frame)
                self.fid_entry.insert('end', en_fid)
                self.fid_entry.grid(row=rows, column=0, sticky='nsew', padx=1, pady=1, ipadx=28)
                if rows == 13:
                    self.fid_entry.grid(row=14, column=0, sticky='nsew', padx=1, pady=1, columnspan=6)
                    self.fid_entry.config(font=('Helvetica', 9, 'bold'))
                self.fid_entry.config(state="readonly")
                self.vars_pair.append(self.fid_entry)
                rows += 1

            for ln in range(lgt - 1):  # VALUES_ENTRY
                self.fid_value = tk.Entry(self.frame, width=40)
                self.fid_value.grid(row=10 + ln, column=1, sticky='nsew', columnspan=4)
                self.fid_value.config(font=('Times new roman', 12))
                self.vars_pair.append(self.fid_value)

        else:
            for en_remove in self.vars_pair:
                en_remove.grid_remove()

            self.vars_pair.clear()

        if self.bselection == 'Get Symbols From Company Name' or self.bselection == 'Get Symbol From SEDOL, ISIN, CUSIP, etc':
            self.symbollookupUI()

        if self.bselection == 'Get User Strategies':
            self.userStrategyUI()

        if self.bselection == 'Submit Trade Report':
            self.TCombobox_trade['state'] = 'readonly'
        else:
            self.TCombobox_trade['state'] = 'disabled'

    def accountselection(self, event):
        '''User Account Combobox Selection'''
        self.aSelection = self.TCombobox1.get()

    def btnconnect(self):
        '''Connect GUI'''
        if self.top_Start:  # NotallowingmultipleUIcheck
            if self.top_Start.state() == "normal": self.top_Start.focus()

        else:
            self.list_Start.clear()
            self.top_Start = tk.Tk()
            self.top_Start.geometry("320x190")
            self.top_Start.minsize(120, 1)
            self.top_Start.maxsize(3844, 1061)
            self.top_Start.resizable(0, 0)
            self.top_Start.title("RealTick XAPI")
            if sys.platform == 'win32':		#allowing only for windows
                self.top_Start.iconbitmap(r'EzeSoft.ico')
            self.top_Start.configure(background="#d9d9d9")

            self.label_start = tk.Label(self.top_Start, text='Enter Login Information',
                                        background="darkslateblue", foreground="black")
            self.label_start.grid(row=0, column=0, sticky='nsew', rowspan=2, columnspan=2, ipady=2, padx=1, pady=1)

            self.fids_Start = ['User Name', 'Domain', 'Password', 'Locale']
            rows_Start = 5
            len_Start = len(self.fids_Start)

            for strt in self.fids_Start:  # FIDS_Change DICT
                self.Entry_start = tk.Entry(self.top_Start)
                self.Entry_start.insert('end', strt)
                self.Entry_start.grid(row=rows_Start, column=0, sticky='nsew', padx=1, pady=1)
                self.Entry_start.config(font=('Helvetica', 9, 'bold'))
                self.Entry_start.config(state="readonly")
                self.Entry_start.grid_propagate(0)
                rows_Start += 1

            for ln in range(len_Start):  # VALUES ENTRY
                self.Entry_valstrt = tk.Entry(self.top_Start)
                self.Entry_valstrt.grid(row=ln + 5, column=1, sticky='nsew', padx=1, pady=1)
                self.Entry_valstrt.config(font=('Times new roman', 12))
                if ln == 2:
                    self.Entry_valstrt.config(show="*")
                self.Entry_valstrt.grid_propagate(0)
                self.list_Start.append(self.Entry_valstrt)

            btn_connectvalues = ['OK', 'CANCEL']
            self.btn_connect = []
            x = 0.15
            for i in range(len(btn_connectvalues)):
                self.Button_connect = tk.Button(self.top_Start)
                self.Button_connect.place(relx=x, rely=0.77, height=31, width=57)
                self.Button_connect.configure(activebackground="#ececec")
                self.Button_connect.configure(activeforeground="#000000")
                self.Button_connect.configure(background="black")
                self.Button_connect.configure(disabledforeground="#a3a3a3")
                self.Button_connect.configure(foreground="white")
                self.Button_connect.configure(highlightbackground="#d9d9d9")
                self.Button_connect.configure(highlightcolor="black")
                self.Button_connect.configure(pady="0")
                self.Button_connect.configure(text=btn_connectvalues[i])
                self.btn_connect.append(self.Button_connect)
                x += 0.5

            self.btn_connect[0].bind('<ButtonRelease>', lambda event: sMain.btnok_connect(self))
            self.top_Start.protocol("WM_DELETE_WINDOW", self.destroy_startwindow)
            self.btn_connect[1].bind('<ButtonRelease>', lambda event: self.destroy_startwindow())

    def btnchangePasswordSRP(self):

        if self.top_Start:  # NotallowingmultipleUIcheck
            if self.top_Start.state() == "normal": self.top_Start.focus()

        else:
            self.list_Start.clear()
            self.top_Start = tk.Tk()
            self.top_Start.geometry("320x210")
            self.top_Start.minsize(120, 1)
            self.top_Start.maxsize(3844, 1061)
            self.top_Start.resizable(0, 0)
            self.top_Start.title("RealTick XAPI")
            if sys.platform == 'win32':		#allowing only for windows
                self.top_Start.iconbitmap(r'EzeSoft.ico')
        
            self.top_Start.configure(background="#d9d9d9")

            self.label_start = tk.Label(self.top_Start, text='Enter Change Password Information',
                                        background="darkslateblue", foreground="black")

            self.label_start.grid(row=0, column=0, sticky='nsew', rowspan=2, columnspan=2, ipady=2, padx=1, pady=1)

            self.fids_Start = ['UserName', 'Domain', 'OldPassword', 'NewPassword', 'Locale']

            rows_Start = 5
            len_Start = len(self.fids_Start)

            for strt in self.fids_Start:  # FIDS_Change DICT
                self.Entry_start = tk.Entry(self.top_Start)
                self.Entry_start.insert('end', strt)
                self.Entry_start.grid(row=rows_Start, column=0, sticky='nsew', padx=1, pady=1)
                self.Entry_start.config(font=('Helvetica', 9, 'bold'))
                self.Entry_start.config(state="readonly")
                self.Entry_start.grid_propagate(0)
                rows_Start += 1

            length = len(self.credentials)
            if length:
                self.userlogged = True
            else:
                self.userlogged = False

            for ln in range(len_Start):  # VALUES ENTRY
                entryText = tk.StringVar()
                self.Entry_valstrt = tk.Entry(self.top_Start, textvariable=entryText)
                self.Entry_valstrt.grid(row=ln + 5, column=1, sticky='nsew', padx=1, pady=1)
                self.Entry_valstrt.config(font=('Times new roman', 12))

                if ln == 0:
                    if self.userlogged == True:
                        self.Entry_valstrt = tk.Entry(self.top_Start)
                        self.Entry_valstrt.insert('end', self.credentials[0].upper())
                        self.Entry_valstrt.grid(row=ln + 5, column=1, sticky='nsew', padx=1, pady=1)
                        self.Entry_valstrt.configure(state='readonly')
                if ln == 1:
                    if self.userlogged == True:
                        self.Entry_valstrt = tk.Entry(self.top_Start)
                        self.Entry_valstrt.insert('end', self.credentials[1].upper())
                        self.Entry_valstrt.grid(row=ln + 5, column=1, sticky='nsew', padx=1, pady=1)
                        self.Entry_valstrt.configure(state='readonly')
                if ln == 2:
                    self.Entry_valstrt.config(show="*")
                if ln == 3:
                    self.Entry_valstrt.config(show="*")
                if ln == 4:
                    if self.userlogged == True:
                        self.Entry_valstrt = tk.Entry(self.top_Start)
                        self.Entry_valstrt.insert('end', self.credentials[3].upper())
                        self.Entry_valstrt.grid(row=ln + 5, column=1, sticky='nsew', padx=1, pady=1)
                        self.Entry_valstrt.configure(state='readonly')

                self.Entry_valstrt.grid_propagate(0)
                self.list_Start.append(self.Entry_valstrt)

            btn_changePasswordSRPvalues = ['OK', 'CANCEL']
            self.btn_changePasswordSRP = []
            x = 0.15
            for i in range(len(btn_changePasswordSRPvalues)):
                self.Button_changePasswordSRP = tk.Button(self.top_Start)
                self.Button_changePasswordSRP.place(relx=x, rely=0.77, height=31, width=57)
                self.Button_changePasswordSRP.configure(activebackground="#ececec")
                self.Button_changePasswordSRP.configure(activeforeground="#000000")
                self.Button_changePasswordSRP.configure(background="black")
                self.Button_changePasswordSRP.configure(disabledforeground="#a3a3a3")
                self.Button_changePasswordSRP.configure(foreground="white")
                self.Button_changePasswordSRP.configure(highlightbackground="#d9d9d9")
                self.Button_changePasswordSRP.configure(highlightcolor="black")
                self.Button_changePasswordSRP.configure(pady="0")
                self.Button_changePasswordSRP.configure(text=btn_changePasswordSRPvalues[i])
                self.btn_changePasswordSRP.append(self.Button_changePasswordSRP)
                x += 0.5

            self.btn_changePasswordSRP[0].bind('<ButtonRelease>', lambda event: sMain.btnok_changePasswordSRP(self))
            self.top_Start.protocol("WM_DELETE_WINDOW", self.destroy_startwindow)
            self.btn_changePasswordSRP[1].bind('<ButtonRelease>', lambda event: self.destroy_startwindow())

    def btnfidlist(self):
        '''start thread for fidlist'''
        thread_fid = threading.Thread(target=sMain.fid_func, args=[self])
        thread_fid.name = 'FidlistThread'
        thread_fid.daemon = True
        thread_fid.start()

    def btnsubmit(self):
        '''Calling submit order func in xapi_client.py'''
        self.symbol = self.vars[0].get()
        self.side = self.vars[1].get()
        self.qty = self.vars[2].get()
        self.route = self.vars[3].get()

        self.staged_str = self.vars[4].get()
        self.staged_Order = str_to_bool(self.staged_str)

        self.claim_str = self.vars[5].get()
        self.claimRequired = str_to_bool(self.claim_str)

        self.trade_ordtype = self.vars[6].get()

        self.order_ticketid = self.vars[7].get()
        self.order_ordertag = self.vars[8].get()

        self.ext_str = self.vars[9].get()  # SingleOrderExtendedFields
        if self.ext_str:
            self.ext_split = re.split(r'[;\s]\s*', self.ext_str)
            self.ext_Leg = list_to_dict(self.ext_split)

        # For Pairs
        if self.vars_pair:
            self.symbol_2 = self.vars_pair[0].get()
            self.side_2 = self.vars_pair[1].get()
            self.qty_2 = self.vars_pair[2].get()

            self.ext_str1 = self.vars_pair[7].get()  # Leg1ExtendedFields
            if self.ext_str1:
                self.ext_split1 = re.split(r'[;\s]\s*', self.ext_str1)
                self.ext_Leg1 = list_to_dict(self.ext_split1)

            self.ext_str2 = self.vars_pair[8].get()  # Leg2ExtendedFields
            if self.ext_str2:
                self.ext_split2 = re.split(r'[;\s]\s*', self.ext_str2)
                self.ext_Leg2 = list_to_dict(self.ext_split2)

            self.ext_opt = self.vars_pair[9].get()  # OptionalFields
            if self.ext_opt:
                self.ext_splitopt = re.split(r'[;\s]\s*', self.ext_opt)
                self.Optional_field = list_to_dict(self.ext_splitopt)

        sMain.btnsubmit(self)

    def symbollookupUI(self):
        self.list_Sym.clear()
        self.top_Sym = tk.Tk()
        self.top_Sym.geometry("320x80")
        self.top_Sym.minsize(176, 1)
        self.top_Sym.maxsize(1924, 1050)
        self.top_Sym.resizable(0, 0)
        self.top_Sym.title("Symbol Lookup")
        if sys.platform == 'win32':		#allowing only for windows
            self.top_Sym.iconbitmap(r'EzeSoft.ico')

        self.top_Sym.configure(background="#d9d9d9")

        self.fids_Sym = ['Company Name/Symbol', 'Select Alternate Symbology']
        rows_Sym = 0

        for mkt_in in self.fids_Sym:  # fids_Sym DICT
            self.Entry_sym = tk.Entry(self.top_Sym)
            self.Entry_sym.insert('end', mkt_in)
            self.Entry_sym.grid(row=rows_Sym, column=0, sticky='nsew', rowspan=3, ipadx=13, padx=1, pady=1)
            self.Entry_sym.config(state="readonly")
            self.Entry_sym.grid_propagate(0)
            rows_Sym += 3

        self.Entry_valsym = tk.Entry(self.top_Sym)
        self.Entry_valsym.grid(row=0, column=1, sticky='nsew', rowspan=3, padx=1, pady=1)
        self.Entry_valsym.config(font=('Times new roman', 12))
        self.Entry_valsym.grid_propagate(0)
        self.list_Sym.append(self.Entry_valsym)

        self.TCombobox1_Sym = ttk.Combobox(self.top_Sym)
        self.TCombobox1_Sym.grid(row=4, column=1, sticky='nsew', padx=1, pady=1)
        self.TCombobox1_Sym.configure(textvariable=combobox_sym)
        self.TCombobox1_Sym.configure(takefocus="")
        self.TCombobox1_Sym.configure(values=['ISIN', 'SEDOL', 'RIC', 'CUSIP', 'BBG'])
        self.TCombobox1_Sym['state'] = 'readonly'
        self.TCombobox1_Sym.bind("<<ComboboxSelected>>", self.symcombobox)
        self.TCombobox1_Sym.current(0)
        self.symSelection = self.TCombobox1_Sym.get()
        self.symlookup = 0  # defaultISIN

        if self.bselection == 'Get Symbols From Company Name':
            self.TCombobox1_Sym.configure(state='disabled')

        btn_symvalues = ['OK', 'CANCEL']
        self.btn_sym = []
        for i in range(len(btn_symvalues)):
            self.Button_sym = tk.Button(self.top_Sym)
            self.Button_sym.grid(row=15, column=i, sticky='nsew', rowspan=4)
            self.Button_sym.configure(activebackground="#ececec")
            self.Button_sym.configure(activeforeground="#000000")
            self.Button_sym.configure(background="black")
            self.Button_sym.configure(disabledforeground="#a3a3a3")
            self.Button_sym.configure(foreground="white")
            self.Button_sym.configure(highlightbackground="#d9d9d9")
            self.Button_sym.configure(highlightcolor="black")
            self.Button_sym.configure(pady="0")
            self.Button_sym.configure(text=btn_symvalues[i])
            self.btn_sym.append(self.Button_sym)

        self.btn_sym[0].configure(command=self.ok_symlookup)
        self.btn_sym[1].bind('<ButtonRelease>', lambda event: close_windows(self.top_Sym))

    def userStrategyUI(self):
        self.list_strat.clear()
        self.top_strat = tk.Tk()
        self.top_strat.geometry("320x60")
        self.top_strat.minsize(176, 1)
        self.top_strat.maxsize(1924, 1050)
        self.top_strat.resizable(0, 0)
        self.top_strat.title("Enter Your Firm Name")
        if sys.platform == 'win32':		#allowing only for windows
            self.top_strat.iconbitmap(r'EzeSoft.ico')
        self.top_strat.configure(background="#d9d9d9")

        self.fids_Strat = ['Firm Name']
        rows_Strat = 1

        for mkt_in in self.fids_Strat:  # fids_Strat DICT
            self.Entry_sym = tk.Entry(self.top_strat)
            self.Entry_sym.insert('end', mkt_in)
            self.Entry_sym.grid(row=rows_Strat, column=0, sticky='nsew', rowspan=3, ipadx=13, padx=1, pady=1)
            self.Entry_sym.config(state="readonly")
            self.Entry_sym.grid_propagate(0)
            rows_Strat += 3

        self.entry_firm = tk.Entry(self.top_strat)
        self.entry_firm.grid(row=1, column=1, sticky='nsew', rowspan=3, padx=1, pady=1)
        self.entry_firm.config(font=('Times new roman', 12))
        self.entry_firm.grid_propagate(0)
        self.list_strat.append(self.entry_firm)

        btn_sym1values = ['OK', 'CANCEL']
        self.btn_sym1 = []
        for i in range(len(btn_sym1values)):
            self.Button_sym = tk.Button(self.top_strat)
            self.Button_sym.grid(row=40, column=i, sticky='nsew', rowspan=4)
            self.Button_sym.configure(activebackground="#ececec")
            self.Button_sym.configure(activeforeground="#000000")
            self.Button_sym.configure(background="black")
            self.Button_sym.configure(disabledforeground="#a3a3a3")
            self.Button_sym.configure(foreground="white")
            self.Button_sym.configure(highlightbackground="#d9d9d9")
            self.Button_sym.configure(highlightcolor="black")
            self.Button_sym.configure(pady="0")
            self.Button_sym.configure(text=btn_sym1values[i])
            self.btn_sym1.append(self.Button_sym)

        self.btn_sym1[0].configure(command=self.ok_symlookup)
        self.btn_sym1[1].bind('<ButtonRelease>', lambda event: close_windows(self.top_strat))

    def symcombobox(self, event):
        '''Symbolselection func'''
        self.symSelection = self.TCombobox1_Sym.get()
        if self.symSelection == 'ISIN':
            self.symlookup = 0
        elif self.symSelection == 'SEDOL':
            self.symlookup = 1
        elif self.symSelection == 'RIC':
            self.symlookup = 2
        elif self.symSelection == 'CUSIP':
            self.symlookup = 3
        else:  # BBG
            self.symlookup = 4

    def ok_symlookup(self):
        self.requestapi_grid()  # respective gui for requested api
        self.requestapiresponse()  # callingapi

    def btnAlloc(self):
        '''Allocation GUI'''
        self.list_alloc.clear()
        self.allocUI = tk.Tk()
        self.allocUI.geometry("300x130")
        self.allocUI.minsize(176, 1)
        self.allocUI.maxsize(1924, 1050)
        self.allocUI.resizable(0, 0)
        self.allocUI.title("Allocation Details")
        if sys.platform == 'win32':		#allowing only for windows
            self.allocUI.iconbitmap(r'EzeSoft.ico')
        self.allocUI.configure(background="#d9d9d9")

        self.fids_Alloc = ['Target Acount', 'Quantity', 'Price', 'Type of Allocation']
        rows_Alloc = 0

        for chng in self.fids_Alloc:  # FIDS DICT
            self.Entry_alloc = tk.Entry(self.allocUI)
            self.Entry_alloc.insert('end', chng)
            self.Entry_alloc.grid(row=rows_Alloc, column=0, sticky='nsew', padx=1, pady=1)
            self.Entry_alloc.config(state="readonly")
            self.Entry_alloc.grid_propagate(0)
            rows_Alloc += 1

        self.tgcombox_Alloc = ttk.Combobox(self.allocUI)  # for fetching accounts from source account
        self.tgcombox_Alloc.grid(row=0, column=1, sticky='nsew', padx=1, pady=1)
        self.tgcombox_Alloc.configure(textvariable=combobox_acctalloc)
        self.tgcombox_Alloc.configure(takefocus="")
        self.tgcombox_Alloc.bind("<<ComboboxSelected>>", self.tgAcctcombobox)
        self.tgcombox_Alloc['state'] = 'readonly'

        if self.combobox_values:
            self.tgcombox_Alloc['values'] = self.combobox_values
            self.tgcombox_Alloc.current(0)
            self.tgAcctselection = self.tgcombox_Alloc.get()

        for ln in range(2):  # VALUES ENTRY
            self.val_alloc = tk.Entry(self.allocUI)
            self.val_alloc.grid(row=ln + 1, column=1, sticky='nsew', padx=1, pady=1)
            self.val_alloc.config(font=('Times new roman', 12))
            self.val_alloc.grid_propagate(0)
            self.list_alloc.append(self.val_alloc)

        self.typecombox_Alloc = ttk.Combobox(self.allocUI)
        self.typecombox_Alloc.grid(row=3, column=1, sticky='nsew', padx=1, pady=1)
        self.typecombox_Alloc.configure(textvariable=combobox_typealloc)
        self.typecombox_Alloc.configure(takefocus="")
        self.typecombox_Alloc.configure(values=['UserSubmitAllocation', 'UserSubmitAllocationEx'])
        self.typecombox_Alloc.bind("<<ComboboxSelected>>", self.typeAlloccombobox)
        self.typecombox_Alloc['state'] = 'readonly'
        self.typecombox_Alloc.current(1)
        self.type_alloc = self.typecombox_Alloc.get()

        btn_allocvalues = ['OK', 'CANCEL']
        self.btn_alloc = []
        for i in range(len(btn_allocvalues)):
            self.Button_alloc = tk.Button(self.allocUI)
            self.Button_alloc.grid(row=15, column=i, sticky='nsew', rowspan=4, columnspan=1)
            self.Button_alloc.configure(activebackground="#ececec")
            self.Button_alloc.configure(activeforeground="#000000")
            self.Button_alloc.configure(background="black")
            self.Button_alloc.configure(disabledforeground="#a3a3a3")
            self.Button_alloc.configure(foreground="white")
            self.Button_alloc.configure(highlightbackground="#d9d9d9")
            self.Button_alloc.configure(highlightcolor="black")
            self.Button_alloc.configure(pady="0")
            self.Button_alloc.configure(text=btn_allocvalues[i])
            self.btn_alloc.append(self.Button_alloc)

        self.list_alloc[0].insert(0, self.qty_fromorder)
        self.list_alloc[1].insert(0, self.prccol)

        self.btn_alloc[0].configure(command=self.ok_allocUI)
        self.btn_alloc[1].bind('<ButtonRelease>', lambda event: close_windows(self.allocUI))

    def ok_allocUI(self):
        '''Function for Calling Submit Allocation Order API in xapi_client.py'''
        if not self.combobox_values:
            tk.messagebox.showinfo("Message", 'Please Fetch Accounts From Get User Accounts')
            return False
        self.source_qty = self.list_alloc[0].get()
        self.source_prc = self.list_alloc[1].get()

        sMain.submitallocationorder(self)

    def tgAcctcombobox(self, event):
        '''Target Account selection func'''
        self.tgAcctselection = self.tgcombox_Alloc.get()

    def typeAlloccombobox(self, event):
        '''Type of Allocation selection func'''
        self.type_alloc = self.typecombox_Alloc.get()

    def btnchange(self):
        '''GUI for CHANGE ORDER'''

        if self.bChange:
            self.list_changeSingle.clear()
            self.change_singleUI = tk.Tk()
            self.change_singleUI.geometry("330x90")
            self.change_singleUI.minsize(176, 1)
            self.change_singleUI.maxsize(1924, 1050)
            self.change_singleUI.resizable(0, 0)
            self.change_singleUI.title("Change Single Order")
            if sys.platform == 'win32':		#allowing only for windows
                self.change_singleUI.iconbitmap(r'EzeSoft.ico')
            self.change_singleUI.configure(background="#d9d9d9")

            self.fids_Change = ['Quantity', 'Extended Fields']
            rows_Change = 0
            len_Change = len(self.fids_Change)

            for chng in self.fids_Change:  # FIDS_Change DICT
                self.Entry_changesingle = tk.Entry(self.change_singleUI)
                self.Entry_changesingle.insert('end', chng)
                self.Entry_changesingle.grid(row=rows_Change, column=0, sticky='nsew', ipady=2, padx=1, pady=1)
                self.Entry_changesingle.config(state="readonly")
                self.Entry_changesingle.grid_propagate(0)
                rows_Change += 1

            for ln in range(len_Change):  # VALUES ENTRY
                self.val_single = tk.Entry(self.change_singleUI)
                self.val_single.grid(row=ln, column=1, sticky='nsew', ipadx=16, ipady=2, padx=1, pady=1)
                self.val_single.config(font=('Times new roman', 12))
                self.val_single.grid_propagate(0)
                self.list_changeSingle.append(self.val_single)

            self.list_changeSingle[0].insert(0, self.qty_fromorder)

            btn_changevalues = ['OK', 'CANCEL']
            self.btn_change = []
            for i in range(len(btn_changevalues)):
                self.Button_change = tk.Button(self.change_singleUI)
                self.Button_change.grid(row=22, column=i, sticky='nsew', rowspan=4, columnspan=1)
                self.Button_change.configure(activebackground="#ececec")
                self.Button_change.configure(activeforeground="#000000")
                self.Button_change.configure(background="black")
                self.Button_change.configure(disabledforeground="#a3a3a3")
                self.Button_change.configure(foreground="white")
                self.Button_change.configure(highlightbackground="#d9d9d9")
                self.Button_change.configure(highlightcolor="black")
                self.Button_change.configure(pady="0")
                self.Button_change.configure(text=btn_changevalues[i])
                self.btn_change.append(self.Button_change)

            self.btn_change[0].configure(command=self.ok_changesingleorder)
            self.btn_change[1].bind('<ButtonRelease>', lambda event: close_windows(self.change_singleUI))

        else:
            self.list_changePair.clear()
            self.change_pairUI = tk.Tk()
            self.change_pairUI.geometry("300x180")
            self.change_pairUI.minsize(176, 1)
            self.change_pairUI.maxsize(1924, 1050)
            self.change_pairUI.resizable(0, 0)
            self.change_pairUI.title("Change Pair Order")
            if sys.platform == 'win32':		#allowing only for windows
                self.change_pairUI.iconbitmap(r'EzeSoft.ico')
            self.change_pairUI.configure(background="#d9d9d9")
            self.fids_Change = ['Leg1 Quantity', 'Leg2 Quantity', 'Leg1 Extended Fields', 'Leg2 ExtendedFileds',
                                'Optional Fields']
            rows_Change = 0
            len_Change = len(self.fids_Change)

            for chng in self.fids_Change:  # FIDS_Change DICT
                self.Entry_change = tk.Entry(self.change_pairUI)
                self.Entry_change.insert('end', chng)
                self.Entry_change.grid(row=rows_Change, column=0, sticky='nsew', padx=1, pady=1)
                self.Entry_change.config(state="readonly")
                self.Entry_change.grid_propagate(0)
                rows_Change += 1

            for ln in range(len_Change):  # VALUES ENTRY
                self.Entry_val = tk.Entry(self.change_pairUI)
                self.Entry_val.grid(row=ln, column=1, sticky='nsew', padx=1, pady=1)
                self.Entry_val.config(font=('Times new roman', 12))
                self.Entry_val.grid_propagate(0)
                self.list_changePair.append(self.Entry_val)

            self.list_changePair[0].insert(0, self.qty_fromorder)

            btn_changepairvalues = ['OK', 'CANCEL']
            self.btn_changepair = []
            for i in range(len(btn_changepairvalues)):
                self.Button_changepair = tk.Button(self.change_pairUI)
                self.Button_changepair.grid(row=15, column=i, sticky='nsew', rowspan=4, columnspan=1)
                self.Button_changepair.configure(activebackground="#ececec")
                self.Button_changepair.configure(activeforeground="#000000")
                self.Button_changepair.configure(background="black")
                self.Button_changepair.configure(disabledforeground="#a3a3a3")
                self.Button_changepair.configure(foreground="white")
                self.Button_changepair.configure(highlightbackground="#d9d9d9")
                self.Button_changepair.configure(highlightcolor="black")
                self.Button_changepair.configure(pady="0")
                self.Button_changepair.configure(text=btn_changepairvalues[i])
                self.btn_changepair.append(self.Button_changepair)

            self.btn_changepair[0].configure(command=self.ok_changepairorder)
            self.btn_changepair[1].bind('<ButtonRelease>', lambda event: close_windows(self.change_pairUI))

    def ok_changesingleorder(self):
        '''Function for Change single Order in xapi_client.py'''
        self.str1 = self.list_changeSingle[1].get()
        self.Changed_str = self.str1.upper()
        if self.Changed_str != '':
            self.ext_split = re.split(r'[;\s]\s*', self.Changed_str)
            self.extchange_Leg1 = list_to_dict(self.ext_split)

        sMain.changesingleorder(self)

    def ok_changepairorder(self):
        '''Calling Change Pair Order in xapi_client.py '''
        self.str1 = self.list_changePair[2].get()
        self.Changed_str = self.str1.upper()
        if self.Changed_str != '':
            self.ext_split = re.split(r'[;\s]\s*', self.Changed_str)
            self.extchange_Leg1 = list_to_dict(self.ext_split)

        self.str2 = self.list_changePair[3].get()
        self.Changed_str1 = self.str2.upper()
        if self.Changed_str1 != '':
            self.ext_split1 = re.split(r'[;\s]\s*', self.Changed_str1)
            self.extchange_Leg2 = list_to_dict(self.ext_split1)

        self.str3 = self.list_changePair[4].get()
        self.Changed_str2 = self.str3.upper()
        if self.Changed_str2 != '':
            self.ext_split2 = re.split(r'[;\s]\s*', self.Changed_str2)
            self.extchange_Opt = list_to_dict(self.ext_split2)

        sMain.changepairorder(self)  # Callingpairchange

    def btncancel(self):
        sMain.cancelorder(self)

    def btnmarket(self):
        '''Market GUI'''
        self.list_Mkt.clear()
        self.top_Mkt = tk.Tk()
        self.top_Mkt.geometry("310x199")
        self.top_Mkt.minsize(176, 1)
        self.top_Mkt.maxsize(1924, 1050)
        self.top_Mkt.resizable(0, 0)
        self.top_Mkt.title("Market Data")
        if sys.platform == 'win32':		#allowing only for windows
            self.top_Mkt.iconbitmap(r'EzeSoft.ico')
        self.top_Mkt.configure(background="#d9d9d9")
        self.list_Mkt = []

        self.fids_Mkt = ['Market Data Api', 'Symbols', '(Separated by comma)', 'Request', 'Advise', 'Market Data Level']
        rows_Mkt = 1
        len_Mkt = len(self.fids_Mkt)

        for mkt_in in self.fids_Mkt:  # fids_Mkt DICT
            self.Entry_mkt = tk.Entry(self.top_Mkt)
            self.Entry_mkt.insert('end', mkt_in)
            if mkt_in == '(Separated by comma)':
                self.Entry_mkt.grid(row=rows_Mkt, column=1, sticky='nsew', rowspan=3, padx=1, ipady=2, ipadx=4, pady=1)
            else:
                self.Entry_mkt.grid(row=rows_Mkt, column=0, sticky='nsew', rowspan=3, padx=1, ipady=2, ipadx=4, pady=1)
            self.Entry_mkt.config(state="readonly")
            self.Entry_mkt.grid_propagate(0)
            rows_Mkt += 3

        self.TCombobox1_Data = ttk.Combobox(self.top_Mkt)
        self.TCombobox1_Data.grid(row=0, column=1, sticky='nsew', rowspan=3, ipady=2, ipadx=4, padx=1, pady=1)
        self.TCombobox1_Data.configure(textvariable=combobox_mkt)
        self.TCombobox1_Data.configure(takefocus="")
        self.TCombobox1_Data.configure(
            values=['Subscribe Level1 Ticks', 'Subscribe Level2 Ticks', 'Add Symbols', 'Remove Symbols',
                    'UnSubscribe Level1 Data', 'UnSubscribe Level2 Data'])
        self.TCombobox1_Data.current(0)
        self.TCombobox1_Data.bind("<<ComboboxSelected>>", self.mktcombobox)
        self.TCombobox1_Data['state'] = 'readonly'

        ln1 = 4  # becauseofrowspan
        for ln in range(len_Mkt - 1):  # VALUES ENTRY
            if ln == 2 or ln == 3:
                self.TCombobox_bool = ttk.Combobox(self.top_Mkt)
                self.TCombobox_bool.grid(row=ln1, column=1, sticky='nsew', rowspan=3, ipady=2, ipadx=4, padx=1, pady=1)
                self.TCombobox_bool.configure(textvariable=combobox_req)
                if ln == 3:
                    self.TCombobox_bool.configure(textvariable=combobox_adv)
                self.TCombobox_bool.configure(takefocus="")
                self.TCombobox_bool.pack_propagate(0)
                self.TCombobox_bool.configure(values=['TRUE', 'FALSE'])
                self.TCombobox_bool.current(0)
                self.TCombobox_bool['state'] = 'readonly'
                self.list_Mkt.append(self.TCombobox_bool)
            elif ln == 4:
                self.TCombobox_lev = ttk.Combobox(self.top_Mkt)
                self.TCombobox_lev.grid(row=ln1, column=1, sticky='nsew', rowspan=3, padx=1, ipady=2, ipadx=4, pady=1)
                self.TCombobox_lev.configure(textvariable=combobox_level)
                self.TCombobox_lev.configure(takefocus="")
                self.TCombobox_lev.pack_propagate(0)
                self.TCombobox_lev.configure(values=['Level1', 'Level2'])
                self.TCombobox_lev.current(0)
                self.TCombobox_lev['state'] = 'disabled'
                self.list_Mkt.append(self.TCombobox_lev)
            elif ln == 0:
                self.Entry_valmkt = tk.Entry(self.top_Mkt)
                self.Entry_valmkt.grid(row=ln1, column=1, sticky='nsew', rowspan=3, padx=1, ipady=2, ipadx=4, pady=1)
                self.Entry_valmkt.config(font=('Times new roman', 12))
                self.Entry_valmkt.grid_propagate(0)
                self.list_Mkt.append(self.Entry_valmkt)
            ln1 += 3

        self.req_Mkt = str_to_bool(self.list_Mkt[1].get())
        self.mktSelection = self.TCombobox1_Data.get()
        self.adv_Mkt = str_to_bool(self.list_Mkt[2].get())

        btn_mktvalues = ['OK', 'CANCEL']
        self.btn_mkt = []
        y = 0
        for i in range(len(btn_mktvalues)):
            self.Button_Mkt = tk.Button(self.top_Mkt)
            if i <= 1:
                self.Button_Mkt.grid(row=25, column=y, sticky='nsew', rowspan=3, ipady=2, ipadx=4, padx=1, pady=1)
                y += 1
            self.Button_Mkt.configure(activebackground="#ececec")
            self.Button_Mkt.configure(activeforeground="#000000")
            self.Button_Mkt.configure(background="black")
            self.Button_Mkt.configure(disabledforeground="#a3a3a3")
            self.Button_Mkt.configure(foreground="white")
            self.Button_Mkt.configure(highlightbackground="#d9d9d9")
            self.Button_Mkt.configure(highlightcolor="black")
            self.Button_Mkt.configure(pady="0")
            self.Button_Mkt.configure(text=btn_mktvalues[i])
            self.btn_mkt.append(self.Button_Mkt)

        self.btn_mkt[0].configure(command=self.btnok_marketdata)
        self.btn_mkt[1].config(command=self.top_Mkt.destroy)

    def mktcombobox(self, event):
        '''MarketdataAPIselection func'''
        self.mktSelection = self.TCombobox1_Data.get()
        if self.mktSelection == 'Add Symbols' or self.mktSelection == 'Remove Symbols':
            self.TCombobox_lev['state'] = 'readonly'
        else:
            self.TCombobox_lev['state'] = 'disabled'

    def btnok_marketdata(self):
        '''Calling market data api in xapi_client.py'''
        self.Sym_str = self.list_Mkt[0].get()
        self.Sym_ip = self.Sym_str.split(',')

        self.req1 = self.list_Mkt[1].get()
        self.req_Mkt = str_to_bool(self.req1)

        self.adv1 = self.list_Mkt[2].get()
        self.adv_Mkt = str_to_bool(self.adv1)

        if self.mktSelection == 'Add Symbols' or self.mktSelection == 'Remove Symbols':
            self.marketLevel = self.list_Mkt[3].get()

        sMain.marketdata(self)

    def btnviewsource(self):
        '''start thread for vwsourcecode'''
        thread_vw = threading.Thread(target=sMain.viewsourcecode, args=[self])
        thread_vw.name = 'ViewsourcecodeThread'
        thread_vw.daemon = True
        thread_vw.start()

    def __adjust_wind(self, event):
        '''Paned window funtion which handles the movable grid'''
        paned = event.widget
        pos = [800, ]
        i = 0
        for sash in pos:
            paned.sashpos(i, sash)
            i += 1
        paned.unbind('<map>', self.__funcwid)
        del self.__funcwid

    def __init__(self, top=None):
        _bgcolor = '#d9d9d9'  # X11 color: 'gray85'
        _fgcolor = '#000000'  # X11 color: 'black'
        _compcolor = '#d9d9d9'  # X11 color: 'gray85'
        _ana1color = '#d9d9d9'  # X11 color: 'gray85'
        _ana2color = '#ececec'  # Closest X11 color: 'gray92'
        self.style = ttk.Style()
        if sys.platform == "win32":
            self.style.theme_use('winnative')
        self.style.configure('.', background=_bgcolor)
        self.style.configure('.', foreground=_fgcolor)
        self.style.configure('.', font="TkDefaultFont")
        self.style.map('.', background=
        [('selected', _compcolor), ('active', _ana2color)])

        top.geometry("917x748+405+167")
        top.minsize(1200, 0)
        top.maxsize(3844, 1061)
        top.resizable(1, 1)
        # top.state('zoomed')
        top.protocol("WM_DELETE_WINDOW", self.destroy_window)
        vresion_lst = []
        for line in open("version.txt").readlines():
            if line != '\n':
                r = line.split()[2]
                if r.isdigit():
                    vresion_lst.append(r)

        version_num = vresion_lst[0] + '.' + vresion_lst[1] + '.' + vresion_lst[2] + '.' + vresion_lst[3]
        top.title("Eze EMS xAPI-" + version_num)
        if sys.platform == 'win32':		#allowing only for windows
            top.iconbitmap(r'EzeSoft.ico')

        top.configure(background="#d9d9d9")

        self.success = 'success'
        self.orderList = []  # For Order Blotter
        self.bselection = ''  # OrderEntryComboboxSelection
        self.valcol = ''  # OrderID from grid
        self.vars_pair = []  # Pair list input values
        self.vars = []  # Order list input values
        self.symcol = ''  # Symbol from grid
        self.sidecol = ''  # Side from grid
        self.prccol = ''  # Price from grid
        self.prctypecol = ''  # PriceType from grid
        self.Ordertypecol = ''  # Ordertype from grid
        self.userToken = ''  # global dec of token which send along with all APIs
        self.aSelection = ''  # Account selection
        self.expcol = ''  # Expiration from grid
        self.childIds = {}  # Dict for childOrderIds
        self.Sym_str = ''
        self.Sym_ip = ''
        self.list_changePair = []  # Change UI input values in list
        self.list_changeSingle = []
        self.list_Mkt = []  # MarketData UI input values in list
        self.list_Start = []  # Start UI input values in list
        self.list_Sym = []
        self.list_strat = []
        self.ext_Leg = ''
        self.ext_Leg1 = ''
        self.ext_Leg2 = ''
        self.Optional_field = ''
        self.extchange_Leg1 = ''
        self.extchange_Leg2 = ''
        self.extchange_Opt = ''
        self.type_pair = ''
        self.mktSelection = ''  # MarketdataAPIselection
        self.top_Mkt = False
        self.top_Start = False
        self.list_alloc = []
        self.qty_fromorder = ''  # Quantity from grid
        self.exchange = ''  # Exchange from grid
        self.combobox_values = []  # useraccounts list
        self.bank_ = ''
        self.branch_ = ''
        self.deposit_ = ''
        self.customer_ = ''
        self.credentials = []  # user credentails

        btn_values = ['Connect', 'Disconnect', 'Fidlist', 'Change Password']
        x = 0.012
        self.btn_top = []
        for i in range(len(btn_values)):
            self.Button_top = tk.Button(top)
            self.Button_top.pack(side='left', anchor='nw', padx=12, pady=10, ipadx=15, ipady=2)
            self.Button_top.configure(activebackground="#ececec")
            self.Button_top.configure(activeforeground="#000000")
            self.Button_top.configure(background="black")
            self.Button_top.configure(disabledforeground="#a3a3a3")
            self.Button_top.configure(foreground="white")
            self.Button_top.configure(highlightbackground="#d9d9d9")
            self.Button_top.configure(highlightcolor="black")
            self.Button_top.configure(pady="0")
            self.Button_top.configure(text=btn_values[i])
            self.btn_top.append(self.Button_top)
            x += 0.088

        self.btn_top[0].configure(command=self.btnconnect)
        self.btn_top[1].bind('<ButtonRelease>', lambda event: sMain.disconnect(self))
        self.btn_top[2].configure(command=self.btnfidlist)
        self.btn_top[3].configure(command=self.btnchangePasswordSRP)

        self.Label_Ord = tk.Label(top)
        self.Label_Ord.pack(side='left', anchor='nw', padx=10, pady=10)
        self.Label_Ord.configure(background="#d9d9d9")
        self.Label_Ord.configure(disabledforeground="#a3a3a3")
        self.Label_Ord.configure(foreground="#000000")
        self.Label_Ord.configure(text='''List of APIs''')

        self.TCombobox2 = ttk.Combobox(top)
        self.TCombobox2.pack(side='left', anchor='nw', ipadx=60, pady=10)
        self.TCombobox2.configure(textvariable=combobox_Ord)
        self.TCombobox2.configure(takefocus="")
        self.TCombobox2.pack_propagate(0)
        self.TCombobox2.configure(
            values=['Subscribe to HeartBeats', 'Submit Single Order', 'Submit Pair Order', 'Submit Seed Data',
                    'Subscribe Order Info', 'Submit Basket Order', 'Submit Trade Report', 'Get User Accounts',
                    'Get Today\'s Balances',
                    'Get Today\'s Activity', 'Get Today\'s Activity Book', 'Get Today\'s NetPositions',
                    'Get Today\'s BrokenDownPositions', 'Get Symbols From Company Name',
                    'Get Symbol From SEDOL, ISIN, CUSIP, etc',
                    'Get User Strategies'])
        self.TCombobox2.bind("<<ComboboxSelected>>", self.orderentrygrid)
        self.TCombobox2['state'] = 'readonly'

        self.Label_acc = tk.Label(top)
        self.Label_acc.pack(side='left', anchor='nw', padx=10, pady=10)
        self.Label_acc.configure(background="#d9d9d9")
        self.Label_acc.configure(disabledforeground="#a3a3a3")
        self.Label_acc.configure(foreground="#000000")
        self.Label_acc.configure(text='''Accounts''')

        self.TCombobox1 = ttk.Combobox(top)
        self.TCombobox1.pack(side='left', anchor='nw', ipadx=60, pady=10)
        self.TCombobox1.configure(textvariable=combobox_Acc)
        self.TCombobox1.configure(takefocus="")
        self.TCombobox1.pack_propagate(0)
        self.TCombobox1.bind("<<ComboboxSelected>>", self.accountselection)

        # For Examples
        self.frame = VerticalScrolledFrame(top, width=500, borderwidth=2, relief=tk.RAISED, background="#d9d9d9")
        self.frame.place(relx=0.01, rely=0.0542, relheight=0.45, relwidth=0.44)
        self.frame.propagate(0)

        self.Fids = ['Symbol', 'Side', 'Quantity', 'Route', 'Staged', 'Claim Require', 'Trade Report Type', 'Ticket ID',
                     'Order Tag', 'Single Order Extended Fields',
                     'For ExtFields/OptFields Example: OPEN_CLOSE:OPEN;EXPIRATION:DAY']

        rows = 1
        lgt = len(self.Fids)

        for en_fid in self.Fids:  # FIDS_DICT
            self.fid_entry = tk.Entry(self.frame)
            self.fid_entry.insert('end', en_fid)
            self.fid_entry.grid(row=rows, column=0, sticky='nsew', padx=1, pady=1, ipadx=20)
            self.fid_entry.config(state="readonly")
            if rows == 11:
                self.fid_entry.grid(row=11, column=0, sticky='nsew', padx=1, pady=1, columnspan=6)
                self.fid_entry.config(font=('Helvetica', 9, 'bold'))
            self.fid_entry.grid_propagate(0)
            rows += 1

        for ln in range(lgt - 1):  # VALUES_ENTRY
            if ln == 6:
                self.TCombobox_trade = ttk.Combobox(self.frame, width=10)
                self.TCombobox_trade.grid(row=ln + 1, column=1, sticky='nsew', padx=1, pady=1)
                self.TCombobox_trade.configure(textvariable=combobox_trd)
                self.TCombobox_trade.configure(takefocus="")
                self.TCombobox_trade.configure(values=['UserSubmitTradeReport', 'ForeignExecution'])
                self.TCombobox_trade.current(0)
                self.TCombobox_trade.grid_propagate(0)
                self.TCombobox_trade['state'] = 'disabled'
                self.vars.append(self.TCombobox_trade)
            elif ln == 4 or ln == 5:
                self.TCombobox_tf = ttk.Combobox(self.frame, width=10)
                self.TCombobox_tf.grid(row=ln + 1, column=1, sticky='nsew', padx=1, pady=1)
                self.TCombobox_tf.configure(textvariable=combobox_stg)
                if ln == 5:
                    self.TCombobox_tf.configure(textvariable=combobox_claim)
                self.TCombobox_tf.configure(takefocus="")
                self.TCombobox_tf.configure(values=['TRUE', 'FALSE'])
                self.TCombobox_tf['state'] = 'readonly'
                self.TCombobox_tf.grid_propagate(0)
                self.vars.append(self.TCombobox_tf)
            elif ln == 9:
                self.ext_single = tk.Entry(self.frame, width=50)
                self.ext_single.grid(row=10, column=1, sticky='nsew', columnspan=4)
                self.ext_single.config(font=('Times new roman', 12))
                self.ext_single.grid_propagate(0)
                self.vars.append(self.ext_single)
            else:
                self.fid_value = tk.Entry(self.frame, width=10)
                self.fid_value.grid(row=ln + 1, column=1, sticky='nsew', padx=1, pady=1)
                self.fid_value.config(font=('Times new roman', 12))
                self.fid_value.grid_propagate(0)
                self.vars.append(self.fid_value)

        btn_list = ['Submit', 'Market Data', 'View Source Code']
        g = 0.08
        self.btn_UI = []
        for i in range(len(btn_list)):
            self.Button_main = tk.Button(top)
            self.Button_main.place(relx=0.458, rely=g, height=32, width=125)
            self.Button_main.configure(activebackground="#ececec")
            self.Button_main.configure(activeforeground="#000000")
            self.Button_main.configure(background="black")
            self.Button_main.configure(disabledforeground="#a3a3a3")
            self.Button_main.configure(foreground="white")
            self.Button_main.configure(highlightbackground="#d9d9d9")
            self.Button_main.configure(highlightcolor="black")
            self.Button_main.configure(pady="0")
            self.Button_main.configure(text=btn_list[i])
            self.btn_UI.append(self.Button_main)
            g += 0.066

        self.btn_UI[0].configure(command=self.btnsubmit)
        self.btn_UI[1].configure(command=self.btnmarket)
        self.btn_UI[2].configure(command=self.btnviewsource)

        # Marketdataframe
        self.mktFrame = tk.Frame(top, width=500, borderwidth=2, relief=tk.RAISED, background="black")
        self.mktFrame.place(relx=0.561, rely=0.053, relheight=0.44, relwidth=0.43)

        self.mktLabel = tk.Label(self.mktFrame, text="MARKET DATA", bg="green", fg="white")
        self.mktLabel.pack(side='top')

        self.lstbx_mkt = VerticalScrolledFrame(self.mktFrame, width=900, relief=tk.SUNKEN, background="black")
        self.lstbx_mkt.pack(side='top', ipady=70, ipadx=20)
        ##################

        self.TPanedwindow1 = ttk.Panedwindow(top, orient="horizontal")
        self.TPanedwindow1.place(relx=0.009, rely=0.51, relheight=0.48, relwidth=0.98)
        self.TPanedwindow1_p1 = ttk.Labelframe(width=800, text='Order Blotter')
        self.TPanedwindow1.add(self.TPanedwindow1_p1)
        self.TPanedwindow1_p2 = ttk.Labelframe(text='API Response')
        self.TPanedwindow1.add(self.TPanedwindow1_p2)
        self.__funcwid = self.TPanedwindow1.bind('<Map>', self.__adjust_wind)

        if sMain.establishserverconnection(self):
            self.orderblotter_grid()  # DatagridofOrderblotter


class VerticalScrolledFrame:
    """
    A vertically scrolled Frame that can be treated like any other Frame
    ie it needs a master and layout and it can be a master.
    :width:, :height:, :bg: are passed to the underlying Canvas
    :bg: and all other keyword arguments are passed to the inner Frame
    note that a widget layed out in this frame will have a self.master 3 layers deep,
    (outer Frame, Canvas, inner Frame) so 
    if you subclass this there is no built in way for the children to access it.
    You need to provide the controller separately.
    """

    def __init__(self, master, **kwargs):
        width = kwargs.pop('width', None)
        height = kwargs.pop('height', None)
        bg = kwargs.pop('bg', kwargs.pop('background', None))
        self.outer = tk.Frame(master, **kwargs)

        self.vsb = tk.Scrollbar(self.outer, orient=tk.VERTICAL)
        self.vsb.pack(fill=tk.Y, side=tk.RIGHT)
        self.canvas = tk.Canvas(self.outer, highlightthickness=0, width=width, height=height, bg=bg)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas['yscrollcommand'] = self.vsb.set
        # mouse scroll does not seem to work with just "bind"; You have
        # to use "bind_all". Therefore to use multiple windows you have
        # to bind_all in the current widget
        self.canvas.bind("<Enter>", self._bind_mouse)
        self.canvas.bind("<Leave>", self._unbind_mouse)
        self.vsb['command'] = self.canvas.yview

        self.inner = tk.Frame(self.canvas, bg=bg)
        # pack the inner Frame into the Canvas with the topleft corner 4 pixels offset
        self.canvas.create_window(4, 4, window=self.inner, anchor='nw')
        self.inner.bind("<Configure>", self._on_frame_configure)

        self.outer_attr = set(dir(tk.Widget))

    def __getattr__(self, item):
        if item in self.outer_attr:
            # geometry attributes etc (eg pack, destroy, tkraise) are passed on to self.outer
            return getattr(self.outer, item)
        else:
            # all other attributes (_w, children, etc) are passed to self.inner
            return getattr(self.inner, item)

    def _on_frame_configure(self, event=None):
        x1, y1, x2, y2 = self.canvas.bbox("all")
        height = self.canvas.winfo_height()
        self.canvas.config(scrollregion=(0, 0, x2, max(y2, height)))

    def _bind_mouse(self, event=None):
        self.canvas.bind_all("<4>", self._on_mousewheel)
        self.canvas.bind_all("<5>", self._on_mousewheel)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mouse(self, event=None):
        self.canvas.unbind_all("<4>")
        self.canvas.unbind_all("<5>")
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        """Linux uses event.num; Windows / Mac uses event.delta"""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")


def sort_column(tree, col, descending):
    '''Function shows the sort tree contents when a column header is clicked on'''
    # grab values to sort
    data = [(tree.set(child, col), child) \
            for child in tree.get_children('')]
    # if the data to be sorted is numeric change to float
    # data =  change_numeric(data)
    # now sort the data in place
    data.sort(reverse=descending)
    for ix, item in enumerate(data):
        tree.move(item[1], '', ix)
    # switch the heading so it will sort in the opposite direction
    tree.heading(col, command=lambda col=col: sort_column(tree, col, \
                                                          int(not descending)))


def bDown_Shift(event):
    ''' Event to handle sorting the columns'''
    tv = event.widget
    select = [tv.index(s) for s in tv.selection()]
    select.append(tv.index(tv.identify_row(event.y)))
    select.sort()
    for i in range(select[0], select[-1] + 1, 1):
        tv.selection_add(tv.get_children()[i])


def bDown(event):
    ''' Event to handle sorting the columns'''
    tv = event.widget
    if tv.identify_row(event.y) not in tv.selection():
        tv.selection_set(tv.identify_row(event.y))


def bUp(event):
    ''' Event to handle sorting the columns'''
    tv = event.widget
    if tv.identify_row(event.y) in tv.selection():
        tv.selection_set(tv.identify_row(event.y))


def bMove(event):
    ''' Event to handle sorting the columns'''
    tv = event.widget
    moveto = tv.index(tv.identify_row(event.y))
    for s in tv.selection():
        tv.move(s, '', moveto)


def list_to_dict(rlist):
    '''Converting list to dict'''
    return OrderedDict(map(lambda s: s.split(':'), rlist))


def str_to_bool(s):
    '''To handle bool for staged/claimreq'''
    if s == 'TRUE':
        return True
    elif s == 'FALSE':
        return False
    elif s == '':
        return False
    else:
        raise ValueError


def set_Tk_var():
    '''Setting value for each variable on GUI'''
    global combobox_Acc
    combobox_Acc = tk.StringVar()
    global combobox_Ord
    combobox_Ord = tk.StringVar()

    global combobox_trd
    combobox_trd = tk.StringVar()

    global Username_var
    Username_var = tk.StringVar()
    Username_var.set('USERNAME_START')

    global che51_mkt
    che51_mkt = tk.BooleanVar()
    global che52_mkt
    che52_mkt = tk.BooleanVar()
    global che53_mkt
    che53_mkt = tk.BooleanVar()

    global combobox_mkt
    combobox_mkt = tk.StringVar()
    global combobox_sym
    combobox_sym = tk.StringVar()
    global combobox_acctalloc
    combobox_acctalloc = tk.StringVar()
    global combobox_typealloc
    combobox_typealloc = tk.StringVar()
    global combobox_claim
    combobox_claim = tk.StringVar()
    global combobox_stg
    combobox_stg = tk.StringVar()
    global combobox_req
    combobox_req = tk.StringVar()
    global combobox_adv
    combobox_adv = tk.StringVar()
    global combobox_level
    combobox_level = tk.StringVar()


def init(top, gui, *args, **kwargs):
    global w, top_level, root
    w = gui
    top_level = top
    root = top


def close_windows(master):
    # Function which closes sub window.
    master.destroy()
