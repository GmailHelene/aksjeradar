# filepath: [data_service.py](http://_vscodecontentref_/3)
import yfinance as yf
import pandas as pd
import requests

# Oslo Børs ticker symbols
OSLO_BORS_TICKERS = [
    "EQNR.OL", "DNB.OL", "NHY.OL", "YAR.OL", "TEL.OL", "ORK.OL", "MOWI.OL", "SALM.OL", "TGS.OL", "SUBC.OL",
    "AKSO.OL", "AKERBP.OL", "PGS.OL", "STB.OL", "KOG.OL", "ELK.OL", "NOD.OL", "SCATC.OL", "BWLPG.OL", "GOGL.OL",
    "ODF.OL", "FRO.OL", "HAFNI.OL", "MPC.OL", "SASNO.OL", "NAS.OL", "NRC.OL", "AFG.OL", "BONHR.OL", "DNO.OL",
    "GSF.OL", "LPG.OL", "QFR.OL", "SCHA.OL", "SNI.OL", "TOM.OL", "VOW.OL", "WWI.OL", "ZAL.OL", "XXL.OL",
    "NRC.OL", "NPRO.OL", "PLCS.OL", "RECSI.OL", "SBX.OL", "SVEG.OL", "TGS.OL", "VISTIN.OL", "WAWI.OL", "YAR.OL"
]

# Global tickers
GLOBAL_TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "BRK-B", "JPM", "V",
    "UNH", "HD", "PG", "MA", "LLY", "AVGO", "XOM", "MRK", "ABBV", "COST",
    "PEP", "KO", "CVX", "WMT", "BAC", "DIS", "ADBE", "CSCO", "PFE", "T",
    "NKE", "MCD", "ORCL", "CRM", "ABT", "CMCSA", "TMO", "ACN", "DHR", "TXN",
    "LIN", "NEE", "WFC", "BMY", "PM", "HON", "AMGN", "UNP", "UPS", "LOW", "QCOM"
]

# Crypto tickers (for søk)
CRYPTO_TICKERS = [
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "AVAX-USD", "DOT-USD", "LINK-USD",
    "MATIC-USD", "TRX-USD", "LTC-USD", "BCH-USD", "XLM-USD", "ATOM-USD", "ETC-USD", "FIL-USD", "ICP-USD", "APT-USD",
    "HBAR-USD", "VET-USD", "NEAR-USD", "OP-USD", "GRT-USD", "AAVE-USD", "SAND-USD", "MANA-USD", "XTZ-USD", "EGLD-USD"
]

