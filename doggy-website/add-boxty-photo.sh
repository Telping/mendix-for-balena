#!/bin/bash

# Script to add Boxty's photo to the homepage

echo "🐾 Adding Boxty's Photo to Homepage"
echo "===================================="
echo ""

TARGET_DIR="app/static/images"
TARGET_FILE="$TARGET_DIR/boxty-hero.jpg"

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating images directory..."
    mkdir -p "$TARGET_DIR"
fi

# Check if photo already exists
if [ -f "$TARGET_FILE" ]; then
    echo "⚠️  Boxty's photo already exists at: $TARGET_FILE"
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing photo."
        exit 0
    fi
fi

# Ask for photo location
echo "Please drag and drop Boxty's photo here, or enter the path:"
read -r PHOTO_PATH

# Remove quotes if user's shell added them
PHOTO_PATH="${PHOTO_PATH//\"/}"
PHOTO_PATH="${PHOTO_PATH//\'/}"

# Check if file exists
if [ ! -f "$PHOTO_PATH" ]; then
    echo "❌ Error: File not found at: $PHOTO_PATH"
    exit 1
fi

# Copy the file
echo "Copying photo..."
cp "$PHOTO_PATH" "$TARGET_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Success! Boxty's photo has been added to the homepage!"
    echo ""
    echo "📍 Photo location: $TARGET_FILE"
    echo ""
    echo "🚀 Start the app to see it:"
    echo "   ./start-local.sh"
    echo ""
    echo "   Then open: http://localhost:5000"
else
    echo "❌ Error: Failed to copy photo"
    exit 1
fi
