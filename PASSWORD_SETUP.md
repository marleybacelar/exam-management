# 🔒 Password Protection Setup Guide

Your Exam Management System now has built-in password protection using environment variables.

## How It Works

- The app checks for an environment variable called `APP_PASSWORD`
- If `APP_PASSWORD` is not set, the app is **publicly accessible** (no password required)
- If `APP_PASSWORD` is set, users must enter the correct password to access the app
- Once authenticated, users remain logged in for the session

## Local Development Setup

### Option 1: Using Environment Variable

```bash
export APP_PASSWORD="your-secure-password"
streamlit run app.py
```

### Option 2: Using .env File (Recommended for local dev)

1. Create a `.env` file in your project root:
```bash
APP_PASSWORD=your-secure-password
```

2. Run with environment variables:
```bash
export $(cat .env | xargs) && streamlit run app.py
```

**Note:** The `.env` file is already in `.gitignore` and won't be committed to Git.

## Streamlit Cloud Deployment Setup

### Step 1: Deploy Your App

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select:
   - Repository: `marleybacelar/exam-management`
   - Branch: `main`
   - Main file path: `app.py`

### Step 2: Configure Password Protection

1. Before deploying, click on **"Advanced settings"**
2. In the **"Secrets"** section, add your environment variable:

```toml
APP_PASSWORD = "your-secure-password-here"
```

3. Click "Deploy!"

### Alternative: Add Password After Deployment

1. Go to your deployed app dashboard
2. Click on the app settings (⚙️)
3. Navigate to "Secrets"
4. Add:
```toml
APP_PASSWORD = "your-secure-password-here"
```
5. Click "Save"
6. The app will automatically restart with password protection enabled

## Security Best Practices

✅ **DO:**
- Use a strong, unique password (minimum 12 characters)
- Include uppercase, lowercase, numbers, and special characters
- Keep your password secret and don't share it publicly
- Change the password periodically
- Use different passwords for different deployments (dev, staging, production)

❌ **DON'T:**
- Hard-code passwords in your source code
- Commit passwords to Git
- Use simple passwords like "password123"
- Share passwords via insecure channels

## Example Strong Passwords

Generate strong passwords using:
```bash
# macOS/Linux
openssl rand -base64 20

# Or use an online generator (make sure it's a reputable site)
```

Example format: `Xk9#mP2$vL8@qR5!nT7`

## Removing Password Protection

To make your app public again:

### Streamlit Cloud:
1. Go to app settings
2. Remove the `APP_PASSWORD` secret
3. Save and restart

### Local Development:
Simply don't set the `APP_PASSWORD` environment variable.

## Testing

### With Password:
```bash
export APP_PASSWORD="test123"
streamlit run app.py
# You should see a login screen
```

### Without Password:
```bash
unset APP_PASSWORD
streamlit run app.py
# App should load directly without login
```

## Troubleshooting

### "Password incorrect" even with correct password
- Check for extra spaces in your environment variable
- Verify the password is exactly as you set it (case-sensitive)
- Restart the Streamlit app after changing the password

### Can't access app after setting password
- Double-check your `APP_PASSWORD` value in Streamlit Cloud secrets
- Make sure there are no syntax errors in the secrets TOML
- Wait a few seconds for the app to restart after changing secrets

### Want to reset password
- Simply update the `APP_PASSWORD` value in your secrets
- The app will automatically restart and use the new password

## Current Setup

Your code is now live at:
**Repository:** https://github.com/marleybacelar/exam-management

When you deploy to Streamlit Cloud and set `APP_PASSWORD`, only users with the correct password will be able to access your exam management system.
