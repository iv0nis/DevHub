# DevHub Web Dashboard

Web-based dashboard for monitoring and controlling DevHub project development in real-time.

## Features

- **Real-time Project Monitoring**: Live view of project status, task progress, and health metrics
- **Blueprint Status**: Visual representation of blueprint completeness with component breakdown
- **Agent Activity**: Real-time monitoring of agent operations and file modifications
- **Document Synchronization**: Status and control of document sync operations
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query for server state
- **UI Components**: Custom components with Tailwind
- **API Integration**: Python integration via API routes

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Python 3.8+ (for DevHub backend integration)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set environment variables:
```bash
# Optional: Set custom DevHub project path
export DEVHUB_PROJECT_PATH=/path/to/your/devhub/project
```

3. Run development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
src/
├── pages/              # Next.js pages and API routes
│   ├── api/           # API endpoints
│   │   ├── project/   # Project status API
│   │   ├── blueprint/ # Blueprint evaluation API
│   │   ├── agents/    # Agent activity API
│   │   └── documents/ # Document sync API
│   └── index.tsx      # Main dashboard page
├── components/        # React components
│   ├── ui/           # Base UI components
│   └── features/     # Feature-specific components
├── types/            # TypeScript type definitions
└── styles/           # Global styles
```

## API Endpoints

- `GET /api/project/status` - Get current project status and metrics
- `GET /api/blueprint/completeness` - Get blueprint completeness score
- `GET /api/agents/activity` - Get agent activity log
- `GET /api/documents/sync` - Get document sync status
- `POST /api/documents/sync` - Trigger manual document sync

## Configuration

The dashboard can be configured via environment variables:

- `DEVHUB_PROJECT_PATH`: Path to DevHub project directory (default: parent directory)
- `PYTHON_PATH`: Path to Python executable (default: python3)

## Development Mode

In development mode, the dashboard uses mock data if the DevHub backend is not available. This allows frontend development without a complete DevHub setup.

## Integration with DevHub

The dashboard integrates with the DevHub Python backend through:

1. **File System Monitoring**: Watches critical DevHub files for changes
2. **API Bridge**: Node.js API routes that call Python scripts
3. **Real-time Updates**: React Query polling for live data updates

## Contributing

1. Follow the existing code style and component patterns
2. Add TypeScript types for all new interfaces
3. Test components in isolation before integration
4. Ensure responsive design works on mobile devices

## License

Part of the DevHub project ecosystem.