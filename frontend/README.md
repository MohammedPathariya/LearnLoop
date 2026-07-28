# LearnLoop frontend

The frontend uses React 19, Vite, Vitest, and custom responsive CSS.

## Local commands

Install dependencies:

```bash
npm ci
```

Start the development server at `http://localhost:3000`:

```bash
npm start
```

Run the frontend tests:

```bash
npm test
```

Create the production build in `build/`:

```bash
npm run build
```

Set `VITE_API_URL` when the backend is not available at
`http://localhost:5050`. Copy `.env.example` to `.env` for a local override.
