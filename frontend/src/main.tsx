import React from 'react';
import ReactDOM from 'react-dom/client';
import { MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';
import './index.css';
import App from './App';

const rootElement = document.getElementById('root');

if (!rootElement) {
  console.error('[main] Root element with id="root" was not found.');
} else {
  console.time('[main] render');
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <MantineProvider
        defaultColorScheme="light"
        theme={{
          fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          defaultRadius: 'md'
        }}
      >
        <App />
      </MantineProvider>
    </React.StrictMode>
  );
  console.timeEnd('[main] render');
  console.log('[main] React render dispatched');
}
