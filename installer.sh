#!/bin/bash

# Script para instalar FFmpeg en GitHub Codespace
set -e # Termina el script inmediatamente si ocurre algún error

echo "🔄 Verificando si FFmpeg está instalado..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ FFmpeg no encontrado. Iniciando instalación..."
    
    # Actualizar lista de paquetes
    echo "🔄 Actualizando lista de paquetes..."
    sudo apt-get update -q
    
    # Instalar FFmpeg
    echo "📦 Instalando FFmpeg..."
    sudo apt-get install -qq -y ffmpeg
    
    echo "✅ FFmpeg instalado correctamente."
else
    echo "✅ FFmpeg ya está instalado."
fi

# Verificar versión instalada
echo "\n🔍 Versión de FFmpeg instalada:"
ffmpeg -version | head -n 1

echo "\n🎉 ¡Configuración completada! FFmpeg está listo para usar."