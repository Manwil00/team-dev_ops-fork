# NicheExplorer Frontend

The NicheExplorer frontend is a modern React application built with TypeScript that provides an intuitive interface for discovering and exploring research trends through AI-powered semantic analysis.

## 🏗️ Architecture Overview

The frontend follows a component-based architecture with clear separation of concerns:

```
src/
├── components/              # Reusable UI components
│   ├── ui/                 # Base UI components (buttons, cards, etc.)
│   ├── Header.tsx          # Application header with branding
│   ├── QueryForm.tsx       # Main search interface
│   ├── AnalysisHistory.tsx # Historical analysis display
│   ├── AnalysisItem.tsx    # Individual analysis card
│   ├── TrendResult.tsx     # Trend visualization component
│   └── StartExploringForm.tsx # Initial query form
├── services/               # API communication layer
│   └── analysis.ts         # Backend API integration
├── lib/                    # Utility functions
│   └── utils.ts           # Common helper functions
├── styles/                 # Styling and design system
└── App.tsx                # Main application component
```

## 🔄 Data Flow & User Journey

### 1. **Initial Interface**
- User lands on clean, modern interface with background imagery
- Sees prominent search form with query input and settings
- Can toggle between auto-detection and manual source selection

### 2. **Query Submission Process**
```typescript
// User submits query through StartExploringForm
const handleAnalyze = async (req: AnalyzeRequest) => {
  try {
    const response = await analyze(req);
    // Process and display results
  } catch (err) {
    // Handle errors gracefully
  }
};
```

### 3. **Real-time Analysis Display**
- Shows loading states during analysis processing
- Streams results as they become available from backend
- Provides immediate feedback on analysis progress

### 4. **Interactive Results Exploration**
- **Trend Cards**: Each trend displays with animated relevance bar
- **Article Expansion**: Individual articles can be expanded for details
- **Progressive Disclosure**: Users can drill down from trends to articles

### 5. **Historical Analysis Management**
- All analyses are persistently stored and can be revisited
- Users can delete unwanted analyses
- Full article details remain accessible in history

## 🎨 Component Architecture

### **StartExploringForm Component**
The main entry point for user queries:

```typescript
interface StartExploringFormProps {
  onAnalyze: (request: AnalyzeRequest) => Promise<void>;
}
```

**Features:**
- Query input with validation
- Source type selection (Research/Community)
- Article limit configuration
- Auto-detection toggle
- Real-time form validation

### **AnalysisHistory Component**
Displays previous analyses in a clean, organized manner:

```typescript
interface AnalysisHistoryProps {
  analyses: Analysis[];
  onDeleteAnalysis: (id: string) => void;
  darkMode?: boolean;
}
```

**Features:**
- Chronological listing of past analyses
- Quick access to previous results
- Delete functionality for cleanup
- Responsive design for all screen sizes

### **AnalysisItem Component**
Individual analysis display with collapsible trends:

```typescript
interface AnalysisItemProps {
  id: string;
  query: string;
  timestamp: string;
  type: 'Research' | 'Community';
  trends: Trend[];
  onDelete: (id: string) => void;
  darkMode?: boolean;
}
```

**Key Features:**
- Shows analysis metadata (query, timestamp, type)
- Displays trend count and total article count
- Expandable to show all trends
- Delete functionality with confirmation

### **TrendResult Component**
Rich display for individual trends with interactive features:

```typescript
interface TrendResultProps {
  title: string;
  description: string;
  articleCount: number;
  relevance: number;
  articles?: Article[];
  darkMode?: boolean;
  rank?: number;
  trendId?: string;
}
```

**Interactive Elements:**
- **Animated Progress Bar**: Shows relevance score with smooth animation
- **Article List**: Expandable list of related articles
- **Individual Article Expansion**: Each article can be expanded independently
- **External Links**: Direct links to source articles

### **Progress Bar Animation System**
The relevance bars use CSS transitions for smooth animations:

```typescript
const [animateBar, setAnimateBar] = useState(false);

useEffect(() => {
  // Trigger animation after component mounts
  const timer = setTimeout(() => setAnimateBar(true), 200);
  return () => clearTimeout(timer);
}, []);

// CSS styling with dynamic width
style={{
  width: animateBar ? `${relevance}%` : '0%',
  transition: 'width 1s ease-out'
}}
```

## 🔌 API Integration

### **Analysis Service**
Centralized API communication through the analysis service:

```typescript
// Core API endpoints
export const analyze = async (request: AnalyzeRequest): Promise<AnalysisResponse> => {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  return response.json();
};

export const getAnalysisHistory = async (): Promise<AnalysisResponse[]> => {
  const response = await fetch('/api/history');
  return response.json();
};

export const deleteAnalysis = async (id: string): Promise<void> => {
  await fetch(`/api/analysis/${id}`, { method: 'DELETE' });
};
```

