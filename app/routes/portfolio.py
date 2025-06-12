from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.portfolio import Portfolio, PortfolioStock
from app.models.stock import Watchlist, WatchlistStock, StockTip
from app.services.data_service import DataService
from app.services.analysis_service import AnalysisService
from app.services.ai_service import AIService


portfolio = Blueprint('portfolio', __name__)

@portfolio.route('/')
def index():
    if current_user.is_authenticated:
        user_portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    else:
        user_portfolios = Portfolio.query.all()

    portfolios_data = []
    for p in user_portfolios:
        stocks_data = []
        total_value = 0

        for stock in p.stocks:
            current_data = DataService.get_stock_data(stock.ticker, period='1d')
            if not current_data.empty:
                current_price = current_data['Close'].iloc[-1]
                value = current_price * stock.shares
                gain_loss = (current_price - stock.average_price) * stock.shares
                gain_loss_percent = ((current_price / stock.average_price) - 1) * 100 if stock.average_price > 0 else 0

                stocks_data.append({
                    'ticker': stock.ticker,
                    'shares': stock.shares,
                    'average_price': stock.average_price,
                    'current_price': current_price,
                    'value': value,
                    'gain_loss': gain_loss,
                    'gain_loss_percent': gain_loss_percent
                })

                total_value += value

        portfolios_data.append({
            'portfolio': p,
            'stocks': stocks_data,
            'total_value': total_value
        })

    return render_template('portfolio/index.html', portfolios=portfolios_data)

@portfolio.route('/create', methods=['GET', 'POST'])
@login_required
def create_portfolio():
    if request.method == 'POST':
        name = request.form.get('name')
        user_id = current_user.id  # <-- Her!
        portfolio = Portfolio(name=name, user_id=current_user.id)
        db.session.add(portfolio)
        db.session.commit()
        flash('Portfolio created!', 'success')
        return redirect(url_for('portfolio.index'))
    return render_template('portfolio/create.html')

@portfolio.route('/<int:id>')
def view(id):
    portfolio = Portfolio.query.get_or_404(id)

    # Fjern eierskapssjekk for å la alle se
    stocks_data = []
    total_value = 0
    total_investment = 0

    for stock in portfolio.stocks:
        current_data = DataService.get_stock_data(stock.ticker, period='1d')
        if not current_data.empty:
            current_price = current_data['Close'].iloc[-1]
            value = current_price * stock.shares
            investment = stock.average_price * stock.shares
            gain_loss = (current_price - stock.average_price) * stock.shares
            gain_loss_percent = ((current_price / stock.average_price) - 1) * 100 if stock.average_price > 0 else 0

            stocks_data.append({
                'ticker': stock.ticker,
                'shares': stock.shares,
                'average_price': stock.average_price,
                'current_price': current_price,
                'value': value,
                'investment': investment,
                'gain_loss': gain_loss,
                'gain_loss_percent': gain_loss_percent
            })

            total_value += value
            total_investment += investment

    total_gain_loss = total_value - total_investment
    total_gain_loss_percent = ((total_value / total_investment) - 1) * 100 if total_investment > 0 else 0

    tickers = [stock.ticker for stock in portfolio.stocks]
    ai_recommendation = AIService.get_ai_portfolio_recommendation(tickers) if tickers else None

    return render_template('portfolio/view.html',
                           portfolio=portfolio,
                           stocks=stocks_data,
                           total_value=total_value,
                           total_investment=total_investment,
                           total_gain_loss=total_gain_loss,
                           total_gain_loss_percent=total_gain_loss_percent,
                           ai_recommendation=ai_recommendation)

