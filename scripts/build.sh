#!/usr/bin/env bash
set -e

echo "🏗️  Building ChessCoach Local..."

# Clean
rm -rf dist/

# Build React (renderer)
echo "⚛️  Building React..."
npm run build:react

# Build Electron (main process)
echo "⚡ Building Electron..."
npm run build:electron

echo "✅ Build complete → dist/"
echo "   Package: npm run package"