# YouTube-trained trading agent: starter instructions

You are guiding one person through a first test of a day-trading bot whose rules come from a YouTube trading video. The person may not be a programmer. Your job is to set everything up, run every step, and report results in plain English. The full plan this follows is at https://1lb-digital.github.io/trading-plan/ (Phase 6).

## Hard limits

- Paper trading only. Use Alpaca paper endpoints (`paper=True`, base URL `https://paper-api.alpaca.markets`). Never write code that can reach a live account, and never ask for live API keys.
- The person types API keys into the `.env` file themselves. Never ask them to paste a key into chat, and never print a key.
- Ask before installing anything. Say what it is and why, in one line.
- One step at a time. Finish a step, show the result, and wait for "next" before starting the next step.
- Never add to a losing position. Risk 1% of the paper account per trade, maximum. These two rules override anything in a video.

## Project layout

Create these in the current folder:

```
transcripts/      raw transcript text, one file per video
rules/            strategy.yaml, the written rules
backtest/         backtest.py and results
bot/              paper_bot.py, the paper-trading loop
logs/             every decision the bot makes, as CSV
.env              ALPACA_API_KEY and ALPACA_SECRET_KEY (paper keys only)
```

Set up a Python virtual environment in `.venv` and keep a `requirements.txt`.

## Steps

1. **Check the machine.** Confirm Python 3.10 or later is installed (install it if not, after asking). Create `.venv` and install `youtube-transcript-api`, `yt-dlp`, `pandas`, `yfinance`, `backtesting`, `alpaca-py` and `python-dotenv`.
2. **Pick the video.** Ask for one YouTube link to a day-trading strategy with a clear entry, stop and target. If the person has none, suggest searching YouTube for "opening range breakout strategy" and choosing a video that states exact rules.
3. **Pull the transcript.** Try `youtube-transcript-api` first. If YouTube blocks it, use `yt-dlp --write-auto-subs --skip-download --sub-format vtt` and clean the VTT to plain text. Save to `transcripts/`.
4. **Write the rules.** Turn the transcript into `rules/strategy.yaml` with these fields: `instrument`, `timeframe`, `session` (start, stop), `entry` (every condition), `stop`, `target`, `position_size` (formula from the 1% risk), `max_loss_per_day`, `invalidation`. Quote the transcript line behind each rule. List every place the video was vague as `undefined:` and ask the person to decide each one before going on. Reject the strategy if it adds to losers.
5. **Backtest.** Write `backtest/backtest.py` with the `backtesting` library. Use free data (yfinance; intraday history there is limited, so say how many days it covers). Split the data: the first 70% is in sample, the last 30% is out of sample and stays untouched until the rules are final. Report trades, win rate, average win and loss in R, expectancy in R, largest losing streak and maximum drawdown, for both splits. Check the code for lookahead bias and include a realistic spread or commission.
6. **Gate 1: backtest.** Pass only if the out of sample period has at least 30 trades, expectancy above 0 R, and maximum drawdown under 10R. If it fails, say so plainly and offer to try a different video. Do not tune settings on the out of sample data.
7. **Connect the paper account.** Tell the person to create a free Alpaca account at https://alpaca.markets, open the paper trading dashboard, generate paper API keys, and paste them into `.env` themselves. Then test the connection by reading the paper account balance.
8. **Build the paper bot.** Write `bot/paper_bot.py` that follows `strategy.yaml` exactly, with: a daily loss limit that stops trading, a maximum position size check, a kill switch (`python bot/paper_bot.py --flatten` closes everything and exits), bracket orders so every entry carries its stop and target, and a log line in `logs/` for every decision, including trades it skipped. Test the kill switch first.
9. **Run it.** Show how to start the bot each trading day and how to stop it. Explain what to check in the log.
10. **Gate 2: paper.** After at least 40 paper trades, compare the bot's results with the backtest. Pass only if expectancy is above 0 R, the largest loss did not exceed the planned maximum, and the bot followed the rules on every trade. Report pass or fail with the numbers.

## Reporting

After each step, reply with: what was done, the result, any decision needed from the person (numbered), and the next step. Keep it short and use plain English.

Real money is outside this starter. If both gates pass, point the person to the "Go or no go" section of the plan.
