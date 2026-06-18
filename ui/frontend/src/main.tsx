import React    from 'react'
import ReactDOM from 'react-dom/client'
import { LanguageProvider } from './contexts/LanguageContext'
import { AuthProvider }     from './contexts/AuthContext'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <LanguageProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </LanguageProvider>
  </React.StrictMode>
)