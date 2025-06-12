from flask import Blueprint, render_template
from app.services.data_service import DataService

stocks = Blueprint('stocks', __name__, url_prefix='/stocks')

@stocks.route('/')
def index():
    oslo_stocks = DataService.get_oslo_bors_overview()
    global_stocks = DataService.get_global_stocks_overview()
    crypto = DataService.get_crypto_overview()
    currency = DataService.get_currency_overview()  # <-- denne linjen må være med
    return render_template(
        'stocks/index.html',
        oslo_stocks=oslo_stocks,
        global_stocks=global_stocks,
        crypto=crypto,
        currency=currency,)