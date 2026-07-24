import { Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProtectedRoute from './components/common/ProtectedRoute';
import DashboardLayout from './components/Layout/DashboardLayout';
import GeneratePage from './pages/dashboard/GeneratePage';
import ClassesPage from './pages/dashboard/ClassesPage';
import ClassDetailPage from './pages/dashboard/ClassDetailPage';
import SubjectsPage from './pages/dashboard/SubjectsPage';
import HistoryPage from './pages/dashboard/HistoryPage';
import OfflineBanner from './components/common/OfflineBanner';
import './App.css';

export default function App() {
  return (
    <>
      <OfflineBanner />
      <Routes>
      {/* Public routes */}
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected dashboard routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/dashboard" element={<Navigate to="/dashboard/classes" replace />} />
          <Route path="/dashboard/generate" element={<GeneratePage />} />
          <Route path="/dashboard/classes" element={<ClassesPage />} />
          <Route path="/dashboard/class/:id" element={<ClassDetailPage />} />
          <Route path="/dashboard/subjects" element={<SubjectsPage />} />
          <Route path="/dashboard/history" element={<HistoryPage />} />
        </Route>
      </Route>

      {/* Catch-all: redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </>
  );
}
