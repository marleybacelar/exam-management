# Deployment & Remote Access Guide

## 🌐 Accessing the App Beyond Localhost

### Option 1: Local Network Access (Easiest)

Run Streamlit with network access enabled:

```bash
streamlit run app.py --server.address=0.0.0.0
```

Then access from any device on your network:
```
http://YOUR_LOCAL_IP:8501
```

**Find your local IP:**
- **macOS/Linux:** `ifconfig | grep inet`
- **Windows:** `ipconfig`

Example: If your IP is `192.168.1.100`, access at `http://192.168.1.100:8501`

---

### Option 2: Custom Port

If port 8501 is blocked, use a different port:

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8080
```

Access at: `http://YOUR_LOCAL_IP:8080`

---

### Option 3: Cloud Deployment

#### A. Streamlit Community Cloud (Free)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/exam-management.git
   git push -u origin main
   ```

2. **Deploy:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Click "Deploy"

3. **Access:** Your app will be at `https://YOUR_APP.streamlit.app`

#### B. Heroku (Free Tier Available)

1. **Create `Procfile`:**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Create `setup.sh`:**
   ```bash
   mkdir -p ~/.streamlit/
   echo "\
   [server]\n\
   headless = true\n\
   port = $PORT\n\
   enableCORS = false\n\
   \n\
   " > ~/.streamlit/config.toml
   ```

3. **Deploy:**
   ```bash
   heroku login
   heroku create your-exam-app
   git push heroku main
   ```

#### C. Docker Deployment

1. **Create `Dockerfile`:**
   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8501
   
   CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
   ```

2. **Build and run:**
   ```bash
   docker build -t exam-app .
   docker run -p 8501:8501 exam-app
   ```

#### D. AWS EC2

1. **Launch EC2 instance** (t2.micro for free tier)
2. **SSH into instance:**
   ```bash
   ssh -i your-key.pem ec2-user@YOUR_EC2_IP
   ```

3. **Install dependencies:**
   ```bash
   sudo yum update -y
   sudo yum install python3-pip -y
   git clone your-repo
   cd exam-management
   pip3 install -r requirements.txt
   ```

4. **Run with screen:**
   ```bash
   screen -S streamlit
   streamlit run app.py --server.address=0.0.0.0 --server.port=8501
   # Press Ctrl+A then D to detach
   ```

5. **Access:** `http://YOUR_EC2_IP:8501`
   - Make sure port 8501 is open in Security Group

---

## 🔒 Security Considerations

### For Local Network Access:
- Only devices on your local network can access
- Relatively safe for home/office use

### For Internet Access:
1. **Add Authentication:**
   ```python
   # Add to app.py
   import streamlit_authenticator as stauth
   
   # Configure authentication
   authenticator = stauth.Authenticate(
       config,
       'exam_app',
       'exam_key',
       cookie_expiry_days=30
   )
   
   name, authentication_status, username = authenticator.login('Login', 'main')
   ```

2. **Use HTTPS:**
   - Set up SSL certificate (Let's Encrypt)
   - Use reverse proxy (nginx)

3. **Environment Variables:**
   ```bash
   # Store sensitive data in .env
   export DATA_DIR=/secure/path/data
   ```

4. **Firewall Rules:**
   ```bash
   # Only allow specific IPs
   sudo ufw allow from YOUR_IP to any port 8501
   ```

---

## 📝 Quick Start Commands

### Development (Local Only):
```bash
streamlit run app.py
# Access: http://localhost:8501
```

### Local Network:
```bash
streamlit run app.py --server.address=0.0.0.0
# Access: http://YOUR_LOCAL_IP:8501
```

### Production (with config):
```bash
streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port=8501 \
  --server.headless=true \
  --server.fileWatcherType=none
```

---

## 🔧 Configuration File

Create `.streamlit/config.toml`:

```toml
[server]
address = "0.0.0.0"
port = 8501
headless = true
enableCORS = false
maxUploadSize = 200

[browser]
serverAddress = "YOUR_DOMAIN_OR_IP"
serverPort = 8501

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

Run with config:
```bash
streamlit run app.py
```

---

## 🌍 Recommended Setup for Different Use Cases

### Personal Use (Home):
- Use local network access
- No authentication needed
- `streamlit run app.py --server.address=0.0.0.0`

### Team Use (Office):
- Deploy to company server
- Add basic authentication
- Use internal network IP

### Public/Production:
- Deploy to Streamlit Cloud (easiest)
- Or use Docker on cloud provider
- Must add authentication
- Use HTTPS

---

## ⚠️ Important Notes

1. **Data Persistence:**
   - Local files in `data/` directory
   - Cloud deployments may need external storage (S3, etc.)
   - Consider database for production

2. **File Upload Limits:**
   - Default Streamlit limit: 200MB
   - Increase in config if needed

3. **Memory Management:**
   - Free tiers have memory limits
   - Large PDFs may cause issues
   - Consider file size limits

4. **Cost:**
   - Streamlit Cloud: Free (public repos)
   - Heroku: Free tier available
   - AWS EC2: t2.micro free for 12 months
   - After that, ~$10-50/month depending on usage

---

## 🎯 Recommended: Streamlit Community Cloud

**Best for this application:**
- Free hosting
- Easy deployment
- Automatic SSL
- GitHub integration
- No server maintenance

**Steps:**
1. Push code to GitHub
2. Deploy on share.streamlit.io
3. Access via public URL
4. **Note:** Your data will be public unless you add authentication

Would you like help setting up any of these deployment options?
