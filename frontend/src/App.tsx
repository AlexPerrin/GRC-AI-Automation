import { Route, Routes } from 'react-router-dom'
import VendorDetailPage from './pages/VendorDetailPage'
import VendorListPage from './pages/VendorListPage'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <a href="/" className="text-lg font-semibold text-gray-900 hover:text-blue-600">
          GRC Vendor Portal
        </a>
        <span
          className="text-sm text-gray-400 cursor-not-allowed"
          title="Coming soon"
        >
          Authentication
        </span>
      </nav>
      <main className="max-w-7xl mx-auto px-6 py-8">
        <Routes>
          <Route path="/" element={<VendorListPage />} />
          <Route path="/vendors/:id" element={<VendorDetailPage />} />
        </Routes>
      </main>
    </div>
  )
}
