import ccxt, config
import pandas as pd
from ta.trend import EMAIndicator
import winsound
from smtplib import SMTP

duration = 1000  # milliseconds
freq = 440  # Hz

symbolName = input("Sembol adı girin (BTC, ETH, LTC...vb): ")
leverage = input ("Kaldıraç büyüklüğü: ")
zamanAraligi = input("Zaman aralığı (1m,3m,5m,15m,30m,45m,1h,2h,4h,6h,8h,12h,1d): ")
symbol = str(symbolName) + "/USDT"
slowEMAValue = input ("Yavaş Ema: ")
fastEMAValue = input ("Hızlı Ema: ")
alinacak_miktar = 0

kesisim = False
longPozisyonda = False
shortPozisyonda = False
pozisyondami = False

# API CONNECT
exchange = ccxt.binance({
"apiKey": config.apiKey,
"secret": config.secretKey,

'options': {
'defaultType': 'future'
},
'enableRateLimit': True
})

while True:
    try:
        
        balance = exchange.fetch_balance()
        free_balance = exchange.fetch_free_balance()
        positions = balance['info']['positions']
        newSymbol = symbolName+"USDT"
        current_positions = [position for position in positions if float(position['positionAmt']) != 0 and position['symbol'] == newSymbol]
        position_bilgi = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
        
        #Pozisyonda olup olmadığını kontrol etme
        if not position_bilgi.empty and position_bilgi["positionAmt"][len(position_bilgi.index) - 1] != 0:
            pozisyondami = True
        else: 
            pozisyondami = False
            shortPozisyonda = False
            longPozisyonda = False
        
        # Long pozisyonda mı?
        if pozisyondami and float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) > 0:
            longPozisyonda = True
            shortPozisyonda = False
        # Short pozisyonda mı?
        if pozisyondamiand float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) < 0:
            shortPozisyonda = True
            longPozisyonda = False
        
        
        # LOAD BARS
        bars = exchange.fetch_ohlcv(symbol, timeframe=zamanAraligi, since = None, limit = 1500)
        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])

        # LOAD SLOW EMA
        slowEma= EMAIndicator(df["close"], float(slowEMAValue))
        df["Slow Ema"] = slowEma.ema_indicator()
        
        # LOAD FAST EMA
        FastEma= EMAIndicator(df["close"], float(fastEMAValue))
        df["Fast Ema"] = FastEma.ema_indicator()
        
        if (df["Fast Ema"][len(df.index)-3] < df["Slow Ema"][len(df.index)-3] and df["Fast Ema"][len(df.index)-2] > df["Slow Ema"][len(df.index)-2]) or (df["Fast Ema"][len(df.index)-3] > df["Slow Ema"][len(df.index)-3] and df["Fast Ema"][len(df.index)-2] < df["Slow Ema"][len(df.index)-2]):
            kesisim = True
        else: 
            kesisim = False
            
        # LONG ENTER
        def longEnter(alinacak_miktar):
            order = exchange.create_market_buy_order(symbol, alinacak_miktar)
            winsound.Beep(freq, duration)
            
        # LONG EXIT
        def longExit():
            order = exchange.create_market_sell_order(symbol, float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]), {"reduceOnly": True})
            winsound.Beep(freq, duration)

        # SHORT ENTER
        def shortEnter(alincak_miktar):
            order = exchange.create_market_sell_order(symbol, alincak_miktar)
            winsound.Beep(freq, duration)
            
        # SHORT EXIT
        def shortExit():
            order = exchange.create_market_buy_order(symbol, (float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) * -1), {"reduceOnly": True})
            winsound.Beep(freq, duration)
        
        # BULL EVENT
        if kesisim and df["Fast Ema"][len(df.index)-2] > df["Slow Ema"][len(df.index)-2] and longPozisyonda == False:
            if shortPozisyonda:
                print("SHORT İŞLEMDEN ÇIKILIYOR...")
                shortExit()
            alinacak_miktar = (((float(free_balance["USDT"]) / 100 ) * 100) * float(leverage)) / float(df["close"][len(df.index) - 1])
            print("LONG İŞLEME GİRİLİYOR...")
            longEnter(alinacak_miktar)
            baslik = symbol
            message = "LONG ENTER\n" + "Toplam Para: " + str(balance['total']["USDT"])
            content = f"Subject: {baslik}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))

        
        # BEAR EVENT
        if kesisim and df["Fast Ema"][len(df.index)-2] < df["Slow Ema"][len(df.index)-2] and shortPozisyonda == False:
            if longPozisyonda:
                print("LONG İŞLEMDEN ÇIKILIYOR...")
                longExit()
            alinacak_miktar = (((float(free_balance["USDT"]) / 100 ) * 100) * float(leverage)) / float(df["close"][len(df.index) - 1])
            print ("SHORT İŞLEME GİRİLİYOR...")
            shortEnter(alinacak_miktar)
            baslik = symbol
            message = "SHORT ENTER\n" + "Toplam Para: " + str(balance['total']["USDT"])
            content = f"Subject: {baslik}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))
 
        if pozisyondami == False:
            print("POZİSYON ARANIYOR...")

        if shortPozisyonda:
            print("SHORT POZİSYONDA BEKLİYOR")
        if longPozisyonda:
            print("LONG POZİSYONDA BEKLİYOR")
        
    except ccxt.BaseError as Error:
        print ("[ERROR] ", Error )
        continue
