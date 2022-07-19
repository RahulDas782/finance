# finance

## About
Finance, a web app via which you can manage portfolios of stocks. Not only will this tool allow you to check real time stocks actual prices and portfolios values, it will also let you buy and sell stocks by querying [IEX](https://iexcloud.io/) API for stocks’ prices. Also you can add money to your account.
Tech stack - **Python, Flask, HTML, CSS, Bootstrap, sqlite3.**

## Functionality

#### All the amounts are in dollar($).

### ```/quote```
  - You can check the current stock price of the stock by entering the stock's symbol.
  - Example: NFLX(netflix), META(facebook), AMZN(amazon).
  
### ```/buy```
  - You can buy any stock by entering the stock's symbol and the number of shares you wana buy.
  - Example: NFLX(netflix) and 3 shares.
  
### ```/sell```
  - You can sell stock by selecting the stock's symbol from the dropdown and the number of shares you wana sell.
  - Example: AMZN(amazon) and 3 shares.
  
### ```/history```
  - It will show you all the transactions(buy and sell) you had done in the past.
  
### ```/add_cash```
  - You can add money to your account as much you want :-)>
  

## Installation and Run
- Firstly clone the project!
- Enter ```pip install -r requirements.txt``` in terminal.
- Enter ```flask run``` in terminal.
- Open the localhost url shown in terminal and you are ready to go ;-)
