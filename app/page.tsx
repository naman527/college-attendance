export default function Home() {
  return (
    <main style={{ padding: '60px', fontFamily: 'sans-serif', textAlign: 'center' }}>
      <h1 style={{ fontSize: '2.5rem', color: '#0f172a', fontWeight: 'bold' }}>
        🏛️ College Attendance Portal
      </h1>
      <p style={{ color: '#64748b', fontSize: '1.2rem', marginTop: '10px' }}>
        Niranjana Majithia College Management System
      </p>
      <div style={{ marginTop: '30px' }}>
        <a 
          href="/login" 
          style={{ 
            background: '#2563eb', 
            color: 'white', 
            padding: '12px 24px', 
            borderRadius: '8px', 
            textDecoration: 'none', 
            fontWeight: 'bold' 
          }}
        >
          Go to Portal Login
        </a>
      </div>
    </main>
  );
}