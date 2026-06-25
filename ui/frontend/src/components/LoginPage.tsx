import { useState } from 'react'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { useLang } from '../contexts/LanguageContext'
import { useAuth } from '../contexts/AuthContext'
import { apiLogin, apiRegister } from '../api/auth'

export default function LoginPage() {
  const { toggleLang, lang } = useLang()
  const { setAuth }          = useAuth()

  const [mode,     setMode]     = useState<'login' | 'register'>('login')
  const [email,    setEmail]    = useState('')
  const [name,     setName]     = useState('')
  const [password, setPassword] = useState('')
  const [showPwd,  setShowPwd]  = useState(false)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')

  const handleSubmit = async () => {
    setError('')
    if (!email || !password) { setError('Please fill in all fields'); return }
    if (mode === 'register' && !name.trim()) { setError('Please enter your name'); return }
    if (password.length < 6) { setError('Password must be at least 6 characters'); return }

    setLoading(true)
    try {
      const result = mode === 'login'
        ? await apiLogin(email.trim(), password)
        : await apiRegister(email.trim(), name.trim(), password)
      setAuth(result.token, result.user)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSubmit()
  }

  return (
    <div className="h-screen flex flex-col items-center justify-center px-4"
         style={{ background: '#F0F4FA' }}>

      <div className="absolute top-5 right-5 flex items-center rounded-full overflow-hidden"
           style={{ border: '1.5px solid #003DA5', background: '#fff' }}>
        <button
          onClick={() => { if (lang !== 'en') toggleLang() }}
          className="px-3 py-1.5 text-xs font-bold transition-all duration-150"
          style={{
            background: lang === 'en' ? '#003DA5' : 'transparent',
            color:      lang === 'en' ? '#ffffff' : '#003DA5',
          }}
        >
          EN
        </button>
        <div style={{ width: '1px', height: '16px', background: '#003DA5', opacity: 0.3 }} />
        <button
          onClick={() => { if (lang !== 'ja') toggleLang() }}
          className="px-3 py-1.5 text-xs font-bold transition-all duration-150"
          style={{
            background: lang === 'ja' ? '#003DA5' : 'transparent',
            color:      lang === 'ja' ? '#ffffff' : '#003DA5',
          }}
        >
          JA
        </button>
      </div>

      <div className="bg-white rounded-3xl shadow-lg w-full flex flex-col items-center"
           style={{ maxWidth: '400px', border: '1px solid #E5E7EB', padding: '40px 36px' }}>

        <div className="w-16 h-16 rounded-2xl mb-5 flex flex-col items-center
                        justify-center shadow-md" style={{ background: '#003DA5' }}>
          <span className="text-white font-black text-2xl leading-none">A</span>
          <div className="w-8 mt-1 rounded-full"
               style={{ height: '2px', background: 'rgba(255,255,255,0.45)' }} />
        </div>

        <h1 className="text-xl font-bold text-gray-900 tracking-tight">Autoliv</h1>
        <p className="text-sm mt-0.5" style={{ color: '#003DA5' }}>
          {lang === 'en' ? 'Onboarding Assistant' : 'オンボーディングアシスタント'}
        </p>

        <div className="flex mt-7 mb-6 p-1 rounded-xl w-full" style={{ background: '#F0F4FA' }}>
          {(['login', 'register'] as const).map(m => (
            <button
              key={m}
              onClick={() => { setMode(m); setError('') }}
              className="flex-1 py-2 text-sm font-semibold rounded-lg transition-all duration-150"
              style={{
                background: mode === m ? '#003DA5' : 'transparent',
                color:      mode === m ? '#ffffff' : '#6B7280',
              }}
            >
              {m === 'login'
                ? (lang === 'en' ? 'Sign in' : 'サインイン')
                : (lang === 'en' ? 'Register' : '登録')}
            </button>
          ))}
        </div>

        <div className="w-full space-y-3">
          {mode === 'register' && (
            <div>
              <label className="text-xs font-semibold text-gray-600 mb-1 block">
                {lang === 'en' ? 'Full name' : '氏名'}
              </label>
              <input
                type="text" value={name} onChange={e => setName(e.target.value)}
                onKeyDown={onKey} placeholder={lang === 'en' ? 'Yamada Taro' : '山田 太郎'}
                className="w-full px-4 py-2.5 text-sm rounded-xl outline-none transition-all"
                style={{ border: '1.5px solid #E5E7EB', background: '#F8F9FB' }}
                onFocus={e => { e.currentTarget.style.borderColor = '#003DA5'; e.currentTarget.style.background = '#fff' }}
                onBlur={e => { e.currentTarget.style.borderColor = '#E5E7EB'; e.currentTarget.style.background = '#F8F9FB' }}
              />
            </div>
          )}

          <div>
            <label className="text-xs font-semibold text-gray-600 mb-1 block">
              {lang === 'en' ? 'Email address' : 'メールアドレス'}
            </label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)}
              onKeyDown={onKey} placeholder="name@gmail.com"
              className="w-full px-4 py-2.5 text-sm rounded-xl outline-none transition-all"
              style={{ border: '1.5px solid #E5E7EB', background: '#F8F9FB' }}
              onFocus={e => { e.currentTarget.style.borderColor = '#003DA5'; e.currentTarget.style.background = '#fff' }}
              onBlur={e => { e.currentTarget.style.borderColor = '#E5E7EB'; e.currentTarget.style.background = '#F8F9FB' }}
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-600 mb-1 block">
              {lang === 'en' ? 'Password' : 'パスワード'}
            </label>
            <div className="relative">
              <input
                type={showPwd ? 'text' : 'password'} value={password}
                onChange={e => setPassword(e.target.value)} onKeyDown={onKey}
                placeholder={lang === 'en' ? 'Min. 6 characters' : '6文字以上'}
                className="w-full px-4 py-2.5 pr-11 text-sm rounded-xl outline-none transition-all"
                style={{ border: '1.5px solid #E5E7EB', background: '#F8F9FB' }}
                onFocus={e => { e.currentTarget.style.borderColor = '#003DA5'; e.currentTarget.style.background = '#fff' }}
                onBlur={e => { e.currentTarget.style.borderColor = '#E5E7EB'; e.currentTarget.style.background = '#F8F9FB' }}
              />
              <button type="button" onClick={() => setShowPwd(p => !p)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors">
                {showPwd ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-3 w-full px-4 py-2.5 rounded-xl text-xs font-medium"
               style={{ background: '#FEE2E2', color: '#B91C1C' }}>
            {error}
          </div>
        )}

        <button
          onClick={handleSubmit} disabled={loading}
          className="mt-5 w-full py-3 rounded-xl text-sm font-semibold text-white
                     transition-all active:scale-95 disabled:opacity-60
                     disabled:cursor-not-allowed flex items-center justify-center gap-2"
          style={{ background: '#003DA5' }}
          onMouseEnter={e => { if (!loading) (e.currentTarget as HTMLButtonElement).style.background = '#002D7A' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = '#003DA5' }}
        >
          {loading && <Loader2 size={15} className="animate-spin" />}
          {mode === 'login'
            ? (lang === 'en' ? 'Sign in' : 'サインイン')
            : (lang === 'en' ? 'Create account' : 'アカウント作成')}
        </button>

        <p className="mt-4 text-xs text-gray-400">
          {mode === 'login'
            ? (lang === 'en' ? "Don't have an account? " : 'アカウントをお持ちでない方は ')
            : (lang === 'en' ? 'Already have an account? ' : 'すでにアカウントをお持ちの方は ')}
          <button
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}
            className="font-semibold underline" style={{ color: '#003DA5' }}
          >
            {mode === 'login'
              ? (lang === 'en' ? 'Register' : '登録する')
              : (lang === 'en' ? 'Sign in' : 'サインイン')}
          </button>
        </p>

        <p className="mt-5 text-xs" style={{ color: '#D1D5DB' }}>
          {lang === 'en'
            ? 'Internal use only · Autoliv Japan Technical Center'
            : '社内利用限定 · Autoliv日本技術センター'}
        </p>
      </div>
    </div>
  )
}