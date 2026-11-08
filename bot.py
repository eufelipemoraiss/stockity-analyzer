import re
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import TOKEN
from indicators import evaluate_all_indicators
from patterns import detect_all_patterns
from utils import fuse_signals

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def parse_candles(text: str):
    """
    Aceita:
    - OHLC separado por vírgula, espaço ou tab (um candle por linha)
    - Apenas fechamentos (um por linha)
    """
    candles = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        parts = re.split(r"[,\s\t]+", line)
        parts = [p.strip().replace(",", ".") for p in parts if p.strip()]

        try:
            values = [float(p) for p in parts]
        except ValueError:
            continue

        if len(values) == 4:
            o, h, l, c = values
            candles.append({"open": o, "high": h, "low": l, "close": c})
        elif len(values) == 1:
            c = values[0]
            candles.append({"open": c, "high": c, "low": c, "close": c})

    return candles


def build_result_message(final_dir: str, confidence: float, pattern_signals, indicator_signals, votes):
    icon = "📈" if final_dir == "CALL" else "📉" if final_dir == "PUT" else "⚖️"
    msg = f"{icon} *SINAL: {final_dir}*\n"
    msg += f"🎯 Confiança: {confidence:.0%}\n\n"

    if pattern_signals:
        msg += "*🕯️ Padrões detectados:*\n"
        for name, direction, _ in pattern_signals:
            msg += f"• {name} → {direction}\n"
        msg += "\n"

    if indicator_signals:
        msg += "*📊 Indicadores:*\n"
        for name, direction, _ in indicator_signals:
            msg += f"• {name} → {direction}\n"
        msg += "\n"

    if votes["CALL"]:
        msg += "*✅ Votos CALL:*\n"
        for name, weight in votes["CALL"]:
            msg += f"• {name} ({weight:.0%})\n"
        msg += "\n"

    if votes["PUT"]:
        msg += "*❌ Votos PUT:*\n"
        for name, weight in votes["PUT"]:
            msg += f"• {name} ({weight:.0%})\n"

    msg += "\n⚠️ *Aviso:* isso é análise técnica, não recomendação de investimento."
    return msg


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Stockity Analyzer no Telegram*\n\n"
        "Envie os dados dos candles no formato:\n"
        "`abertura, máxima, mínima, fechamento`\n\n"
        "Exemplo:\n"
        "```\n"
        "100.0, 100.5, 99.8, 100.2\n"
        "100.2, 100.9, 100.1, 100.7\n"
        "100.7, 101.2, 100.6, 101.0\n"
        "```\n\n"
        "Ou envie apenas os fechamentos, um por linha.\n"
        "Mínimo: 5 candles.",
        parse_mode="Markdown",
    )


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    candles = parse_candles(text)

    if len(candles) < 5:
        await update.message.reply_text(
            "⚠️ Envie pelo menos 5 candles válidos.\n\n"
            "Use o formato:\n"
            "`abertura, máxima, mínima, fechamento`",
            parse_mode="Markdown",
        )
        return

    closes = [c["close"] for c in candles]
    pattern_signals = detect_all_patterns(candles)
    indicator_signals = evaluate_all_indicators(closes)
    final_dir, confidence, votes = fuse_signals(pattern_signals, indicator_signals)

    msg = build_result_message(
        final_dir, confidence, pattern_signals, indicator_signals, votes
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Comandos:*\n"
        "/start — inicia o bot\n"
        "/help — mostra esta ajuda\n\n"
        "Basta enviar os candles que eu retorno o sinal.",
        parse_mode="Markdown",
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Erro: {context.error}")


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze))
    application.add_error_handler(error_handler)

    logger.info("Bot iniciado.")
    application.run_polling()


if __name__ == "__main__":
    main()
