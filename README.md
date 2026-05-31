# Social Autopublisher

Automatic scraping and multi-platform social media publishing for product links.

## Features (Phase 1 MVP)

- **Scrapers**: Mercado Libre (API-based)
- **Publishers**: Twitter/X, Facebook
- **Scheduler**: Railway Cron (3x daily)
- **Database**: PostgreSQL + Redis (Railway)

## Setup

1. Clone repo
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in credentials
4. `alembic upgrade head` to create DB schema
5. `python -m app.run_pipeline` to test locally

## Environment Variables

See `.env.example` for all required credentials:
- **Mercado Libre**: Client ID, Secret, Refresh Token
- **Twitter/X**: Bearer Token
- **Meta (IG+FB)**: Long-lived Access Token, Page ID

## Deployment (Railway)

1. Create Railway project
2. Add Postgres plugin
3. Add Redis plugin
4. Configure cron job: `0 9,15,21 * * * python -m app.run_pipeline`
5. Push to GitHub (Railway auto-deploys)

## Future Phases

- Phase 2: Instagram (media hosting required)
- Phase 3: Amazon PA-API
- Phase 4: TikTok (video generation)
- Phase 5: Advanced hardening & token refresh
