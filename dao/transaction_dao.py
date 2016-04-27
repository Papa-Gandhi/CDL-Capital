#!/usr/bin/python

import sys, LINK_HEADERS,datetime
from decimal import *
sys.path.insert(0, str(LINK_HEADERS.DATABASE_LINK))
sys.path.insert(0, str(LINK_HEADERS.MODELS_LINK))
from database_class import DB
from transaction_model import Transaction
from owned_stock_model import Owned_stock
from user_stock_value_model import User_stock_value
from date_transaction_model import Date_transaction
from PDO import PDO

class Transaction_dao:

     db = None

     def __init__(self):
          self.db =  PDO().get_connection(LINK_HEADERS.DB_HOST, LINK_HEADERS.DB_USER, LINK_HEADERS.DB_PASSWORD, LINK_HEADERS.DB_NAME)

     def select(self):
          result = self.db.query("select * from transactions;")
          if result:
               l = []
               for i in range(len(result)):
                    t = Transaction(result[i]['user'],result[i]['trans_date'],result[i]['stock'],result[i]['price'],result[i]['sold'],result[i]['order_id'],result[i]['profit'],result[i]['algo_id'])
                    l.append(t)
               return l

     def update_profit(self, user, trans_date, order_id, profit, stock, algo_id):
          self.db.query("update transactions set profit=('%s') where user=('%s') and trans_date=('%s') and order_id=('%s') and stock=('%s') and algo_id=('%s')"%(round(Decimal(profit), 2), user, trans_date, order_id, stock, algo_id)+";")
          
     def select_all(self, user):
          result = self.db.query("select * from transactions where user=('%s')"%(user)+";")
          if result:
               l = []
               for i in range(len(result)):
                    t = Transaction(result[i]['user'],result[i]['trans_date'],result[i]['stock'],result[i]['price'],result[i]['sold'],result[i]['order_id'],result[i]['profit'],result[i]['algo_id'])
                    l.append(t)
               l.sort(key=lambda x: x.get_trans_date(), reverse=False)
               return l

     def select_all_active(self, user):
          result = self.db.query("select * from transactions where user=('%s') and sold='0'"%(user)+";")
          if result:
               l = []
               for i in range(len(result)):
                    t = Transaction(result[i]['user'],result[i]['trans_date'],result[i]['stock'],result[i]['price'],result[i]['sold'],result[i]['order_id'],result[i]['profit'],result[i]['algo_id'])
                    l.append(t)
               l.sort(key=lambda x: x.get_trans_date(), reverse=False)
               return l

     def select_all_sold(self, user):
          result = self.db.query("select * from transactions where user=('%s') and sold='1'"%(user)+";")
          if result:
               l = []
               for i in range(len(result)):
                    t = Transaction(result[i]['user'],result[i]['trans_date'],result[i]['stock'],result[i]['price'],result[i]['sold'],result[i]['order_id'],result[i]['profit'],result[i]['algo_id'])
                    l.append(t)
               l.sort(key=lambda x: x.get_trans_date(), reverse=False)
               return l

     def buy(self,user, stock, volume, price, algo_id):
          for i in range(volume):
               self.db.query("insert into transactions (user, stock, price, sold, order_id, profit, algo_id) values ('%s','%s',%f,'%s',%d,%f,'%s')"%(user, stock, round(Decimal(price), 2), 0, int(i), Decimal(0), algo_id)+";")

     def sell(self, user, stock, volume, price, algo_id):
          result = self.db.query("select * from transactions where user=('%s') and stock=('%s') and sold='0'"%(user, stock)+" ORDER BY trans_date ASC, order_id ASC LIMIT "+str(volume)+";")
          time = datetime.datetime.utcnow()
          if result:
               if len(result) >= volume:
                    for i in range(len(result)):
                         profit = Decimal(price) - Decimal(result[i]['price'])
                         self.db.query("update transactions set sold='1', profit=('%s'), trans_date=('%s') where user=('%s') and stock=('%s') and trans_date=('%s') and order_id=(%d) and algo_id=('%s')"%(round(Decimal(profit),2), str(time), user, stock, result[i]['trans_date'], result[i]['order_id'], algo_id)+";")

     def get_user_stock_list(self, user):
          result = self.db.query("select distinct stock from transactions where user=('%s') and sold='0'"%(user)+";")
          if result:
              l=[]
              for i in range(len(result)):
                   l.append(result[i]['stock'])
              return l

     def get_all_algo_stock_list(self, user):
          result = self.db.query("select distinct stock from transactions where user=('%s') and sold='0' and algo_id != '0'"%(user)+";")
          if result:
              l=[]
              for i in range(len(result)):
                   l.append(result[i]['stock'])
              return l

     def get_only_user_stock_list(self, user):
          result = self.db.query("select distinct stock from transactions where user=('%s') and sold='0' and algo_id = '0'"%(user)+";")
          if result:
              l=[]
              for i in range(len(result)):
                   l.append(result[i]['stock'])
              return l

     def get_algo_stock_list(self, user, algo_id):
          result = self.db.query("select distinct stock from transactions where user=('%s') and sold='0' and algo_id = ('%s')"%(user, algo_id)+";")
          if result:
              l=[]
              for i in range(len(result)):
                   l.append(result[i]['stock'])
              return l
         
     #def get_user_owned_stocks_list(self, user):
     #     result=self.db.query("select distinct stock from transactions where user=('%s') and sold='0'"%(user) + ";")
     #     if result:
     #         l=[]
     #         for i in range(len(result)):
     #             l.append(result[i]['stock'])
     #         return l

     def get_owned_stock_model(self, user, stock, price):
          volume_result= self.db.query("select count(*),sum(profit) from transactions where user=('%s') and stock=('%s') and sold='0'"%(user, stock)+";")
          profit_result = volume_result
          
          if volume_result and profit_result:
               volume = int(volume_result[0]['count(*)'])
               #Check for decimal operation failure
	       try:
                   total_worth = int(volume) * Decimal(price)
	       except InvalidOperation:
		   total_worth = 0
               if profit_result[0]['sum(profit)'] != None:
                    profit = Decimal(profit_result[0]['sum(profit)'])
               else:
                    profit = 0
               o = Owned_stock(stock, volume, price, total_worth, profit)
               return o



     def get_owned_stock_volume_per_algorithm(self, user, algo_id):
         volume_result=self.db.query("select stock, count(*) as volume from transactions where user = ('%s') and sold = '0' and algo_id=('%s') group by stock"%(user,algo_id)+";") 
         if volume_result:
             l=[]
             for i in range(len(volume_result)):
                 o = Owned_stock(volume_result[i]['stock'], volume_result[i]['volume'], None, None, None)
                 l.append(o)
             return l   
          
     def get_profit_per_algorithm(self, user):
          profit_result = self.db.query("select sum(profit) as profit from transactions where user = ('%s') and sold = '1' group by algo_id"%(user) + ";")
          if profit_result:
              l=[]
              for i in range(len(profit_result)):
                  o = Owned_stock(None, None, None, None, profit_result[i]['profit'])
                  l.append(o)
              return l

    # def get_algorithm_stock_value_model(self, user):
         # result1=self.db.query("select sum(profit) as profit from transactions where user=('%s') and sold = '1' group by algo_id"%(user) + ";")  
         # if result1:
         #      l=[]
         #      for i in range(len(result)):
         #           l.append(result[i]['profit'])
         #      return l


     def get_user_stock_value_model(self, user):
          result1 = self.db.query("select sum(profit) from transactions where user=('%s') and sold='1'"%(user)+";")
          result2 = self.db.query("select sum(price) from transactions where user=('%s') and sold='0'"%(user)+";")
          if result1[0]['sum(profit)'] != None:
               profit = Decimal(result1[0]['sum(profit)'])
          else:
               profit = 0
               
          if result2[0]['sum(price)'] != None:
               total_stock_values =  Decimal(result2[0]['sum(price)'])
          else:
               total_stock_values = 0
               
          u = User_stock_value(user, profit, total_stock_values)
          return u

     def get_trades_per_day(self,user):
          result = self.db.query("select DATE(trans_date) as date, count(id) as num_trades from transactions where user=('%s') group by DATE(trans_date)"%(user)+";");
          if result:
               l = []
               for i in range(len(result)):
                    t = Date_transaction()
                    t.set_date(result[i]['date'])
                    t.set_num_trades(result[i]['num_trades'])
                    l.append(t)
               return l
          else:
               return False

     def select_all_profit_per_day(self, user):
          result = self.db.query("select UNIX_TIMESTAMP(DATE(trans_date))*1000 as date, sum(profit) as profit from transactions where user=('%s') and sold='1' group by DATE(trans_date)"%(user)+";");
        
          if result:
               l = []
               for i in range(len(result)):
                    t = Date_transaction()
                    t.set_date(result[i]['date'])
                    t.set_profit(result[i]['profit'])
                    l.append(t)
               return l
          else:
               return False

     def select_user_profit_per_day(self, user):
          result = self.db.query("select UNIX_TIMESTAMP(DATE(trans_date))*1000 as date, sum(profit) as profit from transactions where user=('%s') and sold='1' and algo_id='0' group by DATE(trans_date)"%(user)+";");

          if result:
               l = []
               for i in range(len(result)):
                    t = Date_transaction()
                    t.set_date(result[i]['date'])
                    t.set_profit(result[i]['profit'])
                    l.append(t)
               return l
          else:
               return False
     
     def select_all_algorithms_profit_per_day(self, user):
          result = self.db.query("select UNIX_TIMESTAMP(DATE(trans_date))*1000 as date, sum(profit) as profit from transactions where user=('%s') and sold='1' and algo_id!='0' group by DATE(trans_date)"%(user)+";");

          if result:
               l = []
               for i in range(len(result)):
                    t = Date_transaction()
                    t.set_date(result[i]['date'])
                    t.set_profit(result[i]['profit'])
                    l.append(t)
               return l
          else:
               return False

     def select_algorithm_profit_per_day(self, user, algo_id):
          result = self.db.query("select UNIX_TIMESTAMP(DATE(trans_date))*1000 as date, sum(profit) as profit from transactions where user=('%s') and sold='1' and algo_id=('%s') group by DATE(trans_date)"%(user, algo_id)+";");

          if result:
               l = []
               for i in range(len(result)):
                    t = Date_transaction()
                    t.set_date(result[i]['date'])
                    t.set_profit(result[i]['profit'])
                    l.append(t)
               return l
          else:
               return False




#t = Transaction_dao()
#test =  t.select_all_profit_per_day("al356")
#print test[4].get_profit()
