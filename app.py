import re

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from indicators import evaluate_all_indicators
from patterns import detect_all_patterns
from utils import analyze_image_locally, extract_text, fuse_signals

st.set_page_config(page_title="Stockity Crypto IDX Analyzer", layout="centered")

# ─── CSS PARA DECORAÇÃO ───
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stApp { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); }
    h1, h2, h3 { color: #00d4ff; text-align: center; }
    .result-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .call { color: #00ff88; font-size: 60px; font-weight: bold; text-shadow: 0 0 20px #00ff88; }
    .put { color: #ff4757; font-size: 60px; font-weight: bold; text-shadow: 0 0 20px #ff4757; }
    .neutro { color: #a4b0be; font-size: 60px; font-weight: bold; }
    .metric-box {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
    }
    .input-section {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h1>📊 Stockity Crypto IDX Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<h3>Sem API — dados reais inseridos manualmente</h3>", unsafe_allow_html=True)

# ─── ENTRADA 1: PRINT DO GRÁFICO ───
st.markdown('<div class="input-section">', unsafe_allow_html=True)
st.subheader("📸 Upload do print do gráfico")
uploaded_file = st.file_uploader("Envie o print da Stockity (Crypto IDX)", type=["png", "jpg", "jpeg"])
st.markdown('</div>', unsafe_allow_html=True)

# ─── ENTRADA 2: CANDLES MANUAIS ───
st.markdown('<div class="input-section">', unsafe_allow_html=True)
st.subheader("🕯️ Dados dos candles")

modo_entrada = st.radio(
    "Como deseja inserir os dados?",
    ["Tabela interativa", "Colar texto (OHLC ou fechamentos)"],
    horizontal=True,
)

ohlc_list = []

if modo_entrada == "Tabela interativa":
    st.write("Preencha os candles do mais antigo (topo) para o mais recente (final):")

    default_data = {
        "open": [100.0] * 10,
        "high": [100.5] * 10,
        "low": [99.5] * 10,
        "close": [100.2] * 10,
    }
    df_editor = pd.DataFrame(default_data)
    df = st.data_editor(
        df_editor,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "open": st.column_config.NumberColumn("Abertura", help="Preço de abertura"),
            "high": st.column_config.NumberColumn("Máxima", help="Preço máximo"),
            "low": st.column_config.NumberColumn("Mínima", help="Preço mínimo"),
            "close": st.column_config.NumberColumn("Fechamento", help="Preço de fechamento"),
        },
    )

    for _, row in df.iterrows():
        if pd.notna(row["open"]) and pd.notna(row["high"]) and pd.notna(row["low"]) and pd.notna(row["close"]):
            ohlc_list.append(
                {
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                }
            )

else:
    st.write(
        "Cole os valores. Você pode usar **OHLC separado por vírgula** ou **apenas fechamentos**, um por linha."
    )
    st.code(
        """Exemplo OHLC:
100.0, 100.5, 99.8, 100.2
100.2, 100.9, 100.1, 100.7

Exemplo apenas fechamentos:
100.2
100.7
101.1""",
        language="text",
    )

    texto_candles = st.text_area("Cole aqui os candles", height=150)

    if texto_candles.strip():
        linhas = [linha.strip() for linha in texto_candles.split("\n") if linha.strip()]
        for linha in linhas:
            partes = re.split(r"[,\s\t]+", linha)
            partes = [p for p in partes if p]

            try:
                valores = [float(p.replace(",", ".")) for p in partes]
            except ValueError:
                continue

            if len(valores) == 4:
                o, h, l, c = valores
                ohlc_list.append({"open": o, "high": h, "low": l, "close": c})
            elif len(valores) == 1:
                c = valores[0]
                ohlc_list.append({"open": c, "high": c, "low": c, "close": c})
            else:
                continue

st.markdown('</div>', unsafe_allow_html=True)

# ─── BOTÃO DE ANÁLISE ───
analisar = st.button("🔍 ANALISAR AGORA", use_container_width=True)

if analisar:
    if len(ohlc_list) < 5:
        st.error("⚠️ Insira pelo menos 5 candles para fazer a análise técnica.")
        st.stop()

    if uploaded_file:
        image = Image.open(uploaded_file)
    else:
        image = None

    with st.spinner("Analisando dados e imagem..."):
        # Análise visual do print
        vision_result = {
            "direcao": "NEUTRO",
            "confianca": 0.5,
            "justificativa": "Nenhum print enviado.",
        }
        extracted_text = ""

        if image:
            extracted_text = extract_text(image)
            vision_result = analyze_image_locally(image)
            st.image(image, caption="Print do gráfico", use_container_width=True)

        # Dados reais dos candles
        closes = [c["close"] for c in ohlc_list]

        pattern_signals = detect_all_patterns(ohlc_list)
        indicator_signals = evaluate_all_indicators(closes)
        final_dir, confidence, votes = fuse_signals(pattern_signals, indicator_signals, vision_result)

    # ─── RESULTADO PRINCIPAL ───
    css_class = final_dir.lower()
    st.markdown(
        f"""
        <div class="result-card">
            <h2>Sinal Recomendado</h2>
            <div class="{css_class}">{final_dir}</div>
            <h3>Confiança: {confidence:.0%}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─── MÉTRICAS ───
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f'<div class="metric-box"><h4>Análise Visual</h4><h2>{vision_result["direcao"]}</h2></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="metric-box"><h4>Confiança Visual</h4><h2>{vision_result["confianca"]:.0%}</h2></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="metric-box"><h4>Candles Reais</h4><h2>{len(ohlc_list)}</h2></div>',
            unsafe_allow_html=True,
        )

    st.write("**🧠 Justificativa:**", vision_result["justificativa"])
    st.write("**📝 Texto extraído do print:**", extracted_text or "Nenhum")

    # ─── TABELA DE CANDLES ───
    with st.expander("📋 Candles utilizados na análise"):
        st.dataframe(pd.DataFrame(ohlc_list), use_container_width=True)

    # ─── PADRÕES ───
    with st.expander("🕯️ Padrões de candle detectados"):
        if pattern_signals:
            for name, direction, weight in pattern_signals:
                st.write(f"- **{name}** → {direction}")
        else:
            st.write("Nenhum padrão clássico detectado nos candles fornecidos.")

    # ─── INDICADORES ───
    with st.expander("📈 Sinais dos indicadores técnicos"):
        if indicator_signals:
            for name, direction, weight in indicator_signals:
                st.write(f"- **{name}** → {direction}")
        else:
            st.write("Indicadores sem sinal claro com os dados atuais.")

    # ─── VOTOS ───
    with st.expander("🗳️ Votos combinados"):
        st.json(votes)

    st.warning(
        "⚠️ Ferramenta de análise técnica apenas. Não é recomendação de investimento. "
        "Opções binárias envolvem alto risco de perda total do capital."
    )
else:
    st.info("👆 Envie um print e/ou insira os candles, depois clique em **ANALISAR AGORA**.")
