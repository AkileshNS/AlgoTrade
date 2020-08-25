# postgre2df

This repository can be used to scrape data from a Postgresql Table to a Pandas DataFrame.

Functions:
   1)gettable: This function retrieves the entire table.
   Function Parameters: gettable(host-url,database-name,username,password,tablename)
    
   2)gettablerange: This function retrieves the table within the user specified time stamp.
   Function Parameters: gettable(host-url,database-name,username,password,table-name,start-date_time,end-date_time)
   
   Note: date_time format follows the : "YYYY-MM-DD HH:MM:SS" format 
