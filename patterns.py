from typing import List, Tuple, Dict, Any


def is_bullish(c: Dict[str, float]) -> bool:
    return c["close"] > c["open"]


def is_bearish(c: Dict[str, float]) -> bool:
    return c["close"] < c["open"]


def body_size(c: Dict[str, float]) -> float:
    return abs(c["close"] - c["open"])


def total_range(c: Dict[str, float]) -> float:
    return c["high"] - c["low"]


def upper_shadow(c: Dict[str, float]) -> float:
    top = max(c["open"], c["close"])
    return c["high"] - top


def lower_shadow(c: Dict[str, float]) -> float:
    bottom = min(c["open"], c["close"])
    return bottom - c["low"]


def detect_doji(candles: List[Dict[str, float]], idx: int):
    c = candles[idx]
    body = body_size(c)
    range_ = total_range(c)
    if range_ == 0:
        return None
    if body / range_ < 0.1:
        return ("Doji", "NEUTRO", 0.4)
    return None


def detect_hammer(candles: List[Dict[str, float]], idx: int):
    c = candles[idx]
    body = body_size(c)
    range_ = total_range(c)
    if range_ == 0 or body == 0:
        return None
    lower = lower_shadow(c)
    upper = upper_shadow(c)
    if lower > 2 * body and upper < body:
        if is_bullish(c):
            return ("Martelo (Hammer)", "CALL", 0.55)
        else:
            return ("Martelo Invertido", "PUT", 0.55)
    return None


def detect_shooting_star(candles: List[Dict[str, float]], idx: int):
    c = candles[idx]
    body = body_size(c)
    range_ = total_range(c)
    if range_ == 0 or body == 0:
        return None
    upper = upper_shadow(c)
    lower = lower_shadow(c)
    if upper > 2 * body and lower < body:
        if is_bearish(c):
            return ("Estrela Cadente (Shooting Star)", "PUT", 0.55)
        else:
            return ("Pinça de Fundo", "CALL", 0.55)
    return None


def detect_engulfing(candles: List[Dict[str, float]], idx: int):
    if idx < 1:
        return None
    prev = candles[idx - 1]
    curr = candles[idx]
    prev_body = body_size(prev)
    curr_body = body_size(curr)
    if prev_body == 0 or curr_body == 0:
        return None
    if is_bearish(prev) and is_bullish(curr):
        if curr["open"] < prev["close"] and curr["close"] > prev["open"]:
            return ("Engolfo de Alta", "CALL", 0.65)
    if is_bullish(prev) and is_bearish(curr):
        if curr["open"] > prev["close"] and curr["close"] < prev["open"]:
            return ("Engolfo de Baixa", "PUT", 0.65)
    return None


def detect_morning_star(candles: List[Dict[str, float]], idx: int):
    if idx < 2:
        return None
    c1, c2, c3 = candles[idx - 2], candles[idx - 1], candles[idx]
    if is_bearish(c1) and is_bullish(c3):
        if body_size(c2) < body_size(c1) * 0.3:
            if c3["close"] > (c1["open"] + c1["close"]) / 2:
                return ("Estrela da Manhã", "CALL", 0.7)
    return None


def detect_evening_star(candles: List[Dict[str, float]], idx: int):
    if idx < 2:
        return None
    c1, c2, c3 = candles[idx - 2], candles[idx - 1], candles[idx]
    if is_bullish(c1) and is_bearish(c3):
        if body_size(c2) < body_size(c1) * 0.3:
            if c3["close"] < (c1["open"] + c1["close"]) / 2:
                return ("Estrela da Noite", "PUT", 0.7)
    return None


def detect_three_soldiers(candles: List[Dict[str, float]], idx: int):
    if idx < 2:
        return None
    c1, c2, c3 = candles[idx - 2], candles[idx - 1], candles[idx]
    if all(is_bullish(c) for c in [c1, c2, c3]):
        if c1["close"] < c2["close"] < c3["close"]:
            if c2["open"] >= c1["open"] and c3["open"] >= c2["open"]:
                return ("Três Soldados Brancos", "CALL", 0.75)
    return None


def detect_three_crows(candles: List[Dict[str, float]], idx: int):
    if idx < 2:
        return None
    c1, c2, c3 = candles[idx - 2], candles[idx - 1], candles[idx]
    if all(is_bearish(c) for c in [c1, c2, c3]):
        if c1["close"] > c2["close"] > c3["close"]:
            if c2["open"] <= c1["open"] and c3["open"] <= c2["open"]:
                return ("Três Corvos Negros", "PUT", 0.75)
    return None


def detect_marubozu(candles: List[Dict[str, float]], idx: int):
    c = candles[idx]
    body = body_size(c)
    range_ = total_range(c)
    if range_ == 0 or body == 0:
        return None
    upper = upper_shadow(c)
    lower = lower_shadow(c)
    if upper < body * 0.05 and lower < body * 0.05:
        if is_bullish(c):
            return ("Marubozu de Alta", "CALL", 0.6)
        else:
            return ("Marubozu de Baixa", "PUT", 0.6)
    return None


def detect_all_patterns(candles: List[Dict[str, float]]) -> List[Tuple[str, str, float]]:
    if not candles or len(candles) < 3:
        return []

    detectors = [
        detect_doji,
        detect_hammer,
        detect_shooting_star,
        detect_engulfing,
        detect_morning_star,
        detect_evening_star,
        detect_three_soldiers,
        detect_three_crows,
        detect_marubozu,
    ]

    signals = []
    for i in range(len(candles)):
        for detector in detectors:
            result = detector(candles, i)
            if result:
                signals.append(result)

    return signals
