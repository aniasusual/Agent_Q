#!/bin/bash

# Create simple colored PNG files as placeholders using ImageMagick or base64
# For now, we'll create a simple SVG and convert it

# Create a simple SVG icon
cat > icon.svg << 'SVGEOF'
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4f46e5;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#6366f1;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="128" height="128" fill="url(#grad)" rx="24"/>
  <text x="64" y="90" font-size="80" text-anchor="middle" fill="white">Q</text>
</svg>
SVGEOF

echo "SVG icon created. Install ImageMagick to convert to PNG:"
echo "brew install imagemagick"
echo "Then run: convert icon.svg -resize 16x16 icon16.png"
echo "         convert icon.svg -resize 48x48 icon48.png"
echo "         convert icon.svg -resize 128x128 icon128.png"