@portfolio.route('/<int:id>/add', methods=['GET', 'POST'])
@login_required
def add_stock(id):
    portfolio = Portfolio.query.get_or_404(id)

    # Fjern eierskapssjekk for å la alle legge til (eller behold hvis du vil begrense)
    if request.method == 'POST':
        ticker = request.form.get('ticker')
        shares = request.form.get('shares')
        price = request.form.get('price')

        if not ticker or not shares or not price:
            flash('All fields are required', 'danger')
            return redirect(url_for('portfolio.add_stock', id=id))

        try: 
            shares = float(shares)
            price = float(price)
        except ValueError:
            flash('Shares and price must be numbers', 'danger')
            return redirect(url_for('portfolio.add_stock', id=id))

        existing_stock = PortfolioStock.query.filter_by(portfolio_id=id, ticker=ticker).first()

        if existing_stock:
            total_value = (existing_stock.shares * existing_stock.average_price) + (shares * price)
            total_shares = existing_stock.shares + shares
            existing_stock.average_price = total_value / total_shares if total_shares > 0 else 0
            existing_stock.shares = total_shares
        else:
            stock = PortfolioStock(
                portfolio_id=id,
                ticker=ticker,
                shares=shares,
                average_price=price
            )
            db.session.add(stock)
 
        db.session.commit()
        flash('Stock added to portfolio', 'success')
        return redirect(url_for('portfolio.view', id=id))

    return render_template('portfolio/add_stock.html', portfolio=portfolio)

@portfolio.route('/<int:id>/remove/<int:stock_id>', methods=['POST'])
def remove_stock(id, stock_id):
    portfolio = Portfolio.query.get_or_404(id)

    # Fjern eierskapssjekk for å la alle fjerne (eller behold hvis du vil begrense)
    stock = PortfolioStock.query.get_or_404(stock_id)

    if stock.portfolio_id != id:
        flash('Stock does not belong to this portfolio', 'danger')
        return redirect(url_for('portfolio.view', id=id))

    db.session.delete(stock)
    db.session.commit()

    flash('Stock removed from portfolio', 'success')
    return redirect(url_for('portfolio.view', id=id))

@portfolio.route('/watchlist')
@login_required
def watchlist():
    watchlist = Watchlist.query.filter_by(user_id=current_user.id).first()
    stocks = []
    if watchlist:
        for ws in watchlist.stocks:
            # Hent sanntidsdata for aksjen
            stock_data = DataService.get_stock_data(ws.ticker, period='2d')
            last_price = None
            change_percent = None
            if not stock_data.empty and len(stock_data) > 1:
                last_price = stock_data['Close'].iloc[-1]
                prev_price = stock_data['Close'].iloc[-2]
                change_percent = ((last_price - prev_price) / prev_price) * 100 if prev_price else None
            # Hent navn fra info
            info = DataService.get_stock_info(ws.ticker)
            name = info.get('longName', ws.ticker)
            stocks.append({
                'ticker': ws.ticker,
                'name': name,
                'last_price': last_price,
                'change_percent': change_percent
            })
    return render_template('portfolio/watchlist.html', stocks=stocks)

@portfolio.route('/watchlist/create', methods=['GET', 'POST'])
def create_watchlist():
    if request.method == 'POST':
        name = request.form.get('name')
        user_id = current_user.id  # <-- Her!
        watchlist = Watchlist(name=name, user_id=user_id)
        db.session.add(watchlist)
        db.session.commit()
        flash('Watchlist created!', 'success')
        return redirect(url_for('portfolio.watchlist'))
    return render_template('portfolio/create_watchlist.html')

@portfolio.route('/watchlist/<int:id>/add', methods=['GET', 'POST'])
def add_to_watchlist(id):
    watchlist = Watchlist.query.get_or_404(id)

    # Fjern eierskapssjekk for å la alle legge til (eller behold hvis du vil begrense)
    if request.method == 'POST':
        ticker = request.form.get('ticker')

        if not ticker:
            flash('Ticker is required', 'danger')
            return redirect(url_for('portfolio.add_to_watchlist', id=id))

        existing = WatchlistStock.query.filter_by(watchlist_id=id, ticker=ticker).first()

        if existing:
            flash('Stock already in watchlist', 'warning')
        else:
            stock = WatchlistStock(watchlist_id=id, ticker=ticker)
            db.session.add(stock)
            db.session.commit()
            flash('Stock added to watchlist', 'success')

        return redirect(url_for('portfolio.watchlist'))

    return render_template('portfolio/add_to_watchlist.html', watchlist=watchlist)

