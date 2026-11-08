from typing import List, Tuple


def sma(values: List[float], window: int) -> List[float]:
    if len(values) < window:
        return []
    return [sum(values[i:i + window]) / window for i in range(len(values) - window + 1)]


def ema(values: List[float], window: int) -> List[float]:
    if len(values) < window:
        return []
    multiplier = 2 / (window + 1)
    result = [sum(values[:window]) / window]
    for price in values[window:]:
        result.append((price - result[-1]) * multiplier + result[-1])
    return result


def rsi(values: List[float], window: int = 14) -> List[float]:
    if len(values) < window + 1:
        return []
    gains = []
    losses = []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    rsi_values = []
    avg_gain = sum(gains[:window]) / window
    avg_loss = sum(losses[:window]) / window
    rsi_values.append(100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss != 0 else 100)

    for i in range(window, len(gains)):
        avg_gain = (avg_gain * (window - 1) + gains[i]) / window
        avg_loss = (avg_loss * (window - 1) + losses[i]) / window
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rsi_values.append(100 - (100 / (1 + avg_gain / avg_loss)))

    return rsi_values


def macd(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(values, fast)
    ema_slow = ema(values, slow)

    if not ema_fast or not ema_slow:
        return [], [], []

    start = slow - fast
    macd_line = [ema_fast[i + start] - ema_slow[i] for i in range(len(ema_slow))]

    signal_line = ema(macd_line, signal)
    if not signal_line:
        return macd_line, [], []

    start_hist = len(macd_line) - len(signal_line)
    histogram = [macd_line[i + start_hist] - signal_line[i] for i in range(len(signal_line))]

    return macd_line, signal_line, histogram


def bollinger_bands(values: List[float], window: int = 20, num_std: float = 2.0):
    if len(values) < window:
        return [], [], []

    middle, upper, lower = [], [], []
    for i in range(window, len(values) + 1):
        window_vals = values[i - window:i]
        mean = sum(window_vals) / window
        variance = sum((x - mean) ** 2 for x in window_vals) / window
        std = variance ** 0.5
        middle.append(mean)
        upper.append(mean + num_std * std)
        lower.append(mean - num_std * std)

    return middle, upper, lower


def evaluate_all_indicators(closes: List[float]) -> List[Tuple[str, str, float]]:
    signals = []

    # SMA 9 vs SMA 21
    sma9 = sma(closes, 9)
    sma21 = sma(closes, 21)
    if len(sma9) >= 2 and len(sma21) >= 2:
        if sma9[-1] > sma21[-1] and sma9[-2] <= sma21[-2]:
            signals.append(("Cruzamento SMA9/SMA21", "CALL", 0.6))
        elif sma9[-1] < sma21[-1] and sma9[-2] >= sma21[-2]:
            signals.append(("Cruzamento SMA9/SMA21", "PUT", 0.6))
        elif sma9[-1] > sma21[-1]:
            signals.append(("Tendência SMA9 > SMA21", "CALL", 0.45))
        elif sma9[-1] < sma21[-1]:
            signals.append(("Tendência SMA9 < SMA21", "PUT", 0.45))

    # EMA 12 vs EMA 26
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    if len(ema12) >= 2 and len(ema26) >= 2:
        if ema12[-1] > ema26[-1] and ema12[-2] <= ema26[-2]:
            signals.append(("Cruzamento EMA12/EMA26", "CALL", 0.6))
        elif ema12[-1] < ema26[-1] and ema12[-2] >= ema26[-2]:
            signals.append(("Cruzamento EMA12/EMA26", "PUT", 0.6))
        elif ema12[-1] > ema26[-1]:
            signals.append(("Tendência EMA12 > EMA26", "CALL", 0.45))
        elif ema12[-1] < ema26[-1]:
            signals.append(("Tendência EMA12 < EMA26", "PUT", 0.45))

    # RSI
    rsi_vals = rsi(closes, 14)
    if rsi_vals:
        last_rsi = rsi_vals[-1]
        if last_rsi < 30:
            signals.append(("RSI sobrevendido (< 30)", "CALL", 0.55))
        elif last_rsi > 70:
            signals.append(("RSI sobrecomprado (> 70)", "PUT", 0.55))

    # MACD
    macd_line, signal_line, _ = macd(closes)
    if len(macd_line) >= 2 and len(signal_line) >= 2:
        if macd_line[-1] > signal_line[-1] and macd_line[-2] <= signal_line[-2]:
            signals.append(("MACD cruzou para cima", "CALL", 0.6))
        elif macd_line[-1] < signal_line[-1] and macd_line[-2] >= signal_line[-2]:
            signals.append(("MACD cruzou para baixo", "PUT", 0.6))
        elif macd_line[-1] > signal_line[-1]:
            signals.append(("MACD acima do sinal", "CALL", 0.45))
        elif macd_line[-1] < signal_line[-1]:
            signals.append(("MACD abaixo do sinal", "PUT", 0.45))

    # Bollinger Bands
    middle, upper, lower = bollinger_bands(closes, 20, 2.0)
    if middle and upper and lower:
        last_close = closes[-1]
        if last_close > upper[-1]:
            signals.append(("Preço acima da Banda Superior", "PUT", 0.5))
        elif last_close < lower[-1]:
            signals.append(("Preço abaixo da Banda Inferior", "CALL", 0.5))
        elif last_close > middle[-1]:
            signals.append(("Preço acima da média de Bollinger", "CALL", 0.4))
        elif last_close < middle[-1]:
            signals.append(("Preço abaixo da média de Bollinger", "PUT", 0.4))

    return signals
