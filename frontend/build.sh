#!/bin/bash

# Frontend build script for Render deployment

echo "🚀 Starting NourishAI Frontend Build..."

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Build the application
echo "🔨 Building application..."
npm run build

# Check if build was successful
if [ -d "dist" ]; then
    echo "✅ Build successful! Output directory: dist"
    echo "📁 Build contents:"
    ls -la dist/
else
    echo "❌ Build failed! No dist directory found."
    exit 1
fi

echo "🎉 Frontend build complete!"