### **Error Handling Strategy**
Comprehensive error handling throughout the application:

- **Network Errors**: Graceful handling of connection issues
- **API Errors**: User-friendly error messages for backend failures
- **Validation Errors**: Real-time validation with helpful feedback
- **Loading States**: Clear indicators during async operations

## 🎨 Design System

### **Color Scheme & Theming**
- **Primary Colors**: Blue gradients for interactive elements
- **Semantic Colors**: Green for success, red for errors, yellow for warnings
- **Background**: Translucent cards over blurred nature imagery
- **Dark Mode Support**: Components designed for light/dark theme switching

### **Typography**
- **Headings**: Clear hierarchy with appropriate font weights
- **Body Text**: Optimized for readability across all screen sizes
- **Code Elements**: Monospace fonts for technical content

### **Spacing & Layout**
- **Grid System**: Responsive layout using CSS Grid and Flexbox
- **Component Spacing**: Consistent spacing using Tailwind's spacing scale
- **Container Sizing**: Max-width containers for optimal reading experience

### **Animation & Interactions**
- **Micro-interactions**: Subtle animations for better user experience
- **Progress Indicators**: Animated progress bars showing relevance scores
- **Hover Effects**: Interactive elements provide visual feedback
- **Smooth Transitions**: All state changes use CSS transitions

## 🚀 Development Setup

### **Prerequisites**
- Node.js 18+ with npm
- Modern browser with ES2020 support

### **Local Development**
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### **Environment Configuration**
The frontend automatically detects the API server at `http://localhost:8080` in development.

### **Code Quality Tools**
- **TypeScript**: Full type safety throughout the application
- **ESLint**: Code linting with React and TypeScript rules
- **Prettier**: Consistent code formatting
- **Vite**: Fast development and optimized builds

## 📱 Responsive Design

### **Mobile-First Approach**
- Designed for mobile devices first, then enhanced for larger screens
- Touch-friendly interface elements with appropriate sizing
- Optimized layouts for portrait and landscape orientations

### **Breakpoint Strategy**
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+
- **Large Desktop**: 1440px+

### **Progressive Enhancement**
- Core functionality works on all modern browsers
- Enhanced features for browsers with advanced capabilities
- Graceful degradation for older browser versions

## 🧪 Testing Strategy

### **Component Testing**
```bash
# Run component tests
npm test

# Run tests with coverage
npm run test:coverage
```

### **Manual Testing Checklist**
- [ ] Query submission with various inputs
- [ ] Analysis history loading and display
- [ ] Trend expansion and article viewing
- [ ] Delete functionality
- [ ] Responsive design across devices
- [ ] Error handling scenarios

## 🔍 Performance Optimizations

### **Bundle Optimization**
- **Code Splitting**: Lazy loading of route components
- **Tree Shaking**: Elimination of unused code
- **Asset Optimization**: Compressed images and minified CSS/JS

### **Runtime Performance**
- **React.memo**: Preventing unnecessary re-renders
- **useMemo/useCallback**: Memoization of expensive operations
- **Virtual Scrolling**: For large lists of articles (future enhancement)

### **Loading Strategies**
- **Skeleton Loading**: Placeholder UI during data fetching
- **Progressive Loading**: Show partial results as they arrive
- **Error Boundaries**: Graceful error handling without app crashes

## 🔧 Build & Deployment

### **Production Build**
```bash
npm run build
```

Generates optimized static files in the `dist/` directory.

### **Docker Deployment**
The application includes a multi-stage Dockerfile:

```dockerfile
# Build stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### **Configuration Management**
- Environment-specific builds through Vite configuration
- Runtime configuration through environment variables
- API endpoint configuration for different deployment environments

## 🎯 Future Enhancements

### **Planned Features**
- **Real-time Updates**: WebSocket connection for live trend updates
- **Advanced Filtering**: Filter trends by date, relevance, source type
- **Export Functionality**: Export analyses as PDF/CSV
- **Bookmark System**: Save interesting trends for later review
- **Sharing**: Share analyses via URL or social media

### **Technical Improvements**
- **PWA Support**: Offline capability and app-like experience
- **Advanced Caching**: Service worker for improved performance
- **Accessibility**: WCAG 2.1 AA compliance
- **Internationalization**: Support for multiple languages

---

The NicheExplorer frontend provides a sophisticated yet intuitive interface for exploring research trends, built with modern web technologies and best practices for performance, accessibility, and user experience.
