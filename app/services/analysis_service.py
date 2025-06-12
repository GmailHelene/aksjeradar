import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import io
import base64
from app.services.data_service import DataService

class AnalysisService:
    @staticmethod
    def calculate_moving_averages(data, periods=[20, 50, 200]):
        """
        Calculate moving averages for given periods
        
        Args:
            data (DataFrame): Historical stock data
            periods (list): List of periods for moving averages
            
        Returns:
            DataFrame: Data with moving averages
        """
        df = data.copy()
        for period in periods:
            df[f'MA_{period}'] = df['Close'].rolling(window=period).mean()
        return df 
    
    @staticmethod
    def calculate_rsi(data, period=14):
        """
        Calculate Relative Strength Index (RSI) 
        
        Args:
            data (DataFrame): Historical stock data
            period (int): Period for RSI calculation
            
        Returns:
            DataFrame: Data with RSI
        """
        df = data.copy()
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    
    @staticmethod
    def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
        """
        Calculate Moving Average Convergence Divergence (MACD)
        
        Args:
            data (DataFrame): Historical stock data
            fast_period (int): Fast period
            slow_period (int): Slow period
            signal_period (int): Signal period
            
        Returns:
            DataFrame: Data with MACD
        """
        df = data.copy()
        df['EMA_fast'] = df['Close'].ewm(span=fast_period, adjust=False).mean()
        df['EMA_slow'] = df['Close'].ewm(span=slow_period, adjust=False).mean()
        df['MACD'] = df['EMA_fast'] - df['EMA_slow']
        df['MACD_signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        return df
    
    @staticmethod
    def predict_next_day_price(ticker):
        """
        Predict stock price for the next day using linear regression
        
        Args:
            ticker (str): Stock ticker symbol
            days (int): Number of days of historical data to use
            
        Returns:
            dict: Prediction results
        """
        # Get historical data
        stock_data = DataService.get_stock_data(ticker, period='60d')
        stock_info = DataService.get_stock_info(ticker)
        if stock_data.empty:
            return {'error': 'No data available'}
        
        # Prepare data
        prices = stock_data['Close']
        volume = stock_data['Volume']

        volatility = AnalysisService.calculate_volatility(prices)
        sharpe_ratio = AnalysisService.calculate_sharpe_ratio(prices)
        support, resistance = AnalysisService.calculate_support_resistance(prices)
        last_volume, avg_volume = AnalysisService.calculate_volume_analysis(volume)
        pe_ratio = stock_info.get('trailingPE')
        dividend_yield = stock_info.get('dividendYield')
        
        last_signals = [
            {'date': '2024-06-01', 'signal': 'BUY'},
            {'date': '2024-05-15', 'signal': 'SELL'},
        ]
        
        return {
            'last_price': prices.iloc[-1],
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'support': support,
            'resistance': resistance,
            'volume': last_volume,
            'avg_volume': avg_volume,
            'pe_ratio': pe_ratio,
            'dividend_yield': dividend_yield,
            'last_signals': last_signals,
        }
    
    @staticmethod
    def get_technical_analysis(ticker):
        """
        Perform real technical analysis on a stock using historical data.
        Returns signal, RSI, MACD, support, resistance, and volume.
        """
        from app.services.data_service import DataService

        # Hent historiske data (60 dager for kortsiktig analyse)
        data = DataService.get_stock_data(ticker, period='60d')
        if data is None or data.empty or len(data) < 30:
            return {"error": "Not enough data for analysis"}

        # RSI
        df_rsi = AnalysisService.calculate_rsi(data)
        rsi = df_rsi['RSI'].iloc[-1] if 'RSI' in df_rsi.columns else None

        # MACD
        df_macd = AnalysisService.calculate_macd(data)
        macd = df_macd['MACD'].iloc[-1] if 'MACD' in df_macd.columns else None

        # Støtte og motstand
        support, resistance = AnalysisService.calculate_support_resistance(data['Close'], months=2)

        # Volum
        last_volume, avg_volume = AnalysisService.calculate_volume_analysis(data['Volume'])

        # Signal-logikk
        signal = "Hold"
        if rsi is not None and macd is not None:
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
            "rsi": round(rsi, 2) if rsi is not None else None,
            "macd": round(macd, 2) if macd is not None else None,
            "support": round(support, 2) if support is not None else None,
            "resistance": round(resistance, 2) if resistance is not None else None,
            "volume": int(last_volume) if last_volume is not None else None,
            "avg_volume": int(avg_volume) if avg_volume is not None else None
        }
     
    @staticmethod
    def get_stock_recommendation(ticker):
        """
        Get a recommendation for a stock based on technical analysis and prediction
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Recommendation
        """
        # Get technical analysis
        ta_result = AnalysisService.get_technical_analysis(ticker)
        if 'error' in ta_result:
            return {'error': ta_result['error']}
        
        # Get prediction
        pred_result = AnalysisService.predict_next_day_price(ticker)
        if 'error' in pred_result:
            return {'error': pred_result['error']}
        
        # Get stock info
        stock_info = DataService.get_stock_info(ticker)
        pe_ratio = stock_info.get('trailingPE')
        dividend_yield = stock_info.get('dividendYield')
        market_cap = stock_info.get('marketCap')
        
        # Combine signals for a recommendation
        ta_signal = ta_result['overall_signal']
        pred_signal = pred_result['trend']
        
        if ta_signal == 'BUY' and pred_signal == 'UP':
            recommendation = 'STRONG BUY'
            confidence = 'HIGH'
        elif ta_signal == 'SELL' and pred_signal == 'DOWN':
            recommendation = 'STRONG SELL'
            confidence = 'HIGH'
        elif ta_signal == 'BUY' or pred_signal == 'UP':
            recommendation = 'BUY'
            confidence = 'MEDIUM'
        elif ta_signal == 'SELL' or pred_signal == 'DOWN':
            recommendation = 'SELL'
            confidence = 'MEDIUM'
        else:
            recommendation = 'HOLD'
            confidence = 'LOW'
        
        return {
            'ticker': ticker,
            'recommendation': recommendation,
            'confidence': confidence,
            'technical_analysis': ta_result,
            'prediction': pred_result,
            'company_name': stock_info.get('longName', ticker),
            'sector': stock_info.get('sector', 'Unknown'),
            'industry': stock_info.get('industry', 'Unknown'),
            'market_cap': stock_info.get('marketCap', 'Unknown'),
            'pe_ratio': stock_info.get('trailingPE', 'Unknown'),
            'dividend_yield': stock_info.get('dividendYield', 'Unknown'),
            'target_price': stock_info.get('targetMeanPrice', 'Unknown'),
        }
    
    @staticmethod
    def calculate_volatility(prices):
        """
        Calculate the volatility of stock prices
        
        Args:
            prices (Series): Series of stock prices
            
        Returns:
            float: Volatility (standard deviation of returns)
        """
        returns = prices.pct_change().dropna()
        return np.std(returns)
    
    @staticmethod
    def calculate_sharpe_ratio(prices, risk_free_rate=0.02):
        """
        Calculate the Sharpe ratio of stock returns
        
        Args:
            prices (Series): Series of stock prices
            risk_free_rate (float): Risk-free rate (annualized)
            
        Returns:
            float: Sharpe ratio
        """
        returns = prices.pct_change().dropna()
        mean_return = returns.mean() * 252  # annualisert
        std_return = returns.std() * np.sqrt(252)
        if std_return == 0:
            return None
        return (mean_return - risk_free_rate) / std_return
    
    @staticmethod
    def calculate_relative_strength(stock_prices, index_prices, months=3):
        """
        Calculate the relative strength of a stock against an index
        
        Args:
            stock_prices (Series): Series of stock prices
            index_prices (Series): Series of index prices
            months (int): Number of months for the calculation
            
        Returns:
            float: Relative strength (%)
        """
        stock_return = stock_prices.pct_change(periods=21*months).iloc[-1]
        index_return = index_prices.pct_change(periods=21*months).iloc[-1]
        return (stock_return - index_return) * 100
    
    @staticmethod
    def calculate_support_resistance(prices, months=6):
        """
        Calculate the support and resistance levels for a stock
        
        Args:
            prices (Series): Series of stock prices
            months (int): Number of months for the calculation
            
        Returns:
            tuple: Support and resistance levels
        """
        support = prices[-21*months:].min()
        resistance = prices[-21*months:].max()
        return support, resistance
    
    @staticmethod
    def calculate_volume_analysis(volume):
        """
        Calculate volume analysis metrics
        
        Args:
            volume (Series): Series of stock trading volume
            
        Returns:
            tuple: Last volume and average volume
        """
        avg_volume = volume.rolling(window=21).mean().iloc[-1]
        last_volume = volume.iloc[-1]
        return last_volume, avg_volume

    @staticmethod
    def analyze_tickers(tickers):
        """
        Analyze multiple tickers and return a DataFrame with the results
        
        Args:
            tickers (list): List of stock ticker symbols
            
        Returns:
            DataFrame: Analysis results
        """
        # Initialize an empty DataFrame for results
        results = pd.DataFrame()
        
        # Iterate over tickers
        for ticker in tickers:
            # Hent data
            stock_data = DataService.get_stock_data(ticker, period='1y')
            if stock_data.empty:
                continue

            prices = stock_data['Close']
            volume = stock_data['Volume']

            # Volatilitet og Sharpe
            volatility = AnalysisService.calculate_volatility(prices)
            sharpe_ratio = AnalysisService.calculate_sharpe_ratio(prices)

            # Relativ styrke (krever index-data, f.eks. OSEBX)
            index_data = DataService.get_stock_data('^OSEAX', period='1y')
            if not index_data.empty:
                relative_strength_3m = AnalysisService.calculate_relative_strength(prices, index_data['Close'], months=3)
            else:
                relative_strength_3m = None

            # Støtte/motstand
            support, resistance = AnalysisService.calculate_support_resistance(prices)

            # Volum
            last_volume, avg_volume = AnalysisService.calculate_volume_analysis(volume)

            # Get stock info
            stock_info = DataService.get_stock_info(ticker)
            pe_ratio = stock_info.get('trailingPE')
            dividend_yield = stock_info.get('dividendYield')
            market_cap = stock_info.get('marketCap')
            last_signals = [
                {'date': '2024-06-01', 'signal': 'BUY'},
                {'date': '2024-05-15', 'signal': 'SELL'},
                # ... hent eller beregn signaler ...
            ]
            # Legg til i predictions-dict
            results = results.append({
                'ticker': ticker,
                'last_price': prices.iloc[-1],
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'relative_strength_3m': relative_strength_3m,
                'support': support,
                'resistance': resistance,
                'volume': last_volume,
                'avg_volume': avg_volume,
                'pe_ratio': pe_ratio,
                'dividend_yield': dividend_yield,
                'market_cap': market_cap,
                'last_signals': last_signals,
            }, ignore_index=True)
        
        return results


