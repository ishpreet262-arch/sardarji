from flask import Flask, render_template, request, redirect, session
import sqlite3
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import feedparser

app = Flask(__name__)
app.secret_key = "ai_project_secret"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT)""")
    conn.commit()
    conn.close()

init_db()

# ---------- TOP GAINERS LOSERS ----------
def get_market_movers():
    stocks=["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ITC.NS",
            "SBIN.NS","LT.NS","WIPRO.NS","TATAMOTORS.NS","BHARTIARTL.NS","KOTBANK.NS","BAJFINANCE.NS","BAJAFINSV.NS","HCLTECH.NS","TECHM.NS","^NSEI","^NSEBANK"]

    data=[]
    for s in stocks:
        try:
            df=yf.Ticker(s).history(period="2d")
            if len(df)>=2:
                prev=df['Close'].iloc[-2]
                last=df['Close'].iloc[-1]
                change=((last-prev)/prev)*100
                data.append((s.replace(".NS",""),round(change,2)))
        except:
            pass

    gainers=sorted(data,key=lambda x:x[1],reverse=True)[:5]
    losers=sorted(data,key=lambda x:x[1])[:5]
    return gainers,losers

# ---------- NIFTY ----------
def get_nifty():
    try:
        df=yf.Ticker("^NSEI").history(period="1d")
        if not df.empty:
            return round(float(df['Close'].iloc[-1]),2)
    except: pass
    return "Closed"

# ---------- WORLD MARKET ----------
def get_world_market():
    data={}
    try:
        data["dow"]=round(float(yf.Ticker("^DJI").history(period="1d")['Close'].iloc[-1]),2)
    except: data["dow"]="NA"
    try:
        data["nasdaq"]=round(float(yf.Ticker("^IXIC").history(period="1d")['Close'].iloc[-1]),2)
    except: data["nasdaq"]="NA"
    try:
        data["btc"]=round(float(yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]),2)
    except: data["btc"]="NA"
    try:
        data["gold"]=round(float(yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]),2)
    except: data["gold"]="NA"
    return data

# ---------- LIVE TICKER ----------
def get_live_ticker():
    symbols={"NIFTY":"^NSEI","RELIANCE":"RELIANCE.NS","TCS":"TCS.NS","AAPL":"AAPL","BTC":"BTC-USD"}
    out=[]
    for n,s in symbols.items():
        try:
            price=round(float(yf.Ticker(s).history(period="1d")['Close'].iloc[-1]),2)
            out.append(f"{n}:{price}")
        except: pass
    return " | ".join(out)

# ---------- AI SIGNAL ----------
def get_ai_signals():
    watch=["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ITC.NS", "SBIN.NS","LT.NS","WIPRO.NS","TATAMOTORS.NS","BHARTIARTL.NS","KOTBANK.NS","BAJFINANCE.NS","BAJAFINSV.NS","HCLTECH.NS","TECHM.NS","^NSEI","^NSEBANK"]
    buy=""
    sell=""

    for s in watch:
        try:
            df=yf.Ticker(s).history(period="1mo")
            if df.empty: continue
            last=df['Close'].iloc[-1]
            avg=df['Close'].mean()
            name=s.replace(".NS","")

            if last>avg and buy=="":
                buy=name
            if last<avg and sell=="":
                sell=name
        except: pass

    crypto="BTC"
    try:
        df=yf.Ticker("BTC-USD").history(period="1mo")
        if df['Close'].iloc[-1]>df['Close'].mean():
            crypto="BTC 🚀"
        else:
            crypto="ETH"
    except: pass

    return buy,sell,crypto

# ---------- PRO NEWS ----------
def get_market_news():
    news={"india":[],"nifty":[],"global":[],"crypto":[]}

    try:
        feed=feedparser.parse("https://www.moneycontrol.com/rss/business.xml")
        for e in feed.entries[:5]:
            news["india"].append({"title":e.title,"link":e.link})
    except:
        news["india"].append({"title":"India news unavailable","link":"#"})

    try:
        feed=feedparser.parse("https://www.moneycontrol.com/rss/marketreports.xml")
        for e in feed.entries[:5]:
            news["nifty"].append({"title":e.title,"link":e.link})
    except:
        news["nifty"].append({"title":"Nifty news unavailable","link":"#"})

    try:
        feed=feedparser.parse("https://finance.yahoo.com/rss/")
        for e in feed.entries[:5]:
            news["global"].append({"title":e.title,"link":e.link})
    except:
        news["global"].append({"title":"Global news unavailable","link":"#"})

    try:
        feed=feedparser.parse("https://feeds.feedburner.com/CoinDesk")
        for e in feed.entries[:5]:
            news["crypto"].append({"title":e.title,"link":e.link})
    except:
        news["crypto"].append({"title":"Crypto news unavailable","link":"#"})

    return news

# ---------- LOGIN ----------
@app.route('/')
def login():
    return render_template("login.html")

# ---------- SIGNUP ----------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=="POST":
        u=request.form['username']
        e=request.form['email']
        p=request.form['password']
        conn=sqlite3.connect("database.db")
        cur=conn.cursor()
        cur.execute("INSERT INTO users(username,email,password) VALUES(?,?,?)",(u,e,p))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template("signup.html")

# ---------- LOGIN CHECK ----------
@app.route('/home', methods=['POST'])
def home():
    email=request.form['email']
    password=request.form['password']

    conn=sqlite3.connect("database.db")
    cur=conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?",(email,password))
    user=cur.fetchone()
    conn.close()

    if user:
        session['user']=user[1]
        return redirect('/dashboard')
    return "Login Failed"

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    gainers,losers=get_market_movers()
    nifty=get_nifty()
    world=get_world_market()
    ticker=get_live_ticker()
    buy,sell,crypto=get_ai_signals()
    news=get_market_news()

    return render_template("dashboard.html",
        user=session['user'],gainers=gainers,losers=losers,
        nifty=nifty,world=world,ticker=ticker,
        buy=buy,sell=sell,crypto=crypto,news=news)

# ---------- PREDICTION SAFE VERSION ----------
@app.route('/predict', methods=['POST'])
def predict():
    if 'user' not in session:
        return redirect('/')

    stock=request.form['stock'].upper().strip()

    try:
        symbol=stock
        currency="₹"

        # crypto
        if stock in ["BTC","BITCOIN"]:
            symbol="BTC-USD"
            currency="$"
        elif stock in ["ETH","ETHEREUM"]:
            symbol="ETH-USD"
            currency="$"
        else:
            symbol=stock+".NS"

        df=yf.Ticker(symbol).history(period="3mo")

        # if NSE fail try US
        if df.empty:
            symbol=stock
            df=yf.Ticker(symbol).history(period="3mo")
            currency="$"

        if df.empty:
            return "Stock not found or market closed. Try RELIANCE, TCS, HCLTECH"

        last=float(df['Close'].iloc[-1])
        avg=float(df['Close'].mean())
        pred=(last+avg)/2

        if not os.path.exists("static"):
            os.makedirs("static")

        plt.figure(figsize=(6,3))
        plt.plot(df['Close'])
        plt.title(symbol)
        plt.tight_layout()
        plt.savefig("static/graph.png")
        plt.close()

        signal="BUY 📈" if pred>last else "SELL 📉"

        return render_template("result.html",
            stock=symbol,
            price=round(last,2),
            prediction=round(pred,2),
            signal=signal,
            currency=currency)

    except Exception as e:
        return f"Error: {str(e)}"

# ---------- AI ASSISTANT FINAL WITH INDEX SUPPORT ----------
@app.route('/ai_chat', methods=['GET','POST'])
def ai_chat():
    if 'user' not in session:
        return redirect('/')

    reply="Ask any stock like RELIANCE, HCLTECH, NIFTY"

    if request.method=="POST":
        msg=request.form.get("msg","").upper()

        try:
            words=msg.replace("?","").split()
            stock=None

            # detect stock word
            for w in words:
                if len(w)>=3:
                    stock=w
                    break

            if not stock:
                return render_template("chat.html",reply="Type stock name properly")

            currency="₹"

            # 🔴 INDEX DETECTION
            if stock=="NIFTY":
                symbol="^NSEI"
            elif stock=="BANKNIFTY":
                symbol="^NSEBANK"
            elif stock=="SENSEX":
                symbol="^BSESN"

            # 🔴 CRYPTO (optional keep/remove)
            elif stock in ["BTC","BITCOIN"]:
                symbol="BTC-USD"
                currency="$"
            elif stock in ["ETH","ETHEREUM"]:
                symbol="ETH-USD"
                currency="$"

            # 🔴 NORMAL STOCK
            else:
                symbol=stock+".NS"

            df=yf.Ticker(symbol).history(period="3mo")

            # try US stock if NSE not found
            if df.empty and not symbol.startswith("^"):
                symbol=stock
                df=yf.Ticker(symbol).history(period="3mo")
                currency="$"

            if df.empty:
                reply="Stock/Index not found on Yahoo Finance."
            else:
                last=df['Close'].iloc[-1]
                avg=df['Close'].mean()

                predicted=(last+avg)/2
                target=predicted*1.03
                stoploss=last*0.97

                diff=abs(predicted-last)
                confidence=round(70+(diff/last)*100,2)
                if confidence>95:
                    confidence=95

                reply=f"""
AI Price Analysis for {stock}

Current Price: {currency}{round(last,2)}
Predicted Price: {currency}{round(predicted,2)}

Target Price: {currency}{round(target,2)}
Stoploss: {currency}{round(stoploss,2)}

Confidence Level: {confidence}%
"""

        except:
            reply="Error fetching market data."

    return render_template("chat.html", reply=reply)
# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
