"""OCC symbol helpers and expiry/strike selection."""

from datetime import date, datetime


def build_occ_symbol(ticker, expiry, opt_type, strike):
    """Build OCC option symbol: IWM260630C00265000."""
    ticker = ticker.upper()
    exp_dt = datetime.strptime(expiry, "%Y-%m-%d")
    exp_str = exp_dt.strftime("%y%m%d")
    t = "C" if opt_type.lower() == "call" else "P"
    strike_int = int(round(float(strike) * 1000))
    strike_str = str(strike_int).zfill(8)
    return f"{ticker}{exp_str}{t}{strike_str}"


def parse_occ_symbol(sym):
    """Parse OCC symbol into components."""
    i = 0
    while i < len(sym) and sym[i].isalpha():
        i += 1
    ticker = sym[:i]
    date_str = sym[i:i+6]
    opt_type = "call" if sym[i+6] == "C" else "put"
    strike = int(sym[i+7:]) / 1000
    expiry = datetime.strptime(date_str, "%y%m%d").strftime("%Y-%m-%d")
    return {
        "ticker": ticker,
        "expiry": expiry,
        "type": opt_type,
        "strike": strike,
    }


def select_expiry(expirations, target_dte=120):
    """Pick the expiration closest to the target DTE."""
    today = date.today()
    def key(exp):
        dte = (date.fromisoformat(exp) - today).days
        return (abs(dte - target_dte), -dte)
    return min(expirations, key=key)


def select_strikes(strikes, price, count=5):
    """Pick the `count` strikes nearest to the current price, sorted descending."""
    atm = round(price)
    nearest = sorted(strikes, key=lambda s: (abs(s - atm), -s))[:count]
    return sorted(nearest, reverse=True)
