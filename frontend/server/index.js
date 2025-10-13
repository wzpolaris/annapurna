import express from 'express';
import cors from 'cors';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = Number(process.env.PORT) || 4000;
const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || 'http://127.0.0.1:8000';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DIST_DIR = path.resolve(__dirname, '../dist');

app.use(cors({ origin: process.env.CORS_ORIGIN || '*' }));
app.use(express.json({ limit: '1mb' }));

app.post('/api/chat', async (req, res) => {
  try {
    const response = await axios.post(
      `${FASTAPI_BASE_URL}/chat`,
      req.body,
      {
        headers: {
          'Content-Type': 'application/json',
          'x-requested-with': 'northfield-frontend'
        },
        timeout: 0, // was 30_000 (30s); 0 disables timeout
      }
    );

    res.status(response.status).json(response.data);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.code === 'ECONNABORTED') {
        console.warn(
          '[frontend] Backend request timed out after',
          error.config?.timeout,
          'ms'
        );
      }
      const status = error.response?.status || 502;
      const message =
        error.response?.data?.message ||
        error.message ||
        'Backend request failed';
      res.status(status).json({ message });
      return;
    }

    res.status(500).json({ message: 'Unexpected server error' });
  }
});

app.use(express.static(DIST_DIR));

app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api/')) {
    next();
    return;
  }

  res.sendFile(path.join(DIST_DIR, 'index.html'), (err) => {
    if (err) {
      next(err);
    }
  });
});

app.use((err, req, res, _next) => {
  console.error('Express server error:', err);
  res.status(500).json({ message: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`[frontend] Server listening on http://localhost:${PORT}`);
});
