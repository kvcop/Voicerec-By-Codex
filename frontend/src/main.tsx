import React from 'react';
import ReactDOM from 'react-dom/client';

export function App() {
  return <h1>Voicerec</h1>;
}

const rootElement = typeof document === 'undefined' ? null : document.getElementById('root');
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

export default App;
