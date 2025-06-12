from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.services.analysis_service import AnalysisService
from app.services.ai_service import AIService
from app.services.data_service import DataService, OSLO_BORS_TICKERS, GLOBAL_TICKERS
import random


analysis = Blueprint('analysis', __name__)

@analysis.route('/')
def index():
    oslo_stocks = DataService.get_oslo_bors_overview()
    global_stocks = DataService.get_global_stocks_overview()
    crypto = DataService.get_crypto_overview()
    currency = DataService.get_currency_overview()

    # Tell signalene
    buy_signals = sum(1 for d in oslo_stocks.values() if d.get('signal') == 'BUY')
    buy_signals += sum(1 for d in global_stocks.values() if d.get('signal') == 'BUY')
    sell_signals = sum(1 for d in oslo_stocks.values() if d.get('signal') == 'SELL')
    sell_signals += sum(1 for d in global_stocks.values() if d.get('signal') == 'SELL')
    neutral_signals = sum(1 for d in oslo_stocks.values() if d.get('signal') not in ['BUY', 'SELL'])
    neutral_signals += sum(1 for d in global_stocks.values() if d.get('signal') not in ['BUY', 'SELL'])

    # Markedssentiment (velg selv logikk, her: flest signaler vinner)
    if buy_signals > sell_signals and buy_signals > neutral_signals:
        market_sentiment = "Bullish"
    elif sell_signals > buy_signals and sell_signals > neutral_signals:
        market_sentiment = "Bearish"
    elif neutral_signals > 0:
        market_sentiment = "Neutral"
    else:
        market_sentiment = "N/A"

    return render_template(
        'analysis/index.html',
        oslo_stocks=oslo_stocks,
        global_stocks=global_stocks,
        crypto=crypto,
        currency=currency,
        buy_signals=buy_signals,
        sell_signals=sell_signals,
        neutral_signals=neutral_signals,
        market_sentiment=market_sentiment
    )

@analysis.route('/technical')
def technical():
    oslo = OSLO_BORS_TICKERS[:10]
    global_ = GLOBAL_TICKERS[:10]
    crypto = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD"]
    valuta = ["USDNOK=X", "EURUSD=X", "USDSEK=X", "USDGBP=X"]

    all_tickers = oslo + global_ + crypto + valuta

    analyses = {}
    for ticker in all_tickers:
        analyses[ticker] = AnalysisService.get_technical_analysis(ticker)

    return render_template('analysis/technical.html', analyses=analyses)

@analysis.route('/prediction')
def prediction():
    tickers_oslo = OSLO_BORS_TICKERS[:50]
    tickers_global = GLOBAL_TICKERS[:50]
    predictions_oslo = {}
    predictions_global = {}
    for ticker in tickers_oslo:
        predictions_oslo[ticker] = AnalysisService.get_price_prediction(ticker)
    for ticker in tickers_global:
        predictions_global[ticker] = AnalysisService.get_price_prediction(ticker)
    return render_template(
        'analysis/prediction.html',
        predictions_oslo=predictions_oslo,
        predictions_global=predictions_global
    )

@analysis.route('/recommendation')
def recommendation():
    ticker = request.args.get('ticker')
    if not ticker:
        flash("No ticker specified.", "warning")
        return redirect(url_for('analysis.index'))
    recommendation = AnalysisService.get_stock_recommendation(ticker)
    return render_template(
        'analysis/recommendation.html',
        ticker=ticker,
        recommendation=recommendation
    )


@analysis.route('/ai', methods=['GET', 'POST'])
def ai():
    ai_analysis = None
    ticker = ""
    ai_analyses = AIService.ANALYSIS_REGISTER  # Send hele registeret til templaten
    if request.method == 'POST':
        ticker = request.form.get('ticker')
        if ticker:
            ai_analysis = AIService.get_ai_analysis(ticker)
    return render_template('analysis/ai.html', ai_analysis=ai_analysis, ticker=ticker, ai_analyses=ai_analyses)

@analysis.route('/market-overview')
def market_overview():
    market_overview = DataService.get_market_overview()
    return render_template(
        'analysis/market_overview.html',
        oslo_stocks=market_overview['oslo_stocks'],
        global_stocks=market_overview['global_stocks'],
        crypto=market_overview['crypto'],
        currency=market_overview['currency']
)

class AnalysisService:
    @staticmethod
    def get_price_prediction(ticker):
        # Hent historiske priser og gjør en enkel prediksjon (dummy-eksempel)
        # Bytt ut med ekte ML-modell hvis du har!
        predicted_price = random.uniform(50, 500)
        signal = random.choice(['Buy', 'Sell', 'Hold'])
        confidence = random.choice(['High', 'Medium', 'Low'])
        return {
            "predicted_price": predicted_price,
            "signal": signal,
            "confidence": confidence
        }

    @staticmethod
    def get_technical_analysis(ticker):
        # Dummy-teknisk analyse, bytt ut med ekte logikk om ønskelig
        import random
        rsi = round(random.uniform(10, 90), 2)
        macd = round(random.uniform(-5, 5), 2)
        support = round(random.uniform(50, 200), 2)
        resistance = round(random.uniform(200, 400), 2)
        volume = random.randint(100000, 1000000)
        avg_volume = random.randint(100000, 1000000)
        signal = "Hold"
        if rsi < 30 and macd > 0:
            signal = "Buy"
        elif rsi > 70 and macd < 0:
            signal = "Sell"
        elif macd > 0:
            signal = "Buy"
        elif macd < 0:
            signal = "Sell"
        return {
            "signal": signal,
            "rsi": rsi,
            "macd": macd,
            "support": support,
            "resistance": resistance,
            "volume": volume,
            "avg_volume": avg_volume
        }

class AIService:
    ANALYSIS_REGISTER = {
        "AAPL": {"signal": "BUY", "confidence": 0.9, "comment": "Strong buy due to strong earnings", "sentiment": "Bullish"},
        "TSLA": {"signal": "SELL", "confidence": 0.85, "comment": "Overvalued based on P/E ratio", "sentiment": "Bearish"},
        "AMZN": {"signal": "HOLD", "confidence": 0.75, "comment": "Stable growth, hold for now", "sentiment": "Neutral"},
        # Add more tickers and analyses as needed
    }

    @staticmethod
    def get_ai_analysis(ticker):
        # Dummy-eksempel, bytt ut med ekte AI-analyse
        import random
        signal = random.choice(['Buy', 'Sell', 'Hold'])
        confidence = random.choice(['High', 'Medium', 'Low'])
        sentiment = random.choice(['Bullish', 'Bearish', 'Neutral'])
        comment = f"AI vurderer {ticker} som {signal.lower()} med {confidence.lower()} selvtillit."
        return {
            "signal": signal,
            "confidence": confidence,
            "sentiment": sentiment,
            "comment": comment
        }

    @staticmethod
    def get_all_ai_analysis():
        # Returner en dict med eksempelticker og analyse
        return {
            "EQNR": {"signal": "BUY", "confidence": 0.85, "comment": "Sterk trend", "sentiment": "Bullish"},
            "AAPL": {"signal": "HOLD", "confidence": 0.65, "comment": "Avvent", "sentiment": "Neutral"},
            # osv...
        }