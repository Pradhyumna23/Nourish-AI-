# 🚀 NourishAI Deployment Guide - Render

This guide will help you deploy NourishAI to Render, a modern cloud platform for hosting web applications.

## 📋 Prerequisites

Before deploying, ensure you have:

- ✅ **GitHub repository** with your code
- ✅ **MongoDB Atlas** database (cloud database)
- ✅ **Gemini API key** from Google AI Studio
- ✅ **USDA API key** from FoodData Central
- ✅ **Render account** (free tier available)

## 🌐 Deployment Steps

### **Step 1: Prepare Your Repository**

1. **Ensure all files are committed** to your GitHub repository
2. **Verify environment variables** are not hardcoded
3. **Check that render.yaml** is in the root directory

### **Step 2: Create Render Account**

1. Go to [render.com](https://render.com)
2. **Sign up** using your GitHub account
3. **Authorize Render** to access your repositories

### **Step 3: Deploy Backend Service**

1. **Click "New +"** in Render dashboard
2. **Select "Web Service"**
3. **Connect your GitHub repository**: `Nourish-AI-`
4. **Configure the service**:
   - **Name**: `nourishai-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && python mongodb_main.py`
   - **Plan**: `Free` (or upgrade as needed)

### **Step 4: Configure Environment Variables**

In the Render dashboard for your backend service, add these environment variables:

```env
MONGODB_URL=your_mongodb_atlas_connection_string
GEMINI_API_KEY=your_gemini_api_key
USDA_API_KEY=your_usda_api_key
JWT_SECRET_KEY=your_strong_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=false
```

### **Step 5: Deploy Frontend Service**

1. **Click "New +"** again
2. **Select "Static Site"**
3. **Connect the same repository**
4. **Configure the static site**:
   - **Name**: `nourishai-frontend`
   - **Build Command**: `cd frontend && npm ci && npm run build`
   - **Publish Directory**: `frontend/dist`
   - **Plan**: `Free`

### **Step 6: Configure Frontend Environment**

Add this environment variable to your frontend service:

```env
VITE_API_URL=https://your-backend-service-url.onrender.com/api/v1
```

Replace `your-backend-service-url` with the actual URL of your deployed backend.

## 🔧 Configuration Details

### **Backend Configuration**

The backend is configured to:
- ✅ **Auto-detect port** from Render's PORT environment variable
- ✅ **Handle CORS** for Render domains
- ✅ **Health check** endpoint at `/health`
- ✅ **Production optimizations** (no reload, proper logging)

### **Frontend Configuration**

The frontend is configured to:
- ✅ **Build with Vite** for optimal performance
- ✅ **Use environment variables** for API URL
- ✅ **Static file serving** with proper routing
- ✅ **SPA routing** support

## 🌟 Post-Deployment

### **Verify Deployment**

1. **Backend Health Check**: Visit `https://your-backend-url.onrender.com/health`
2. **Frontend Application**: Visit `https://your-frontend-url.onrender.com`
3. **API Documentation**: Visit `https://your-backend-url.onrender.com/docs`

### **Test Core Features**

1. ✅ **User Registration/Login**
2. ✅ **Food Search** (USDA integration)
3. ✅ **AI Recommendations** (Gemini integration)
4. ✅ **Food Logging**
5. ✅ **Chatbot** (authenticated users)

## 🔒 Security Considerations

### **Environment Variables**
- ✅ **Never commit** real API keys to repository
- ✅ **Use Render's environment** variable system
- ✅ **Rotate secrets** regularly

### **Database Security**
- ✅ **MongoDB Atlas** with authentication
- ✅ **Network access** restricted to Render IPs
- ✅ **Connection string** in environment variables

## 🚨 Troubleshooting

### **Common Issues**

#### **Backend Won't Start**
- Check environment variables are set correctly
- Verify MongoDB connection string
- Check build logs for Python dependency issues

#### **Frontend Build Fails**
- Ensure Node.js version compatibility
- Check for missing dependencies
- Verify build command path

#### **CORS Errors**
- Ensure frontend URL is added to CORS origins
- Check that API URL is correctly configured

#### **Database Connection Issues**
- Verify MongoDB Atlas connection string
- Check network access settings in Atlas
- Ensure database user has proper permissions

### **Logs and Monitoring**

- **Backend Logs**: Available in Render dashboard
- **Frontend Build Logs**: Check during deployment
- **Health Monitoring**: Use `/health` endpoint

## 📈 Scaling and Optimization

### **Performance Tips**
- ✅ **Use CDN** for static assets
- ✅ **Enable compression** in production
- ✅ **Monitor response times**
- ✅ **Optimize database queries**

### **Scaling Options**
- **Upgrade Render plan** for more resources
- **Use Redis** for caching (additional service)
- **Implement rate limiting** for API protection

## 💰 Cost Considerations

### **Free Tier Limits**
- **Backend**: 750 hours/month (sleeps after 15 min inactivity)
- **Frontend**: Unlimited bandwidth
- **Database**: MongoDB Atlas free tier (512MB)

### **Upgrade Benefits**
- **No sleep** for paid services
- **More resources** (CPU, memory)
- **Custom domains**
- **Advanced monitoring**

## 🎉 Success!

Once deployed, your NourishAI application will be:
- ✅ **Publicly accessible** via HTTPS
- ✅ **Automatically updated** when you push to GitHub
- ✅ **Scalable** and production-ready
- ✅ **Secure** with proper environment variable handling

**Live URLs**:
- **Frontend**: `https://your-frontend-name.onrender.com`
- **Backend API**: `https://your-backend-name.onrender.com`
- **API Docs**: `https://your-backend-name.onrender.com/docs`

---

**Need Help?** Check the [Render Documentation](https://render.com/docs) or create an issue in the repository.
