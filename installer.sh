#!/bin/bash

# script to set up FFmpeg in a GitHub Codespace
set -e

echo "🔄 Checking if FFmpeg is installed..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ FFmpeg not found. Starting installation..."
    
    echo "🔄 Updating pkgs..."
    sudo apt-get update -q
    
    echo "📦 Installing FFmpeg..."
    sudo apt-get install -qq -y ffmpeg
    
    echo "✅ FFmpeg installed correctly."
else
    echo "✅ FFmpeg is already installed."
fi


echo "\n🔍 FFmpeg version installed:"
ffmpeg -version | head -n 1

echo "\n🎉 Config completed! FFmpeg is ready to use."