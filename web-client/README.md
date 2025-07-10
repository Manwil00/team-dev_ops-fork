# Web Client

React + TypeScript frontend for exploring research trends via AI analysis.

## Structure
```
src/
├── components/
│   ├── ui/ (base components)
│   ├── Header.tsx
│   ├── QueryForm.tsx
│   ├── AnalysisHistory.tsx
│   ├── AnalysisItem.tsx
│   ├── TopicResult.tsx
│   └── StartExploringForm.tsx
├── services/
│   └── analysis.ts (API calls)
├── lib/utils.ts
├── styles/
└── App.tsx
```

## Key Features
- Query submission with source selection.
- Real-time analysis display.
- Interactive trend and article exploration.
- Analysis history management.

## API Integration

For detailed backend API specs, see the [Swagger Docs](https://aet-devops25.github.io/team-dev_ops/swagger/).

The client uses fetch to interact with backend endpoints for query submission, analysis retrieval, and history management.

## Running
```bash
npm install
npm run dev
```

## Docker
Served via Nginx in Dockerfile."
