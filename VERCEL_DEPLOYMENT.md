# Vercel Deployment Guide

## Files Created for Vercel Deployment

1. `/api/webhook.py` - Handles incoming webhook requests from Telegram
2. `/api/cron.py` - Scheduled task that checks traffic conditions and notifies subscribers
3. `/vercel.json` - Vercel configuration including cron jobs

## Steps to Deploy Your Bot on Vercel

### 1. Push Your Code to GitHub

Make sure your repository includes:
- All the files we've created
- Your `requirements.txt`
- The `.env` file (but don't commit it, keep it in .gitignore)

### 2. Create a New Project on Vercel

- Go to [Vercel](https://vercel.com/)
- Create an account or sign in
- Create a new project and import your GitHub repository

### 3. Configure Environment Variables

In your Vercel project settings, add these environment variables:

- `TELEBOT_TOKEN` - Your Telegram bot token
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase API key
- `TUAS_CHECKPOINT_URL` - URL for the Tuas checkpoint image
- `WOODLANDS_CHECKPOINT_URL` - URL for the Woodlands checkpoint image 
- `WEBHOOK_URL` - The URL of your Vercel deployment + `/api/webhook`

### 4. Deploy Your Bot

- Vercel should automatically deploy your bot

### 5. Set Up the Telegram Webhook

After deployment is complete, register your webhook with Telegram by visiting:

```
https://api.telegram.org/bot{YOUR_BOT_TOKEN}/setWebhook?url={YOUR_VERCEL_DEPLOYMENT_URL}/api/webhook
```

Replace `{YOUR_BOT_TOKEN}` with your actual bot token and `{YOUR_VERCEL_DEPLOYMENT_URL}` with your Vercel deployment URL.

## Additional Notes

1. Vercel has limitations for serverless functions (memory, execution time). If you hit these limits, you might need to optimize your code or consider other hosting options.

2. Tesseract OCR might have issues in serverless environments. If OCR isn't working properly, consider:
   - Using a cloud OCR service instead
   - Pre-processing images more aggressively 
   - Switching to a different hosting solution

3. You need to create a table in Supabase to store the latest checkpoint times:
   ```sql
   CREATE TABLE checkpoint_times (
     id SERIAL PRIMARY KEY,
     checkpoint TEXT NOT NULL,
     time TEXT
   );
   ```

4. Enable appropriate RLS policies for both tables in Supabase.
