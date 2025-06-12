import os
import openai
import joblib
from app.services.data_service import DataService
from app.services.analysis_service import AnalysisService
from app.models.stock import StockTip, Watchlist, WatchlistStock
from app.models.portfolio import Portfolio, PortfolioStock

class AIService:
    # Ekte register med analyse-data
    ANALYSIS_REGISTER = {
        "EQNR": {
            "signal": "Buy",
            "confidence": "High",
            "sentiment": "Bullish",
            "comment": "Sterk oljepris og gode kvartalstall."
        },
        "AAPL": {
            "signal": "Hold",
            "confidence": "Medium",
            "sentiment": "Neutral",
            "comment": "Stabil vekst, men høyt priset."
        },
        "TSLA": {
            "signal": "Sell",
            "confidence": "Low",
            "sentiment": "Bearish",
            "comment": "Usikkerhet rundt leveranser og marginer."
        },
        # Legg til flere tickere her...
    }

    ml_model = joblib.load('stock_tip_model.pkl')

    @staticmethod
    def get_ai_analysis(ticker, api_key=None):
        """
        Get AI-powered analysis for a stock
        
        Args:
            ticker (str): Stock ticker symbol
            api_key (str, optional): OpenAI API key
            
        Returns:
            dict: AI analysis
        """
        # Set API key
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.environ.get('OPENAI_API_KEY')
        
        if not openai.api_key:
            return {
                'ticker': ticker,
                'analysis': "AI analysis unavailable - API key not provided. Please set your OpenAI API key in the settings.",
                'investment_strategy': None,
                'risk_assessment': None
            }
          
        try:
            # Get stock data and analysis
            stock_info = DataService.get_stock_info(ticker)
            ta_result = AnalysisService.get_technical_analysis(ticker)
            pred_result = AnalysisService.predict_next_day_price(ticker)
            
            company_name = stock_info.get('longName', ticker)
            sector = stock_info.get('sector', 'Unknown')
            current_price = ta_result.get('last_price', 'Unknown')
            ma_signals = f"MA 20/50: {ta_result.get('ma_20_50_signal', 'Unknown')}, MA 50/200: {ta_result.get('ma_50_200_signal', 'Unknown')}"
            rsi = f"RSI: {ta_result.get('rsi', 'Unknown')} - {ta_result.get('rsi_signal', 'Unknown')}"
            macd = f"MACD Signal: {ta_result.get('macd_signal', 'Unknown')}"

            # Få ML-tipset
            ml_tip = AIService.get_ml_tip(ticker)

            # Hent siste signaler fra databasen eller annen kilde
            last_signals = [
                {'date': '2024-06-01', 'signal': 'BUY'},
                {'date': '2024-05-15', 'signal': 'SELL'},
                # ...hent fra din egen signal-logikk...
            ]
            signals_text = "\n".join([f"{s['date']}: {s['signal']}" for s in last_signals[-5:]])  # Siste 5 signaler

            prompt = f"""
You are a professional stock analyst AI. Analyze the stock {ticker} ({company_name}) in the {sector} sector.
Current Price: {current_price}
Technical Analysis: {ma_signals}, {rsi}, {macd}
Prediction: {prediction}
Recent News: {news_text}
Previous AI tips: {tips_text}
User feedback on previous tips: {feedback_text}
Machine Learning model tip: {ml_tip}
Last signals: {signals_text}
Give a detailed, actionable buy/sell/hold recommendation with reasoning, investment strategy (short/long term), and risk assessment. Structure your answer in three sections: Market Analysis, Investment Strategy, Risk Assessment. Explain if you agree or disagree with the ML model tip and why.
"""

            response = openai.ChatCompletion.create(
                model="gpt-4",  # eller "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "You are a professional stock analyst AI."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            analysis_text = response.choices[0].message.content.strip()

            # Del opp i seksjoner
            sections = analysis_text.split('\n\n')
            market_analysis = sections[0] if len(sections) > 0 else analysis_text
            investment_strategy = sections[1] if len(sections) > 1 else None
            risk_assessment = sections[2] if len(sections) > 2 else None

            return {
                'ticker': ticker,
                'company_name': company_name,
                'summary': market_analysis,  # eller 'summary': analysis_text,
                'analysis': analysis_text,
                'market_analysis': market_analysis,
                'investment_strategy': investment_strategy,
                'risk_assessment': risk_assessment,
                'ml_tip': ml_tip
            }
        
        except Exception as e:
            return {
                'ticker': ticker,
                'error': str(e),
                'analysis': "An error occurred during AI analysis. Please try again later."
            }
    
    @staticmethod
    def get_ai_portfolio_recommendation(tickers, api_key=None):
        """
        Get AI portfolio recommendation based on a list of tickers
        
        Args:
            tickers (list): List of stock ticker symbols
            api_key (str, optional): OpenAI API key
            
        Returns:
            dict: Portfolio recommendation
        """
        # Set API key
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.environ.get('OPENAI_API_KEY')
        
        if not openai.api_key:
            return {
                'recommendation': "AI portfolio recommendation unavailable - API key not provided.",
                'allocation': {},
                'strategy': None
            }
        
        try:
            # Get data for all tickers
            stocks_data = []
            for ticker in tickers:
                info = DataService.get_stock_info(ticker)
                ta = AnalysisService.get_technical_analysis(ticker)
                
                if 'error' not in ta:
                    stocks_data.append({
                        'ticker': ticker,
                        'name': info.get('longName', ticker),
                        'sector': info.get('sector', 'Unknown'),
                        'price': ta.get('last_price', 'Unknown'),
                        'signal': ta.get('overall_signal', 'Unknown')
                    })
            
            # Create prompt
            stocks_text = "\n".join([
                f"{s['ticker']} ({s['name']}): Price ${s['price']}, Sector: {s['sector']}, Signal: {s['signal']}"
                for s in stocks_data
            ])
            
            prompt = f"""
            Analyze the following portfolio of stocks:
            
            {stocks_text}
            
            Provide:
            1. Overall portfolio recommendation and strategy
            2. Suggested allocation percentages for each stock
            3. Risk assessment and diversification analysis
            
            Format your response in a structured way with clear sections.
            """
            
            # Get AI response
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=1000,
                n=1,
                stop=None,
                temperature=0.7,
            )
            
            recommendation_text = response.choices[0].text.strip()
            
            # Extract allocations from text (this is a simple approach, might need improvement)
            allocation = {}
            for stock in stocks_data:
                ticker = stock['ticker']
                # Look for percentage patterns
                for line in recommendation_text.split('\n'):
                    if ticker in line and '%' in line:
                        # Extract percentage
                        try:
                            percentage = float(line.split('%')[0].split()[-1])
                            allocation[ticker] = percentage
                        except:
                            allocation[ticker] = 0
            
            # If we couldn't find allocations, distribute equally
            if not allocation:
                equal_percent = 100 / len(tickers)
                allocation = {ticker: equal_percent for ticker in tickers}
            
            # Extract sections
            sections = recommendation_text.split('\n\n')
            
            overall_recommendation = sections[0] if len(sections) > 0 else recommendation_text
            allocation_strategy = sections[1] if len(sections) > 1 else None
            risk_assessment = sections[2] if len(sections) > 2 else None
            
            return {
                'recommendation': recommendation_text,
                'overall': overall_recommendation,
                'allocation_strategy': allocation_strategy,
                'risk_assessment': risk_assessment,
                'allocation': allocation
            }
        
        except Exception as e:
            return {
                'error': str(e),
                'recommendation': "An error occurred during AI portfolio analysis. Please try again later."
            }
    
    @staticmethod
    def get_ml_tip(ticker):
        ta = AnalysisService.get_technical_analysis(ticker)
        if 'error' in ta:
            return 'HOLD'
        # Konverter signaler til tall
        def to_num(signal):
            if signal == 'BUY' or signal == 'OVERSOLD': return 1
            if signal == 'SELL' or signal == 'OVERBOUGHT': return -1
            return 0
        features = [[
            to_num(ta.get('ma_20_50_signal')),
            to_num(ta.get('ma_50_200_signal')),
            to_num(ta.get('rsi_signal')),
            to_num(ta.get('macd_signal'))
        ]]
        prediction = AIService.ml_model.predict(features)[0]
        return prediction

    @staticmethod
    def get_ai_analysis(ticker):
        ticker = ticker.upper()
        if ticker in AIService.ANALYSIS_REGISTER:
            return AIService.ANALYSIS_REGISTER[ticker]
        else:
            return {
                "signal": "N/A",
                "confidence": "N/A",
                "sentiment": "N/A",
                "comment": "Ingen analyse funnet for denne tickeren."
            }