# UI Components Documentation

## Component Architecture
React functional components with TypeScript, CSS Modules for styling, and folder-based organization. All components follow consistent patterns for props, state management, and testing.

### Design Principles
- **Single Responsibility**: Each component has one clear purpose
- **Composition over Inheritance**: Build complex UIs from simple components
- **Type Safety**: Full TypeScript coverage with no `any` types
- **Testability**: Components designed for easy testing

## Implementation Patterns

### Component Structure
```tsx
// types.ts - Component type definitions
export interface ComponentProps {
  id: string;
  className?: string;
  onAction: (data: ActionData) => void;
  children?: React.ReactNode;
}

// index.tsx - Component implementation
import React, { useState, useCallback } from 'react';
import styles from './styles.module.css';
import type { ComponentProps } from './types';

export const Component: React.FC<ComponentProps> = ({
  id,
  className,
  onAction,
  children
}) => {
  const [state, setState] = useState(initialState);
  
  const handleAction = useCallback((data: ActionData) => {
    // Handle action
    onAction(data);
  }, [onAction]);
  
  return (
    <div className={`${styles.container} ${className}`}>
      {children}
    </div>
  );
};

Component.displayName = 'Component';
```

### CSS Module Pattern
```css
/* styles.module.css */
.container {
  display: flex;
  flex-direction: column;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
}

.container:hover {
  background-color: var(--color-hover);
}

/* Responsive design */
@media (max-width: 768px) {
  .container {
    padding: var(--spacing-sm);
  }
}
```

## Current Components

### App Component
**Location**: `components/App/`
- Main application container
- Manages global layout
- Provides context providers
- Handles routing (future)

### Dialog Component
**Location**: `components/Dialog/`
- Modal dialog implementation
- Uses Radix UI primitives
- Supports custom content
- Accessible (ARIA compliant)

## Planned Components

### AudioUpload
```tsx
interface AudioUploadProps {
  onUpload: (file: File) => Promise<void>;
  maxSize?: number;
  acceptedFormats?: string[];
}

// Features:
// - Drag and drop support
// - File validation
// - Upload progress
// - Error handling
```

### TranscriptViewer
```tsx
interface TranscriptViewerProps {
  meetingId: string;
  autoScroll?: boolean;
  highlightSpeaker?: string;
}

// Features:
// - Real-time SSE updates
// - Speaker color coding
// - Search highlighting
// - Export functionality
```

### SpeakerTimeline
```tsx
interface SpeakerTimelineProps {
  speakers: Speaker[];
  duration: number;
  currentTime?: number;
  onSeek?: (time: number) => void;
}

// Features:
// - Visual timeline
// - Speaker segments
// - Interactive seeking
// - Zoom controls
```

## Composition Patterns

### Layout Components
```tsx
// Consistent layout structure
<PageLayout>
  <Header />
  <Main>
    <Sidebar />
    <Content>
      {children}
    </Content>
  </Main>
  <Footer />
</PageLayout>
```

### Compound Components
```tsx
// Related components that work together
<TranscriptPanel>
  <TranscriptPanel.Header />
  <TranscriptPanel.Body>
    <TranscriptPanel.Line />
  </TranscriptPanel.Body>
  <TranscriptPanel.Footer />
</TranscriptPanel>
```

## State Management Patterns

### Local State
```tsx
// Component-specific state
const [isOpen, setIsOpen] = useState(false);
const [formData, setFormData] = useState<FormData>(initialData);
```

### Lifted State
```tsx
// Parent manages shared state
const ParentComponent = () => {
  const [sharedState, setSharedState] = useState();
  
  return (
    <>
      <ChildA state={sharedState} />
      <ChildB onUpdate={setSharedState} />
    </>
  );
};
```

### Context for Cross-Cutting Concerns
```tsx
// Theme, auth, preferences
const ThemeContext = React.createContext<Theme>('light');

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be within ThemeProvider');
  }
  return context;
};
```

## Styling Patterns

### Design Tokens
```css
:root {
  /* Colors */
  --color-primary: #3b82f6;
  --color-secondary: #8b5cf6;
  --color-danger: #ef4444;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  
  /* Typography */
  --font-mono: 'Fira Code', monospace;
  --font-sans: 'Inter', sans-serif;
}
```

### Component Variants
```tsx
// Using class-variance-authority
import { cva } from 'class-variance-authority';

const buttonVariants = cva('button-base', {
  variants: {
    variant: {
      primary: 'bg-primary text-white',
      secondary: 'bg-secondary text-white',
      ghost: 'bg-transparent hover:bg-gray-100'
    },
    size: {
      sm: 'px-2 py-1 text-sm',
      md: 'px-4 py-2',
      lg: 'px-6 py-3 text-lg'
    }
  },
  defaultVariants: {
    variant: 'primary',
    size: 'md'
  }
});
```

## Accessibility Patterns

### ARIA Attributes
```tsx
<button
  aria-label="Upload audio file"
  aria-pressed={isUploading}
  aria-disabled={isDisabled}
  role="button"
>
  Upload
</button>
```

### Keyboard Navigation
```tsx
const handleKeyDown = (e: KeyboardEvent) => {
  switch (e.key) {
    case 'Enter':
    case ' ':
      handleAction();
      break;
    case 'Escape':
      handleClose();
      break;
  }
};
```

### Focus Management
```tsx
useEffect(() => {
  if (isOpen) {
    firstFocusableRef.current?.focus();
  }
}, [isOpen]);
```

## Testing Patterns

### Component Tests
```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Component } from './index';

describe('Component', () => {
  it('renders with props', () => {
    render(
      <Component
        id="test"
        onAction={jest.fn()}
      />
    );
    
    expect(screen.getByTestId('test')).toBeInTheDocument();
  });
  
  it('handles user interaction', () => {
    const handleAction = jest.fn();
    render(<Component onAction={handleAction} />);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleAction).toHaveBeenCalled();
  });
});
```

### Hook Tests
```tsx
import { renderHook, act } from '@testing-library/react';
import { useCustomHook } from './hooks';

test('hook behavior', () => {
  const { result } = renderHook(() => useCustomHook());
  
  act(() => {
    result.current.action();
  });
  
  expect(result.current.state).toBe(expected);
});
```

## Performance Optimization

### Memoization
```tsx
// Expensive component
const ExpensiveComponent = React.memo(({ data }) => {
  // Only re-renders when data changes
  return <ComplexVisualization data={data} />;
});

// Expensive computation
const processedData = useMemo(
  () => expensiveProcess(rawData),
  [rawData]
);

// Stable callbacks
const handleClick = useCallback(
  (id: string) => {
    dispatch({ type: 'SELECT', id });
  },
  [dispatch]
);
```

### Code Splitting
```tsx
// Lazy load heavy components
const HeavyComponent = lazy(() => import('./HeavyComponent'));

// With loading boundary
<Suspense fallback={<LoadingSpinner />}>
  <HeavyComponent />
</Suspense>
```

---

*This documentation covers UI component patterns and best practices. Update when adding new components or patterns.*