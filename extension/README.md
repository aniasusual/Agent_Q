# Agent Q - Chrome Extension

AI-powered Playwright test automation assistant built with React, TypeScript, and Vite.

## 🎯 Milestone 1: Complete! ✅

You now have a fully functional Chrome extension with:
- ✅ React + TypeScript + Vite setup
- ✅ Side panel UI with chat interface
- ✅ Monaco code editor integration
- ✅ Beautiful, responsive design
- ✅ Background service worker
- ✅ Content script foundation

## 📦 Installation

### Option 1: Load Unpacked Extension (Development)

1. **Build the extension:**
   ```bash
   cd extension
   npm install
   npm run build
   ```

2. **Load in Chrome:**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)
   - Click "Load unpacked"
   - Select the `extension/dist` folder
   - The Agent Q icon should appear in your toolbar!

3. **Open the side panel:**
   - Click the Agent Q icon in your toolbar
   - The side panel will open on the right side
   - Try chatting with the agent!

### Option 2: Development with Hot Reload

For development with live updates:

```bash
npm run dev
```

Then manually reload the extension in `chrome://extensions/` when you make changes.

## 🚀 Usage

1. **Open any website** you want to test
2. **Click the Agent Q icon** to open the side panel
3. **Type a test description** like:
   - "Test that users can click the login button"
   - "Check if the search bar works"
   - "Verify the checkout flow"
4. **See the generated code** in the Monaco editor
5. (Future milestones) Run, save, and export your tests!

## 🏗️ Project Structure

```
extension/
├── public/
│   └── manifest.json          # Chrome extension manifest
├── src/
│   ├── components/
│   │   ├── Header.tsx         # Top header with status
│   │   ├── ChatSection.tsx    # Chat interface
│   │   ├── EditorSection.tsx  # Monaco code editor
│   │   └── Footer.tsx         # Bottom footer
│   ├── App.tsx                # Main app component
│   ├── App.css                # App styles
│   ├── index.css              # Global styles
│   ├── sidepanel.tsx          # Entry point for side panel
│   ├── background.ts          # Service worker
│   └── content.ts             # Content script
├── sidepanel.html             # Side panel HTML
├── vite.config.ts             # Vite configuration
├── tsconfig.json              # TypeScript configuration
└── package.json               # Dependencies

dist/                          # Built extension (after npm run build)
├── manifest.json
├── sidepanel.html
├── sidepanel.js
├── background.js
├── content.js
└── assets/
```

## 🛠️ Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **Monaco Editor** - VS Code-like code editor
- **Chrome Extension APIs** - Side panel, messaging, etc.

## 📝 Scripts

```bash
npm run dev      # Start development server
npm run build    # Build production extension
npm run preview  # Preview production build
```

## 🎨 Features (Milestone 1)

### ✅ Implemented
- Professional side panel UI
- Chat interface with message history
- Monaco code editor with syntax highlighting
- Connection status indicator
- Responsive design
- TypeScript support
- Background service worker
- Content script foundation

### 🔜 Coming Next (Milestone 2)
- WebSocket connection to backend
- Real Gemini AI integration
- Actual test code generation
- DOM and screenshot capture

## 🐛 Troubleshooting

### Extension doesn't load
- Make sure you ran `npm run build` first
- Check that you're loading the `dist` folder, not the root
- Look for errors in `chrome://extensions/` page

### Side panel doesn't open
- Click the Agent Q icon in the toolbar
- If no icon, check that the extension is enabled
- Try reloading the extension

### Monaco editor not showing
- Check browser console for errors (F12)
- Make sure the build completed successfully
- Verify dist/assets folder has the CSS files

### Content script errors
- Content scripts only work on regular web pages
- They won't work on chrome:// pages or extension pages
- Check the console on the target page (F12)

## 📖 Development Guide

### Adding a new component

1. Create file in `src/components/YourComponent.tsx`
2. Import and use in `App.tsx`
3. Add styles to `App.css`
4. Rebuild: `npm run build`

### Modifying styles

1. Edit `src/App.css` or `src/index.css`
2. Use CSS variables defined in `:root` for consistency
3. Rebuild and reload extension

### Testing changes

1. Make your changes
2. Run `npm run build`
3. Go to `chrome://extensions/`
4. Click reload icon on Agent Q card
5. Reopen side panel to see changes

## 🎯 Next Milestones

### Milestone 2: Backend Connection
- WebSocket client in extension
- Backend WebSocket endpoint
- Real-time communication
- Connection status updates

### Milestone 3: DOM Capture
- Screenshot capture API
- DOM tree extraction
- Send data to backend
- Page analysis

### Milestone 4: AI Integration
- Gemini prompt engineering
- Test code generation
- Display in Monaco editor
- Handle AI responses

## 🤝 Contributing

This is in active development. Features are being added milestone by milestone.

## 📄 License

ISC

---

**Built with ❤️ for automated testing**