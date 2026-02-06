/**
 * Main App Component
 * Ko-Desain Platform untuk Aplikasi Pembayaran Mobile Tunanetra
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnnouncerProvider } from './components/accessibility/ScreenReaderAnnouncer';

// Pages (to be created)
// import LoginPage from './pages/LoginPage';
// import DashboardPage from './pages/DashboardPage';
// import SessionPage from './pages/SessionPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Placeholder components
const LoginPage = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-100">
    <div className="bg-white p-8 rounded-lg shadow-md w-96">
      <h1 className="text-2xl font-bold mb-6 text-center">Ko-Desain Platform</h1>
      <p className="text-gray-600 mb-4 text-center">
        Platform untuk ko-desain aplikasi pembayaran mobile aksesibel
      </p>
      <form className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            type="email"
            id="email"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="email@example.com"
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Password
          </label>
          <input
            type="password"
            id="password"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <button
          type="submit"
          className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-md font-medium focus:ring-4 focus:ring-blue-300"
        >
          Masuk
        </button>
      </form>
    </div>
  </div>
);

const DashboardPage = () => (
  <div className="min-h-screen bg-gray-100 p-8">
    <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Sesi Aktif</h2>
        <p className="text-gray-600">Belum ada sesi aktif</p>
        <button className="mt-4 bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-md">
          Buat Sesi Baru
        </button>
      </div>
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Artifact Terbaru</h2>
        <p className="text-gray-600">Belum ada artifact</p>
      </div>
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Research Mode</h2>
        <p className="text-gray-600">Bandingkan sesi dengan AI vs tanpa AI</p>
      </div>
    </div>
  </div>
);

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AnnouncerProvider>
        <BrowserRouter>
          {/* Skip Link for Accessibility */}
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-500 text-white px-4 py-2 rounded z-50"
          >
            Langsung ke konten utama
          </a>

          <main id="main-content" tabIndex={-1}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              {/* <Route path="/session/:sessionId" element={<SessionPage />} /> */}
              <Route path="/" element={<Navigate to="/login" replace />} />
            </Routes>
          </main>
        </BrowserRouter>
      </AnnouncerProvider>
    </QueryClientProvider>
  );
};

export default App;
