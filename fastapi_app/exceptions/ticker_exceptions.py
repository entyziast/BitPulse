from exceptions.main_exception import BitPulseException


class TickerNotFoundException(BitPulseException):
    def __init__(self, symbol: str):
        self.message = f"Ticker with symbol '{symbol}' not found in database. Try to subscribe to this ticker first."
        self.status_code = 404


class TickerIDNotFoundException(BitPulseException):
    def __init__(self, id: int):
        self.message = f"Ticker with id '{id}' not found in database. Try to subscribe to this ticker first."
        self.status_code = 404

    
class TickerNotExistInBinanceException(BitPulseException):
    def __init__(self, symbol: str):
        self.message = f"Error to find ticker with symbol '{symbol}' in Binance API."
        self.status_code = 404


class ESNotFoundError(BitPulseException):
    def __init__(self, ticker_id: int):
        self.message = f"Ticker with ID {ticker_id} not found in Elasticsearch"
        self.status_code = 404