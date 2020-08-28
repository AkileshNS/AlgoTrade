# postgre2df

This repository can be used to scrape data from a Postgresql Table to a Pandas DataFrame.

Functions:

1)gettable: This function retrieves the entire table.
Function Parameters:
gettable(host-url,database-name,username,password,tablename)
    
2)gettablerange: This function retrieves the table within the user specified time stamp.
Function Parameters:
gettablerange(host-url,database-name,username,password,table-name,start-date_time,end-date_time)
   
3)expirymonth: This function retrieves the table for the expiry month and year set by the user.
Function Parameters:
expirymonth(host-url,database-name,username,password,table-name,month,year)


Note: Ensure to prefix single digit month's by a 0. Example: August - 08.
Note: date_time format follows the : "YYYY-MM-DD HH:MM:SS" format 