@portfolio.route('/tips')
def stock_tips():
    tips = StockTip.query.order_by(StockTip.created_at.desc()).limit(10).all()
    if not tips:
        demo_tips = [
            {"ticker": "EQNR.OL", "tip_type": "BUY", "confidence": "HIGH", 
             "analysis": "Strong technical signals with support from rising oil prices."},
            {"ticker": "DNB.OL", "tip_type": "HOLD", "confidence": "MEDIUM", 
             "analysis": "Solid fundamentals but facing market headwinds in the banking sector."},
            {"ticker": "NHY.OL", "tip_type": "BUY", "confidence": "MEDIUM", 
             "analysis": "Potential growth with aluminum price recovery and green initiatives."},
            {"ticker": "TEL.OL", "tip_type": "SELL", "confidence": "LOW", 
             "analysis": "Increased competition and margin pressure in key markets."},
            {"ticker": "AAPL", "tip_type": "BUY", "confidence": "HIGH", 
             "analysis": "Strong product cycle and services growth with robust cash position."}
        ]
        for tip in demo_tips:
            stock_tip = StockTip(
                ticker=tip["ticker"],
                tip_type=tip["tip_type"],
                confidence=tip["confidence"],
                analysis=tip["analysis"]
            )
            db.session.add(stock_tip)
        db.session.commit()
        tips = StockTip.query.order_by(StockTip.created_at.desc()).limit(10).all()
    return render_template('portfolio/tips.html', tips=tips)

@portfolio.route('/tips/add', methods=['GET', 'POST'])
@login_required
def add_tip():
    if request.method == 'POST':
        ticker = request.form.get('ticker')
        tip_type = request.form.get('tip_type')
        confidence = request.form.get('confidence')
        analysis = request.form.get('analysis')
        tip = StockTip(
            ticker=ticker,
            tip_type=tip_type,
            confidence=confidence,
            analysis=analysis,
            user_id=current_user.id
        )
        db.session.add(tip)
        db.session.commit()
        flash('Stock tip added successfully', 'success')
        return redirect(url_for('portfolio.stock_tips'))
    ticker = request.args.get('ticker', '')
    return render_template('portfolio/add_tip.html', ticker=ticker)

@portfolio.route('/tips/feedback/<int:tip_id>', methods=['POST'])
@login_required
def tip_feedback(tip_id):
    tip = StockTip.query.get_or_404(tip_id)
    feedback = request.form.get('feedback')
    tip.feedback = feedback
    db.session.commit()
    flash('Feedback saved!', 'success')
    return redirect(url_for('portfolio.stock_tips'))

@portfolio.route('/add/<ticker>')
@login_required
def add_stock_by_ticker(ticker):
    stock_info = DataService.get_stock_info(ticker)
    if not stock_info:
        flash(f"Aksje {ticker} ble ikke funnet.", "danger")
        return redirect(url_for('main.index'))

    # Finn eller opprett brukerens første portefølje
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio:
        portfolio = Portfolio(name="Min portefølje", user_id=current_user.id)
        db.session.add(portfolio)
        db.session.commit()

    # Sjekk om aksjen allerede finnes i porteføljen
    existing_stock = PortfolioStock.query.filter_by(portfolio_id=portfolio.id, ticker=ticker).first()
    if existing_stock:
        # Øk antall aksjer med 1 (eller tilpass etter behov)
        existing_stock.shares += 1
    else:
        # Legg til ny aksje med 1 aksje og dagens pris som snittpris
        avg_price = stock_info.get('regularMarketPrice') or 0
        stock = PortfolioStock(
            portfolio_id=portfolio.id,
            ticker=ticker,
            shares=1,
            average_price=avg_price
        )
        db.session.add(stock)

    db.session.commit()
    flash(f"Aksje {ticker} lagt til i din portefølje!", "success")
    return redirect(url_for('main.index'))