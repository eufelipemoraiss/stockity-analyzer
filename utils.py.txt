import cv2
import easyocr
import numpy as np
from PIL import Image
from typing import List, Tuple, Dict, Any


_reader = None


def get_reader():
    """Inicializa o leitor OCR apenas uma vez."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["pt", "en"], gpu=False)
    return _reader


def extract_text(image: Image.Image) -> str:
    """Extrai texto do print usando OCR local."""
    try:
        arr = np.array(image)
        results = get_reader().readtext(arr)
        return " ".join([r[1] for r in results])
    except Exception:
        return ""


def extract_dominant_colors(image: Image.Image, k: int = 5) -> List[Dict[str, Any]]:
    """Extrai as cores dominantes da imagem usando k-means."""
    try:
        small = image.resize((100, 100))
        arr = np.array(small)
        pixels = arr.reshape(-1, 3).astype(np.float32)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        counts = np.bincount(labels.flatten())
        colors = centers.astype(int)

        dominant = []
        for count, color in sorted(zip(counts, colors), key=lambda x: x[0], reverse=True):
            r, g, b = color
            dominant.append({"rgb": [int(r), int(g), int(b)], "count": int(count)})

        return dominant
    except Exception:
        return []


def infer_bias_from_colors(dominant_colors: List[Dict[str, Any]]) -> Tuple[str, float]:
    """Compara tons de verde vs vermelho no gráfico."""
    green_score = 0.0
    red_score = 0.0

    for c in dominant_colors:
        r, g, b = c["rgb"]
        weight = c["count"]

        if g > r + 40 and g > b + 40:
            green_score += weight
        elif r > g + 40 and r > b + 40:
            red_score += weight

    total = green_score + red_score
    if total == 0:
        return "NEUTRO", 0.5

    green_ratio = green_score / total
    red_ratio = red_score / total

    if green_ratio > 0.6:
        return "CALL", min(0.7, green_ratio)
    elif red_ratio > 0.6:
        return "PUT", min(0.7, red_ratio)
    return "NEUTRO", 0.5


def detect_trend_from_edges(image: Image.Image) -> Tuple[str, float]:
    """Detecta a inclinação geral das linhas do gráfico."""
    try:
        gray = np.array(image.convert("L"))
        edges = cv2.Canny(gray, 50, 150)

        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=80, minLineLength=50, maxLineGap=15
        )

        if lines is None or len(lines) < 3:
            return "NEUTRO", 0.5

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 != x1:
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                if angle > 90:
                    angle -= 180
                elif angle < -90:
                    angle += 180
                angles.append(angle)

        if not angles:
            return "NEUTRO", 0.5

        avg_angle = np.median(angles)

        # No gráfico y cresce para baixo, então ângulo negativo = alta
        if avg_angle < -5:
            return "CALL", min(0.65, abs(avg_angle) / 45)
        elif avg_angle > 5:
            return "PUT", min(0.65, abs(avg_angle) / 45)
        return "NEUTRO", 0.5
    except Exception:
        return "NEUTRO", 0.5


def analyze_image_locally(image: Image.Image) -> Dict[str, Any]:
    """Análise visual 100% local, sem API."""
    colors = extract_dominant_colors(image)
    color_dir, color_conf = infer_bias_from_colors(colors)
    trend_dir, trend_conf = detect_trend_from_edges(image)

    votes = {"CALL": [], "PUT": [], "NEUTRO": []}
    votes[color_dir].append(("Cor predominante do gráfico", color_conf))
    votes[trend_dir].append(("Inclinação das linhas", trend_conf))

    score_call = sum(w for _, w in votes["CALL"])
    score_put = sum(w for _, w in votes["PUT"])
    total = score_call + score_put

    if total == 0 or abs(score_call - score_put) < 0.1:
        final_dir = "NEUTRO"
        final_conf = 0.5
    elif score_call > score_put:
        final_dir = "CALL"
        final_conf = score_call / total
    else:
        final_dir = "PUT"
        final_conf = score_put / total

    justificativa = (
        f"Análise local: tendência visual {trend_dir.lower()} "
        f"e coloração predominante {color_dir.lower()}."
    )

    return {
        "direcao": final_dir,
        "confianca": round(final_conf, 2),
        "justificativa": justificativa,
        "timeframe_sugerido": "N/A (depende do print)",
        "observacao": "Análise feita localmente sem API de IA.",
        "detalhes": votes,
        "cores_dominantes": colors[:3],
    }


def fuse_signals(
    pattern_signals: List[Tuple[str, str, float]],
    indicator_signals: List[Tuple[str, str, float]],
    vision_result: Dict[str, Any],
) -> Tuple[str, float, Dict[str, List[Tuple[str, float]]]]:
    """Combina sinais de padrões, indicadores e análise visual."""
    votes = {"CALL": [], "PUT": [], "NEUTRO": []}

    for name, direction, weight in pattern_signals + indicator_signals:
        votes[direction].append((name, weight))

    vision_dir = vision_result.get("direcao", "NEUTRO")
    vision_conf = vision_result.get("confianca", 0)
    if vision_dir != "NEUTRO":
        votes[vision_dir].append(("Análise visual local", vision_conf))

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
