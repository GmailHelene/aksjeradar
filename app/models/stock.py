from datetime import datetime
from app import db

class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    stocks = db.relationship('WatchlistStock', backref='watchlist', lazy='dynamic')
    
    def __repr__(self):
        return f'<Watchlist {self.name}>'

class WatchlistStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlist.id'))
    ticker = db.Column(db.String(20))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WatchlistStock {self.ticker}>'

class StockTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20))
    tip_type = db.Column(db.String(20))  # BUY, SELL, HOLD
    confidence = db.Column(db.String(20))  # HIGH, MEDIUM, LOW
    analysis = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    feedback = db.Column(db.Text)
    
    def __repr__(self):
        return f'<StockTip {self.ticker} - {self.tip_type}>'

