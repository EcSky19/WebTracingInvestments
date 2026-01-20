# WebTracingInvestment

Social sentiment analysis for stock market research. Tracks keywords and sentiment across Reddit and Threads to monitor public opinion on companies.

## Features

- 📊 **Sentiment Tracking**: Real-time sentiment analysis of social posts mentioning tracked stocks
- 🔍 **Keyword Detection**: Automatic detection of company mentions and ticker symbols
- 📈 **Aggregation**: Hourly sentiment aggregation and trending
- 🌐 **Multi-source**: Reddit and Threads integration (Threads pending API access)
- 📱 **REST API**: Query sentiment data, posts, and distributions
- 🔄 **Background Jobs**: Scheduled ingestion every 5 minutes

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required for Reddit ingestion:
- `REDDIT_CLIENT_ID` - Get from https://www.reddit.com/prefs/apps
- `REDDIT_CLIENT_SECRET` - From same location
- `REDDIT_USER_AGENT` - Custom user agent (e.g., `WebTracingInvestment/0.1.0`)

Optional for Threads:
- `THREADS_ACCESS_TOKEN` - Meta Graph API token
- `THREADS_USER_ID` - Your Threads user ID

### 3. Run the Server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The server will:
- Initialize the SQLite database
- Start the background scheduler (ingests every 5 minutes)
- Listen for API requests

## API Endpoints

### View All Tracked Stocks

```bash
curl http://localhost:8000/sentiment/stocks?hours=24
```

Response:
```json
[
  {
    "symbol": "TSLA",
    "total_posts": 45,
    "avg_sentiment": 0.32,
    "most_recent_post": "2026-01-16T10:30:00Z"
  }
]
```

### Get Sentiment Distribution for a Stock

```bash
curl http://localhost:8000/sentiment/distribution/TSLA?hours=24
```

Response:
```json
{
  "symbol": "TSLA",
  "very_negative": 2,
  "negative": 8,
  "neutral": 15,
  "positive": 20,
  "very_positive": 5,
  "total_posts": 50,
  "avg_sentiment": 0.32
}
```

### Get Recent Posts for a Symbol

```bash
curl http://localhost:8000/posts/TSLA?limit=10
```

### View Hourly Sentiment Trends

```bash
curl http://localhost:8000/sentiment/hourly?symbol=TSLA&hours=24
```

### Interactive Docs

Visit `http://localhost:8000/docs` for Swagger UI with all endpoints.

## Architecture

```
app/
├── core/          # Logging, symbols database
├── ingest/        # Reddit, Threads adapters
├── nlp/           # Sentiment & entity extraction
├── db/            # Database models, session
├── services/      # Pipeline, aggregation
├── jobs/          # Scheduler, background tasks
├── api/           # Routes, schemas
└── main.py        # App entry point
```

## Data Flow

1. **Ingest** - Reddit/Threads adapters fetch new posts every 5 minutes
2. **Process** - Posts cleaned, symbols detected, sentiment scored
3. **Store** - Posts saved to database with metadata
4. **Aggregate** - Hourly sentiment buckets computed
5. **Query** - REST API exposes sentiment data

## Tracked Symbols

Currently tracking ~15 major stocks (TSLA, AAPL, NVDA, MSFT, etc.). Add more in `app/core/symbols.py`.

## Sentiment Scale

- **-1.0 to -0.6** - Very negative
- **-0.6 to -0.2** - Negative  
- **-0.2 to 0.2** - Neutral
- **0.2 to 0.6** - Positive
- **0.6 to 1.0** - Very positive

Uses VADER sentiment analyzer (upgradeable to FinBERT for finance-specific scoring).

## Next Steps

- [ ] Add stock price ingestion (yfinance)
- [ ] Implement correlation analysis (sentiment vs price)
- [ ] Upgrade to FinBERT sentiment model
- [ ] Add Threads API integration
- [ ] Build dashboard UI
- [ ] Add alerts for sentiment spikes
