from app import db
from datetime import datetime

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Ikke bruk secondary her hvis du bruker PortfolioStock-modellen
    stocks = db.relationship('PortfolioStock', backref='portfolio', lazy='dynamic')

    def __repr__(self):
        return f'<Portfolio {self.name}>'

class PortfolioStock(db.Model):
    __tablename__ = 'portfolio_stock'
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'))
    ticker = db.Column(db.String(20))
    shares = db.Column(db.Float, default=0)
    average_price = db.Column(db.Float, default=0)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PortfolioStock {self.ticker}>'

class StockTip(db.Model):
    __tablename__ = 'stock_tips'
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    tip_type = db.Column(db.String(10), nullable=False)  # BUY, SELL, HOLD
    confidence = db.Column(db.String(10), nullable=False)  # HIGH, MEDIUM, LOW
    analysis = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<StockTip {self.ticker} - {self.tip_type}>'