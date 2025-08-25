# Chat Frontend

Modern React frontend for the fullstack chat application.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Access at: [http://localhost:5173](http://localhost:5173)

## Features

- **Real-time chat interface** with message history
- **Dark/Light theme toggle** with system preference detection
- **Mobile-responsive design** with collapsible sidebar
- **Search and filter** chat conversations
- **Pin and archive** important chats
- **Chat settings** (AI model parameters, system prompts)

## Tech Stack

- **React 18** with hooks and context
- **Vite** for fast development and building
- **Zustand** for state management
- **CSS** with custom properties for theming

## Project Structure

```
src/
├── components/
│   ├── chat/          # Chat area, messages, input
│   ├── sidebar/       # Chat list, search, filters
│   ├── layout/        # Main layout components
│   ├── common/        # Reusable UI components
│   └── ui/            # Basic UI elements (alerts, etc)
├── contexts/          # React contexts (theme)
├── services/          # API client and communication
├── stores/            # Zustand state management
├── utils/             # Storage utilities
├── App.jsx            # Main app component
└── main.jsx           # Entry point
```

## Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint (if configured)
```

## Environment Variables

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Key Components

- **MainLayout** - Main app layout with sidebar and chat area
- **ChatSidebar** - Chat list with search, filtering, and organization
- **ChatArea** - Message display and input interface
- **ChatStore** - Zustand store for chat state management

## Development

The frontend communicates with the FastAPI backend via REST API. Chat data is persisted in the database, while UI preferences (theme, sidebar width) are stored in localStorage.

For the complete application setup, see the main project README.
