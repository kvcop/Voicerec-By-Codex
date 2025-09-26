# Frontend - Component Context

## Purpose
React-based web application for meeting transcription interface. Provides audio upload, real-time transcript display, speaker identification visualization, and meeting management. Built with TypeScript, Vite, and shadcn/ui components.

## Current Status: Initial Setup
Frontend scaffolding established with React 18, TypeScript, and Vite. Basic component structure with App and Dialog components. Internationalization support with English and Russian locales. UI component library (shadcn) integrated but not fully utilized yet.

## Component-Specific Development Guidelines

### TypeScript Standards
- **Strict mode** enabled
- **Explicit types** for all props and state
- **No any types** - use unknown or specific types
- **Interface over type** for component props

### React Patterns
- **Functional components only** - No class components
- **Custom hooks** for reusable logic
- **React.memo** for expensive components
- **Suspense/ErrorBoundary** for robust UX

### Component Structure
```
components/
└── ComponentName/
    ├── index.tsx          # Component implementation
    ├── styles.module.css  # CSS modules
    ├── ComponentName.test.tsx # Component tests
    └── types.ts          # Type definitions (if complex)
```

### Styling Approach
- **CSS Modules** for component isolation
- **Tailwind utilities** via shadcn/ui
- **Consistent spacing** using Tailwind classes
- **Dark mode support** (future)

## Major Subsystem Organization

### Components (`src/components/`)
- **App/**: Main application container
- **Dialog/**: Modal dialog implementation
- Future: AudioUpload, TranscriptViewer, SpeakerTimeline

### State Management (future)
- **Context API** for global state
- **Custom hooks** for local state logic
- **React Query** for server state (planned)

### API Integration (future)
- **Axios/fetch** for HTTP requests
- **EventSource** for SSE streaming
- **WebSocket** for real-time updates

### Internationalization (`src/locales/`)
- **next-intl** for i18n support
- JSON files for translations
- Support for English and Russian

## Architectural Patterns

### Component Composition
```tsx
// Feature component with clear props
interface TranscriptViewerProps {
  meetingId: string;
  onSpeakerClick: (speakerId: string) => void;
}

export const TranscriptViewer: React.FC<TranscriptViewerProps> = ({
  meetingId,
  onSpeakerClick
}) => {
  // Component logic
  return (
    <div className={styles.container}>
      {/* Component JSX */}
    </div>
  );
};
```

### Custom Hook Pattern
```tsx
// Reusable logic extraction
const useTranscriptStream = (meetingId: string) => {
  const [transcript, setTranscript] = useState<Transcript[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // SSE connection logic
  }, [meetingId]);
  
  return { transcript, isLoading };
};
```

### Error Boundary Pattern
```tsx
class ErrorBoundary extends React.Component {
  // Graceful error handling
  componentDidCatch(error: Error) {
    // Log to monitoring service
  }
}
```

## Integration Points

### Backend APIs
- **REST endpoints** for CRUD operations
- **Server-Sent Events** for transcript streaming
- **File upload** for audio processing
- **WebSocket** for real-time updates (future)

### External Libraries
- **shadcn/ui**: Component library
- **Radix UI**: Headless components
- **class-variance-authority**: Dynamic styling
- **tailwind-merge**: Class name management

### Browser APIs
- **File API** for audio upload
- **EventSource** for SSE
- **LocalStorage** for preferences
- **Web Audio API** (future audio preview)

## UI/UX Patterns

### Loading States
- Skeleton screens for initial load
- Inline spinners for actions
- Progress bars for uploads

### Error Handling
- Toast notifications for errors
- Inline validation messages
- Retry mechanisms for failures

### Responsive Design
- Mobile-first approach
- Breakpoint-based layouts
- Touch-friendly interactions

## Development Commands

All commands run from `frontend/` directory:

```bash
# Development
npm run dev              # Start dev server
npm run build           # Production build
npm run preview         # Preview production build

# Quality checks
npm run lint            # ESLint
npm test               # Vitest tests
npm test -- --watch    # Watch mode

# Component generation (future)
npm run generate:component ComponentName
```

## Testing Strategy

### Unit Tests
- Component rendering tests
- Hook behavior tests
- Utility function tests

### Integration Tests
- User flow testing
- API integration mocks
- State management tests

### Testing Tools
- **Vitest**: Test runner
- **React Testing Library**: Component testing
- **MSW**: API mocking (future)

## Key Files Reference

- **src/main.tsx**: Application entry point
- **src/components/App/**: Main application component
- **vite.config.ts**: Build configuration
- **vitest.config.ts**: Test configuration
- **tsconfig.json**: TypeScript configuration

## Next Implementation Steps

1. Audio upload component with drag-and-drop
2. Real-time transcript viewer with SSE
3. Speaker identification timeline
4. Meeting list and management
5. Search and filter functionality
6. User authentication UI
7. Settings and preferences panel
8. Mobile-responsive layouts

## Performance Optimization

- **Code splitting** with React.lazy
- **Bundle optimization** via Vite
- **Image optimization** with lazy loading
- **Memoization** for expensive computations
- **Virtual scrolling** for long transcripts

---

*This component documentation provides architectural context for the frontend application. Update when new patterns emerge or components are added.*