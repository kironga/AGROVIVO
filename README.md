# Agrofields Planet / AgroVivo

Django 5+ storefront starter for Agrofields Planet Ltd. The brief supplied two incompatible stacks; this implementation follows the all-Python Django brief. It uses SQLite locally and accepts PostgreSQL through DATABASE_URL.

## Run locally

1. Create a virtual environment and install `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`; set a private SECRET_KEY for any shared environment.
3. Run `python manage.py migrate`, `python manage.py seed_products`, and `python manage.py createsuperuser`.
4. Start with `python manage.py runserver`. Visit /, /products/, /crop-programmes/, /cart/ and /admin/.

All 11 product prices are illustrative KES placeholders. Confirm prices, stock, application guidance, product registration and technical sheets with Agrofields before accepting live orders.

## Included now

Responsive corporate and catalogue pages, 11-product and seven-crop seed command, Django admin, session cart, validated checkout, stock checks, order records, customer login/order history, contact form, sitemap and robots endpoint, WhatsApp CTA, Dockerfile and environment template. M-Pesa is simulated only in DEBUG. Production payment endpoints deliberately return unavailable until a real Daraja STK client and Stripe Checkout/webhook verification are configured. The Render start command ensures missing seed catalog records are created at startup without overwriting existing catalog edits; use `python manage.py seed_products --force` to reapply seed values intentionally.

## Frontend image assets

Place farm imagery in `static/images/farm-photos/`, product imagery in `static/images/product-photos/`, and the company mark at `static/images/logo/logo.jfif`. The current storefront uses the supplied farm and product photos. Product image associations are set by `catalog/management/commands/seed_products.py`; rerun `python manage.py seed_products` after changing those associations. The responsive storefront includes a mobile navigation menu, animated section reveals, live product search, crop-stage filtering and quick add-to-cart feedback.

## Production setup before launch

Set DEBUG=False, SECRET_KEY, ALLOWED_HOSTS and PostgreSQL DATABASE_URL. Configure RESEND_API_KEY and DEFAULT_FROM_EMAIL. Set Daraja credentials and a public HTTPS callback URL, then implement and verify the Daraja OAuth/STK Push and callback signing/validation path. Implement Stripe Checkout Session creation and verify webhook signatures with STRIPE_WEBHOOK_SECRET. Configure domain and sitemap URL, review security headers/rate limiting, product images/storage, county delivery operations, legal pages, and payment reconciliation. The current app has no live card or live M-Pesa processing.

`docker compose up` is not configured; build and run the included Dockerfile with your deployment platform's database and environment variables.

## Free preview deployment (Render + Neon)

The repository includes `render.yaml` for a free Render Django web service. Create a Neon Postgres project, copy its pooled connection string (it should include `sslmode=require`), then connect this repository in Render using **New → Blueprint**. Render will ask for `DATABASE_URL`; paste the Neon connection string. The Blueprint generates `SECRET_KEY`, collects static files, runs migrations, checks `/healthz`, and seeds the catalog once after the first deploy. Use the resulting `https://agrofields-planet.onrender.com` address to preview the site. Add `RESEND_API_KEY` and `DEFAULT_FROM_EMAIL` in Render if email delivery is needed.

This free setup is for a preview, not reliable commerce: Render free web services sleep after 15 minutes of inactivity and take about a minute to wake, and their filesystem is temporary. Neon is the persistent database; do not use SQLite or store customer uploads on Render. Neon currently offers 1 GB storage per free project; watch its compute allowance in the Neon console. Avoid Render's own free Postgres for this setup because new free Render databases expire after 30 days.

Vercel can deploy Django full-stack, but Vercel Hobby is restricted to personal, non-commercial use. This is a company storefront, so do not deploy its public business site on a free Hobby account. Running this Django app on Vercel would also duplicate the Render web service. Use Render + Neon for the free preview; consider Vercel only with a suitable paid business plan or for a separate non-commercial personal demo.
