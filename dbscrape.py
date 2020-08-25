# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 15:53:07 2020

@author: Akil
"""
import psycopg2
import pandas as pd
import sys

def getdata(host,database,username,password,tablename,startdt,enddt):
    
    param_dic = {
        "host"      : host,
        "database"  : database,
        "user"      : username,
        "password"  : password
    }
    startdt = '\'' + str(startdt) + '\''
    enddt = '\'' + str(enddt) + '\''
    
    def connect(params_dic):
        """ Connect to the PostgreSQL database server """
        conn = None
        try:
            conn = psycopg2.connect(**params_dic)
        except (Exception, psycopg2.DatabaseError):
            sys.exit(1) 
        return conn
    

    
    def postgresql_to_dataframe(conn, select_query, column_names):
                
        cursor = conn.cursor()
        try:
            cursor.execute(select_query)
        except (Exception, psycopg2.DatabaseError):
            cursor.close()
            return 1
        
        tupples = cursor.fetchall()
        cursor.close()
        
        df = pd.DataFrame(tupples, columns=column_names)
        return df
    
    
    # Connect to the database
    conn = connect(param_dic)
    
    column_names = ["datetime","internaltime","open","high","low","close","volume","unknown","expirydate","exchange"]
    df = postgresql_to_dataframe(conn, "SELECT * FROM public."+tablename+" WHERE datetime BETWEEN "+startdt+" and "+enddt, column_names)
    return df


    