class DataService:
    @staticmethod
    def get_stock_data(ticker, period='1y'):
        """Get historical stock data for a specific ticker"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            return hist
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_stock_info(ticker):
        """Get detailed information about a stock"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info
        except Exception as e:
            print(f"Error fetching info for {ticker}: {e}")
            return {}

    @staticmethod
    def get_multiple_stocks_data(tickers):
        """Get data for multiple stocks"""
        result = {}
        for ticker in tickers:
            data = DataService.get_stock_data(ticker)
            if not data.empty and len(data) > 0:
                last_close = data['Close'].iloc[-1]
                prev_close = data['Close'].iloc[-2] if len(data) > 1 else data['Open'].iloc[-1]
                change = last_close - prev_close
                change_percent = (change / prev_close) * 100 if prev_close > 0 else 0
                signal = "BUY" if change_percent > 0 else "SELL"
                result[ticker] = {
                    'name': ticker,
                    'last_price': last_close,
                    'change': change,
                    'change_percent': change_percent,
                    'signal': signal,
                    'data': data
                }
        return result

    @staticmethod
    def get_oslo_bors_overview():
        """Hent oversikt over Oslo Børs-aksjer med sanntidsdata fra Yahoo Finance."""
        tickers = OSLO_BORS_TICKERS
        data = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                data[ticker] = {
                    "name": info.get("longName", ticker),
                    "last_price": info.get("regularMarketPrice"),
                    "change": info.get("regularMarketChange"),
                    "change_percent": info.get("regularMarketChangePercent"),
                    "signal": "BUY" if info.get("regularMarketChangePercent", 0) > 0 else "SELL"
                }
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                data[ticker] = {
                    "name": ticker,
                    "last_price": None,
                    "change": None,
                    "change_percent": None,
                    "signal": None
                }
        return data

    @staticmethod
    def get_global_stocks_overview():
        """Get an overview of global stocks"""
        return DataService.get_multiple_stocks_data(GLOBAL_TICKERS)

    @staticmethod
    def get_crypto_overview():
        """Hent kryptodata fra CoinGecko API"""
        url = "https://api.coingecko.com/api/v3/simple/price"
        coins = ["bitcoin", "ethereum", "solana", "cardano", "polkadot", "chainlink", "uniswap", "binancecoin"]
        ids = ",".join(coins)
        params = {
            "ids": ids,
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            mapping = {
                "bitcoin": ("BTC", "Bitcoin"),
                "ethereum": ("ETH", "Ethereum"),
                "solana": ("SOL", "Solana"),
                "cardano": ("ADA", "Cardano"),
                "polkadot": ("DOT", "Polkadot"),
                "chainlink": ("LINK", "Chainlink"),
                "uniswap": ("UNI", "Uniswap"),
                "binancecoin": ("BNB", "Binance Coin"),
            }
            result = {}
            for key, (symbol, name) in mapping.items():
                if key in data:
                    result[symbol] = {
                        "name": name,
                        "last_price": data[key].get("usd"),
                        "change_percent": data[key].get("usd_24h_change"),
                        "signal": "BUY" if data[key].get("usd_24h_change", 0) > 0 else "SELL"
                    }
            return result
        except Exception as e:
            print("Error fetching crypto:", e)
            return {}

    @staticmethod
    def search_ticker(query):
        """Search for ticker symbols"""
        all_tickers = OSLO_BORS_TICKERS + GLOBAL_TICKERS + CRYPTO_TICKERS
        return [ticker for ticker in all_tickers if query.upper() in ticker.upper()]

    @staticmethod
    def get_single_stock_data(ticker):
        """Get data for a single stock"""
        result = DataService.get_multiple_stocks_data([ticker])
        return result.get(ticker, {})

    @staticmethod
    def get_currency_overview():
        """Get the latest currency exchange rates"""
        url = "https://api.exchangerate.host/latest"
        params = {"base": "USD", "symbols": "NOK,EUR,SEK,GBP"}
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            rates = data.get("rates", {})
            # Sjekk at date finnes, ellers bruk dagens dato
            date = data.get("date")
            if not date:
                from datetime import date as dt 
                date = dt.today().isoformat()
            y_url = "https://api.exchangerate.host/" + date
            y_params = {"base": "USD", "symbols": "NOK,EUR,SEK,GBP"}
            y_r = requests.get(y_url, params=y_params, timeout=10)
            y_data = y_r.json()
            y_rates = y_data.get("rates", {})
            result = {}
            for symbol, price in rates.items():
                prev = y_rates.get(symbol)
                change = ((price - prev) / prev * 100) if prev else None
                signal = None
                if change is not None:
                    signal = "BUY" if change > 0 else "SELL"
                result[f"USD/{symbol}"] = {
                    "name": f"USD/{symbol}",
                    "last_price": price,
                    "change_percent": change,
                    "signal": signal
                }
            return result
        except Exception as e:
            print("Error fetching currency:", e)
            return {}

    @staticmethod
    def get_market_sentiment(stocks):
        """Get the current market sentiment"""
        signals = [d.get('signal') for d in stocks.values() if d.get('signal')]
        if not signals:
            return "Neutral"
        if signals.count('Buy') > signals.count('Sell'):
            return "Bullish"
        elif signals.count('Sell') > signals.count('Buy'):
            return "Bearish"
        else:
            return "Neutral"

    @staticmethod
    def get_ai_analysis_data():
        """Hent AI-basert analyse for utvalgte aksjer og kryptovalutaer."""
        # Dummy-data, bytt ut med ekte AI-analyse senere
        return {
            "EQNR.OL": {"name": "Equinor", "last_price": 300, "change_percent": 1.2, "signal": "Buy"},
            "NHY.OL": {"name": "Norsk Hydro", "last_price": 80, "change_percent": -0.5, "signal": "Hold"},
            "BTC": {"name": "Bitcoin", "last_price": 67000, "change_percent": 2.1, "signal": "Buy"},
            "AAPL": {"name": "Apple", "last_price": 190, "change_percent": 0.8, "signal": "Buy"},
        }

    @staticmethod
    def get_market_overview():
        """Returnerer samlet markedsoversikt for Oslo Børs, globale aksjer, krypto og valuta."""
        return {
            "oslo_stocks": DataService.get_oslo_bors_overview(),
            "global_stocks": DataService.get_global_stocks_overview(),
            "crypto": DataService.get_crypto_overview(),
            "currency": DataService.get_currency_overview()
        }