from typing import List, Tuple, Dict, Any


def fuse_signals(
    pattern_signals: List[Tuple[str, str, float]],
    indicator_signals: List[Tuple[str, str, float]],
) -> Tuple[str, float, Dict[str, List[Tuple[str, float]]]]:
    """Combina sinais de padrões e indicadores técnicos."""
    votes = {"CALL": [], "PUT": [], "NEUTRO": []}

    for name, direction, weight in pattern_signals + indicator_signals:
        votes[direction].append((name, weight))

    score_call = sum(w for _, w in votes["CALL"])
    score_put = sum(w for _, w in votes["PUT"])
    total = score_call + score_put

    if total == 0:
        return "NEUTRO", 0.0, votes

    if score_call > score_put:
        return "CALL", score_call / total, votes
    if score_put > score_call:
        return "PUT", score_put / total, votes
    return "NEUTRO", 0.5, votes
