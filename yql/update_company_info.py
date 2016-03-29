#!/usr/bin/python
from datetime import datetime
import sys,simplejson,re,time,LINK_HEADERS, update
from yahoo_finance_class import YQLQuery
sys.path.insert(0, str(LINK_HEADERS.DATABASE_LINK))
from database_class import DB
sys.path.insert(0, str(LINK_HEADERS.ALGORITHMS_LINK))
import algorithm

###global variables
column_query_result= None
column_names = None
num_columns = None
###Sanitizes result of db query to retrieve ticker symbols from database and puts into list 
## @param result=all sticker symbols from db
def create_result_list(result):
    l=[]
    for i in range(len(result)):
        if "^" in result[i]['symbol'] or "." in result[i]['symbol']:
            continue
        else:
            l.append(result[i]['symbol'].replace(" ",""))
    return l

###converts ticker list into a string and executes yql query at intervals of 100 
## @param l = list of ticker symbols
## @param yql = YQLQuery object 
def request_yql(l,yql,db):
    START_YQL = "select " + column_names +  " from yahoo.finance.quotes where symbol in ('"
    END_YQL = "');"    
    result_string=""
    final=0
    counter=0
    for i in range(len(l)):
        result_string += l[i]
        counter+=1
        final+=1

	if counter==40 or final == len(l):
	    yql_query=START_YQL + result_string + END_YQL
            while True:
                yql_result=yql.execute(yql_query)
                if "query" in yql_result.keys():
		    break
                else:
                    time.sleep(1)
                    
            isGood=update_company_info(yql_result,db)
            result_string=""
	    counter=0
        else:
            result_string += ","
       
###updates company information in database
## @param yql_result = yql query result with stock data for all stock symbols in database 
## @param db = db object
def update_company_info(yql_result,db):
 #   db_file = open('db_update_log','w')
    START_SQL="INSERT INTO company_info(" + column_names + ")" + "VALUES"
    END_SQL= ""
    VALUES_LIST=[]
    for x in range(int(yql_result['query']['count'])):
	values=[]
        for key, value in yql_result['query']['results']['quote'][x].iteritems():
            if key == "Change" or key == "symbol":
                continue
#            if key == "Ask" and (value == "None" or value == "null"):
#               value = '0'
            value=str(value).replace("'","\\'")
	    values.append(value)
        values=tuple(values)
	VALUES_LIST.append(values)
    VALUES_LIST=str(VALUES_LIST).strip("[]")
    for x in range(num_columns):
        END_SQL+= str(column_query_result[x]) + "=VALUES(" + str(column_query_result[x]) + "),"        
    END_SQL=END_SQL[:-1] + ";"
    		
    SQL_QUERY=START_SQL + VALUES_LIST + " ON DUPLICATE KEY UPDATE " + END_SQL
    try:
        db.query(SQL_QUERY)
    except Exception, e :
        error_log = open('/usr/lib/cgi-bin/kchang_cdlcapital/logs/update_company_log.txt','a')
        error_log.write(str(e))
        print str(e) 
        error_log.close()
def main(): 
    global column_query_result, num_columns, column_names
    db = DB("localhost","root","mmGr2016","cdlcapital")
    result = db.get_stock_symbols()
    l = create_result_list(result)
    column_query_result=db.get_column_names()
    num_columns=len(column_query_result)
    column_names=str(column_query_result).strip("[]")
    column_names=column_names.replace("'","")
    
    opening_time = "13:30:00"
    closing_time = "20:00:00"
    while True:
        current_time = datetime.utcnow().strftime("%H:%M:%S")
        start=time.time()
        if current_time > opening_time and current_time < closing_time:
            yql= YQLQuery()
            print "request: " + str(current_time)
            request_yql(l,yql,db)
            update.main()
            algorithm.main()
            runtime=time.time()-start
            if runtime < 252:
                sleeptime=252 - runtime
                time.sleep(sleeptime)
        else:
            exit()

if __name__ == "__main__":        
    main()
