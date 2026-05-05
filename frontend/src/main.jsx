import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Bell,
  Bot,
  Brain,
  CalendarClock,
  ChevronRight,
  ClipboardList,
  Cross,
  CreditCard,
  Droplets,
  FileText,
  Globe2,
  Heart,
  HeartPulse,
  History,
  LogOut,
  Menu,
  Mic,
  Moon,
  Pill,
  Search,
  Settings,
  ShieldCheck,
  Stethoscope,
  Sun,
  Thermometer,
  Upload,
  User,
  UserPlus,
  Weight,
} from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";
const AuthContext = createContext(null);

const defaultPatientProfile = {
  name: "Aarav Mehta",
  age: 34,
  avatar: "AM",
  bloodGroup: "B+",
  gender: "Male",
  phone: "+91 98765 43210",
  email: "aarav.mehta@example.com",
  address: "Bengaluru, Karnataka",
  emergencyContact: "+91 98765 43210",
  allergies: "Penicillin",
  chronicConditions: "Type 2 diabetes risk",
  currentMedications: "Vitamin D3, Metformin",
  assignedDoctor: "Dr. Meera Iyer",
  insuranceProvider: "MediCare Plus",
  status: "Stable",
  risk: "Low",
  lastCheckup: "29 Apr 2026",
};

const patientDashboard = {
  patient: defaultPatientProfile,
  appointment: {
    doctor: "Dr. Arjun Sharma",
    department: "General Medicine",
    date: "02 May 2026",
    time: "10:30 AM",
    status: "Confirmed",
  },
  medications: [
    { name: "Vitamin D3", time: "08:00 AM", status: "Taken" },
    { name: "Metformin", time: "08:00 PM", status: "Pending" },
  ],
  vitals: [
    { label: "Heart Rate", value: "76", unit: "bpm", state: "normal", icon: Heart },
    { label: "Blood Pressure", value: "118/78", unit: "mmHg", state: "normal", icon: Activity },
    { label: "Temperature", value: "98.4", unit: "F", state: "normal", icon: Thermometer },
    { label: "Oxygen Level", value: "98", unit: "%", state: "normal", icon: Droplets },
    { label: "Blood Sugar", value: "126", unit: "mg/dL", state: "caution", icon: Cross },
    { label: "Weight", value: "72", unit: "kg", state: "info", icon: Weight },
  ],
  reports: [
    { name: "CBC Blood Report", date: "28 Apr 2026", status: "Reviewed", flag: "Normal" },
    { name: "Fasting Glucose", date: "25 Apr 2026", status: "AI summary ready", flag: "Caution" },
  ],
  symptoms: { entry: "Mild headache", severity: 3, lastUpdated: "Today, 8:15 AM" },
  notes: ["Continue hydration", "Repeat glucose test next month", "Bring previous reports to next visit"],
  trends: {
    bp: [118, 122, 120, 119, 118, 121, 118],
    sugar: [132, 128, 130, 126, 124, 129, 126],
    weight: [73, 72.8, 72.5, 72.4, 72.2, 72, 72],
  },
};

const medicalDepartments = [
  "General Medicine",
  "Cardiology",
  "Dermatology",
  "Neurology",
  "Orthopedics",
  "Pediatrics",
  "Gynecology",
  "ENT",
  "Ophthalmology",
  "Psychiatry",
  "Dentistry",
  "Gastroenterology",
  "Pulmonology",
  "Endocrinology",
  "Nephrology",
  "Urology",
  "Oncology",
  "Physiotherapy",
];

function api(path, options = {}) {
  const token = localStorage.getItem("mediguide_token");
  return fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Request failed");
    return data;
  });
}

function doctorApi(path, options = {}) {
  const token = localStorage.getItem("mediguide_doctor_token");
  return fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Request failed");
    return data;
  });
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("mediguide_user");
    return stored ? JSON.parse(stored) : null;
  });

  useEffect(() => {
    if (!localStorage.getItem("mediguide_token")) return;
    api("/api/auth/me").then(setUser).catch(() => logout());
  }, []);

  function saveAuth(auth) {
    localStorage.setItem("mediguide_token", auth.access_token);
    localStorage.setItem("mediguide_user", JSON.stringify(auth.user));
    setUser(auth.user);
  }

  function logout() {
    localStorage.removeItem("mediguide_token");
    localStorage.removeItem("mediguide_user");
    setUser(null);
  }

  const value = useMemo(() => ({ user, saveAuth, logout, isAuthed: Boolean(user) }), [user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function useAuth() {
  return useContext(AuthContext);
}

function ProtectedRoute({ children }) {
  const { isAuthed } = useAuth();
  return isAuthed ? children : <Navigate to="/login" replace />;
}

function Landing() {
  const [authMode, setAuthMode] = useState(null);
  const features = [
    ["Symptom Checker", "Follow-up questions and AI-guided risk review for MediGuide AI users.", Activity],
    ["Disease Prediction", "ML-style health predictions shown as educational probabilities.", Brain],
    ["Medical Chatbot", "Protected MediGuide AI chatbot with safety-first medical guardrails.", Bot],
    ["OCR Analysis", "Upload reports and prescriptions for AI-assisted medical summaries.", FileText],
    ["Smart Scheduling", "AI agent scheduling with real-time conflict checks and doctor matching.", CalendarClock],
  ];

  return (
    <main>
      <nav className="topbar">
        <Link className="brand" to="/"><span><HeartPulse size={22} /></span>MediGuide AI</Link>
        <div className="nav-actions">
          <button className="btn secondary" onClick={() => setAuthMode("doctor")}><Stethoscope size={16} /> Doctor Login</button>
          <button className="btn secondary" onClick={() => setAuthMode("login")}>Login</button>
          <button className="btn primary" onClick={() => setAuthMode("signup")}>Sign Up</button>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-copy">
          <div className="pill"><ShieldCheck size={16} /> MediGuide AI clinical support</div>
          <h1>MediGuide AI</h1>
          <p>
            A secure healthcare assistant for symptom analysis, disease prediction, report OCR,
            appointment scheduling, risk triage, health history, and doctor escalation guidance.
          </p>
          <div className="hero-actions">
            <button className="btn primary large" onClick={() => setAuthMode("signup")}><UserPlus size={18} /> Start Securely</button>
            <button className="btn secondary large" onClick={() => setAuthMode("login")}>Login</button>
            <button className="btn secondary large" onClick={() => setAuthMode("doctor")}><Stethoscope size={18} /> Doctor Login</button>
          </div>
          <div className="disclaimer">
            MediGuide AI provides AI-assisted health information only and is not a replacement for a licensed medical professional.
          </div>
        </div>
      </section>

      <section className="clinical-strip">
        <div><Cross size={18} /><strong>Medical-first UI</strong><span>White, teal, blue, and navy theme</span></div>
        <div><ShieldCheck size={18} /><strong>Safety disclaimer</strong><span>No final diagnosis claims</span></div>
        <div><Stethoscope size={18} /><strong>Doctor escalation</strong><span>For serious or unclear cases</span></div>
      </section>

      <section className="preview-grid">
        {features.map(([title, desc, Icon]) => (
          <article className="preview-card" key={title}>
            <Icon />
            <h3>{title}</h3>
            <p>{desc}</p>
            <span>Login required</span>
          </article>
        ))}
      </section>
      {authMode && <LandingAuthModal mode={authMode} setMode={setAuthMode} onClose={() => setAuthMode(null)} />}
    </main>
  );
}

function LandingAuthModal({ mode, setMode, onClose }) {
  const navigate = useNavigate();
  const { saveAuth } = useAuth();
  const isSignup = mode === "signup";
  const isDoctor = mode === "doctor";
  const [form, setForm] = useState(isDoctor ? { email: "dentist@mediguide.ai", password: "Dentist@123", name: "" } : { name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setError("");
    setForm(mode === "doctor" ? { email: "dentist@mediguide.ai", password: "Dentist@123", name: "" } : { name: "", email: "", password: "" });
  }, [mode]);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isDoctor) {
        const result = await doctorApi("/api/doctor/login", { method: "POST", body: JSON.stringify({ email: form.email, password: form.password }) });
        localStorage.setItem("mediguide_doctor_token", result.access_token);
        localStorage.setItem("mediguide_doctor", JSON.stringify(result.doctor));
        navigate("/doctor/dashboard");
        return;
      }
      const auth = await api(`/api/auth/${isSignup ? "signup" : "login"}`, {
        method: "POST",
        body: JSON.stringify(isSignup ? form : { email: form.email, password: form.password }),
      });
      saveAuth(auth);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-modal-backdrop" role="dialog" aria-modal="true" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <form className="auth-card auth-modal-card" onSubmit={submit}>
        <button className="auth-modal-close" type="button" aria-label="Close login box" onClick={onClose}>x</button>
        <span className="secure-badge">{isDoctor ? <Stethoscope size={16} /> : <ShieldCheck size={16} />} {isDoctor ? "Doctor-only access" : "Secure patient access"}</span>
        <h1>{isDoctor ? "Doctor Login" : isSignup ? "Create your account" : "Welcome back"}</h1>
        <p>{isDoctor ? "Access patient requests and appointment workflow." : "Sign in to use MediGuide AI protected health tools."}</p>
        <div className="auth-mode-tabs">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Patient Login</button>
          <button type="button" className={mode === "signup" ? "active" : ""} onClick={() => setMode("signup")}>Sign Up</button>
          <button type="button" className={mode === "doctor" ? "active" : ""} onClick={() => setMode("doctor")}>Doctor</button>
        </div>
        {isSignup && (
          <label>Name<input required minLength="2" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        )}
        <label>Email<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
        <label>Password<input required minLength="8" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
        {error && <div className="error">{error}</div>}
        <button className="btn primary full" disabled={loading}>{loading ? "Please wait..." : isDoctor ? "Login as Doctor" : isSignup ? "Sign Up" : "Login"}</button>
        {isDoctor && <small>Dentist demo: dentist@mediguide.ai / Dentist@123</small>}
      </form>
    </div>
  );
}

function AuthPage({ mode }) {
  const isSignup = mode === "signup";
  const navigate = useNavigate();
  const { saveAuth, isAuthed } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthed) navigate("/dashboard");
  }, [isAuthed, navigate]);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const auth = await api(`/api/auth/${isSignup ? "signup" : "login"}`, {
        method: "POST",
        body: JSON.stringify(isSignup ? form : { email: form.email, password: form.password }),
      });
      saveAuth(auth);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <Link className="brand" to="/"><span><HeartPulse size={22} /></span>MediGuide AI</Link>
      <form className="auth-card" onSubmit={submit}>
        <h1>{isSignup ? "Create your account" : "Welcome back"}</h1>
        <p>Authentication is required before accessing dashboard tools.</p>
        {isSignup && (
          <label>Name<input required minLength="2" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        )}
        <label>Email<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
        <label>Password<input required minLength="8" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
        {error && <div className="error">{error}</div>}
        <button className="btn primary full" disabled={loading}>{loading ? "Please wait..." : isSignup ? "Sign Up" : "Login"}</button>
        <Link to={isSignup ? "/login" : "/signup"}>{isSignup ? "Already have an account? Login" : "Need an account? Sign up"}</Link>
      </form>
    </main>
  );
}

function DashboardLayout() {
  const { user, logout } = useAuth();
  const [active, setActive] = useState("overview");
  const [theme, setTheme] = useState(() => localStorage.getItem("mediguide_theme") || "light");
  const [profile, setProfile] = useState(() => {
    const stored = localStorage.getItem("mediguide_patient_profile");
    return stored ? { ...defaultPatientProfile, ...JSON.parse(stored) } : defaultPatientProfile;
  });
  const sections = [
    ["overview", "Dashboard", Menu],
    ["appointments", "Appointments", CalendarClock],
    ["medications", "Medications", Pill],
    ["report", "Reports", FileText],
    ["symptoms", "Symptoms", Activity],
    ["chat", "AI Assistant", Bot],
    ["emergency", "Emergency", AlertTriangle],
    ["profile", "Profile", User],
    ["settings", "Settings", Settings],
  ];

  function updateProfile(nextProfile) {
    const initials = nextProfile.name
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "PT";
    const updated = { ...nextProfile, avatar: initials };
    localStorage.setItem("mediguide_patient_profile", JSON.stringify(updated));
    setProfile(updated);
  }

  function toggleTheme() {
    const nextTheme = theme === "light" ? "dark" : "light";
    localStorage.setItem("mediguide_theme", nextTheme);
    setTheme(nextTheme);
  }

  function logoutToLanding() {
    logout();
    window.location.replace("/");
  }

  return (
    <div className={`app-shell ${theme === "dark" ? "dark-theme" : ""}`}>
      <Sidebar sections={sections} active={active} setActive={setActive} profile={profile} user={user} logout={logoutToLanding} />
      <main className="dashboard">
        <DashboardHeader
          user={user}
          profile={profile}
          title={sections.find(([key]) => key === active)?.[1]}
          setActive={setActive}
          logout={logoutToLanding}
          theme={theme}
          toggleTheme={toggleTheme}
        />
        <ToolPanel active={active} setActive={setActive} profile={profile} updateProfile={updateProfile} />
        <div className="disclaimer">
          MediGuide AI provides AI-assisted health information only and is not a replacement for a licensed medical professional.
        </div>
      </main>
    </div>
  );
}

function Sidebar({ sections, active, setActive, profile, user, logout }) {
  return (
    <aside className="sidebar">
      <Link className="brand" to="/dashboard"><span><HeartPulse size={22} /></span>MediGuide AI</Link>
      <div className="user-box">Patient portal<strong>{profile.name || user?.name}</strong><small>Secure login active</small></div>
      <nav className="sidebar-nav" aria-label="Patient dashboard navigation">
        {sections.map(([key, label, Icon]) => (
          <button key={key} className={active === key ? "active" : ""} onClick={() => setActive(key)}>
            <Icon size={18} /> {label}
          </button>
        ))}
      </nav>
      <button className="sidebar-logout" onClick={logout}><LogOut size={18} /> Logout</button>
    </aside>
  );
}

function ToolPanel({ active, setActive, profile, updateProfile }) {
  if (active === "overview") return <PatientDashboardHome setActive={setActive} profile={profile} />;
  if (active === "symptoms") return <SymptomTool />;
  if (active === "chat") return <ChatTool />;
  if (active === "report") return <ReportTool />;
  if (active === "appointments") return <AppointmentTool />;
  if (active === "medications") return <MedicationPage />;
  if (active === "emergency") return <EmergencyPage />;
  if (active === "profile") return <ProfilePage profile={profile} updateProfile={updateProfile} />;
  if (active === "settings") return <SettingsPage />;
  return <PlaceholderPage title="Secure patient workspace" />;
}

function DashboardHeader({ user, profile, title, setActive, logout, theme, toggleTheme }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [appointmentNotifications, setAppointmentNotifications] = useState([]);

  async function loadPatientNotifications() {
    try {
      const items = await api("/api/appointments");
      const updates = items
        .filter((item) => ["accepted", "rejected", "rescheduled"].includes(item.status))
        .slice(0, 8)
        .map((item) => ({
          id: item.id,
          title: item.status === "accepted" ? "Appointment accepted" : item.status === "rejected" ? "Appointment rejected" : "Appointment rescheduled",
          body: `${item.doctor_name} ${item.status} your ${item.specialization} appointment.`,
          meta: new Date(item.starts_at).toLocaleString(),
          status: item.status,
        }));
      setAppointmentNotifications(updates);
    } catch {
      setAppointmentNotifications([]);
    }
  }

  useEffect(() => {
    loadPatientNotifications();
    const timer = window.setInterval(loadPatientNotifications, 30000);
    return () => window.clearInterval(timer);
  }, []);

  function goTo(section) {
    setMenuOpen(false);
    setActive(section);
  }

  return (
    <header className="patient-header">
      <div>
        <p>Secure patient dashboard</p>
        <h1>{title}</h1>
      </div>
      <div className="header-actions">
        <label className="dashboard-search">
          <Search size={18} />
          <input placeholder="Search reports, doctors, medicines" />
        </label>
        <div className="notification-wrap">
          <button
            className="icon-button"
            aria-label="Notifications"
            aria-expanded={notificationsOpen}
            onClick={() => {
              setMenuOpen(false);
              setNotificationsOpen((open) => !open);
              loadPatientNotifications();
            }}
          >
            <Bell size={18} />
            {!!appointmentNotifications.length && <span className="notification-count">{appointmentNotifications.length}</span>}
          </button>
          {notificationsOpen && (
            <div className="notification-dropdown">
              <div className="profile-dropdown-head">
                <strong>Appointment updates</strong>
                <span>{appointmentNotifications.length ? "Latest doctor decisions" : "No appointment decisions yet"}</span>
              </div>
              {!appointmentNotifications.length ? (
                <div className="notification-empty">Accepted or rejected appointments will appear here.</div>
              ) : appointmentNotifications.map((item) => (
                <button key={item.id} onClick={() => { setNotificationsOpen(false); setActive("appointments"); }}>
                  <span className={`status-dot ${item.status}`} />
                  <div>
                    <strong>{item.title}</strong>
                    <span>{item.body}</span>
                    <small>{item.meta}</small>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
        <button className="btn primary" onClick={() => setActive("appointments")}><CalendarClock size={18} /> Book Appointment</button>
        <div className="profile-menu-wrap">
          <button
            className="patient-avatar avatar-button"
            title="Open account menu"
            aria-label="Open account menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {profile.avatar}
          </button>
          {menuOpen && (
            <div className="profile-dropdown">
              <div className="profile-dropdown-head">
                <strong>{profile.name || user?.name}</strong>
                <span>{profile.email || user?.email}</span>
              </div>
              <button onClick={() => goTo("profile")}><User size={16} /> Profile</button>
              <button onClick={() => goTo("settings")}><Settings size={16} /> Settings</button>
              <button onClick={toggleTheme}>
                {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
                {theme === "light" ? "Dark theme" : "Light theme"}
              </button>
              <button className="logout-menu-item" onClick={logout}><LogOut size={16} /> Logout</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

function PatientDashboardHome({ setActive, profile }) {
  const { appointment, medications, vitals, reports, symptoms, notes, trends } = patientDashboard;
  return (
    <div className="patient-dashboard">
      <section className="priority-grid">
        <HealthSummaryCard patient={profile} onOpen={() => setActive("profile")} />
        <UpcomingAppointmentCard appointment={appointment} onOpen={() => setActive("appointments")} />
        <MedicationReminderCard medications={medications} onOpen={() => setActive("medications")} />
      </section>

      <section className="vitals-grid">
        {vitals.map((vital) => <VitalCard key={vital.label} vital={vital} onOpen={() => setActive("symptoms")} />)}
      </section>

      <section className="dashboard-split">
        <Card title="Health Trends" action="View symptoms" onAction={() => setActive("symptoms")}>
          <div className="chart-tabs">
            <MiniLineChart label="Blood pressure" color="#0f766e" data={trends.bp} />
            <MiniLineChart label="Blood sugar" color="#f59e0b" data={trends.sugar} />
            <MiniLineChart label="Weight" color="#2563eb" data={trends.weight} />
          </div>
        </Card>
        <Card title="AI Health Assistant" action="Open chat" onAction={() => setActive("chat")}>
          <div className="assistant-card">
            <Bot size={24} />
            <h3>Ask MediGuide AI</h3>
            <p>Summarize symptoms, prepare doctor questions, or explain report values.</p>
            <small>AI guidance is not a replacement for professional medical advice.</small>
          </div>
        </Card>
      </section>

      <section className="dashboard-split lower">
        <Card title="Recent Reports" action="Open reports" onAction={() => setActive("report")}>
          <div className="compact-list">
            {reports.length ? reports.map((report) => (
              <div className="list-row" key={report.name}>
                <FileText size={18} />
                <div><strong>{report.name}</strong><span>{report.date} - {report.status}</span></div>
                <button className={`status-pill action-pill ${report.flag.toLowerCase()}`} onClick={() => setActive("report")}>{report.flag}</button>
              </div>
            )) : <EmptyState text="No reports uploaded yet" />}
          </div>
        </Card>
        <Card title="Symptoms Tracker" action="Open symptoms" onAction={() => setActive("symptoms")}>
          <div className="symptom-preview">
            <span>Today</span>
            <strong>{symptoms.entry}</strong>
            <div className="severity-track"><i style={{ width: `${symptoms.severity * 10}%` }} /></div>
            <small>Severity {symptoms.severity}/10 - {symptoms.lastUpdated}</small>
          </div>
        </Card>
      </section>

      <section className="dashboard-split lower">
        <Card title="Doctor Notes" action="Ask AI" onAction={() => setActive("chat")}>
          <ul className="note-list">{notes.map((note) => <li key={note}>{note}</li>)}</ul>
        </Card>
        <EmergencySummary onOpen={() => setActive("emergency")} />
      </section>
    </div>
  );
}

function Card({ title, action, onAction, children }) {
  return <article className="dash-card"><div className="card-heading"><h2>{title}</h2>{action && <button onClick={onAction}>{action}<ChevronRight size={16} /></button>}</div>{children}</article>;
}

function HealthSummaryCard({ patient, onOpen }) {
  return (
    <Card title="Health Summary" action="Profile" onAction={onOpen}>
      <div className="summary-status">
        <span className="risk-dot low" />
        <div><strong>{patient.status}</strong><small>Current health status</small></div>
      </div>
      <div className="summary-meta">
        <span>Risk level <b className="green-text">{patient.risk}</b></span>
        <span>Last checkup <b>{patient.lastCheckup}</b></span>
        <span>Assigned doctor <b>{patient.assignedDoctor}</b></span>
        <span>Blood group <b>{patient.bloodGroup}</b></span>
      </div>
    </Card>
  );
}

function UpcomingAppointmentCard({ appointment, onOpen }) {
  return (
    <Card title="Upcoming Appointment" action="Reschedule" onAction={onOpen}>
      <div className="appointment-summary">
        <Stethoscope size={22} />
        <div><strong>{appointment.doctor}</strong><span>{appointment.department}</span></div>
      </div>
      <div className="summary-meta">
        <span>{appointment.date} <b>{appointment.time}</b></span>
        <span>Status <b className="blue-text">{appointment.status}</b></span>
      </div>
    </Card>
  );
}

function MedicationReminderCard({ medications, onOpen }) {
  return (
    <Card title="Medication Reminder" action="Medicines" onAction={onOpen}>
      <div className="compact-list">
        {medications.map((med) => (
          <div className="medicine-row" key={med.name}>
            <Pill size={18} />
            <div><strong>{med.name}</strong><span>{med.time}</span></div>
            <span className={`status-pill ${med.status.toLowerCase()}`}>{med.status}</span>
          </div>
        ))}
      </div>
      <p className="refill-note">Refill reminder: Metformin in 6 days</p>
    </Card>
  );
}

function VitalCard({ vital, onOpen }) {
  const Icon = vital.icon;
  return (
    <button className={`vital-card ${vital.state}`} onClick={onOpen}>
      <Icon size={19} />
      <span>{vital.label}</span>
      <strong>{vital.value}</strong>
      <small>{vital.unit}</small>
    </button>
  );
}

function MiniLineChart({ label, data, color }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 82 - ((value - min) / Math.max(max - min, 1)) * 58;
    return `${x},${y}`;
  }).join(" ");
  return (
    <div className="mini-chart">
      <div><strong>{label}</strong><span>{data[data.length - 1]}</span></div>
      <svg viewBox="0 0 100 90" preserveAspectRatio="none" aria-hidden="true">
        <polyline points={points} fill="none" stroke={color} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

function EmergencySummary({ onOpen }) {
  return (
    <article className="dash-card emergency-panel">
      <div className="card-heading"><h2>Emergency</h2><button onClick={onOpen}>Open<ChevronRight size={16} /></button></div>
      <div className="emergency-grid">
        <span>Emergency contact <b>+91 98765 43210</b></span>
        <span>Allergies <b>Penicillin</b></span>
        <span>Nearby hospital <b>CityCare Hospital</b></span>
      </div>
      <button className="sos-button" onClick={onOpen}><AlertTriangle size={18} /> SOS Assistance</button>
    </article>
  );
}

function EmptyState({ text }) {
  return <div className="empty">{text}</div>;
}

function ResultBox({ data }) {
  if (!data) return <div className="empty">No result yet. Submit the form to run the protected AI API.</div>;
  return <pre className="result">{JSON.stringify(data, null, 2)}</pre>;
}

function SymptomTool() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      setData(await api("/api/ai/symptom-analysis", {
        method: "POST",
        body: JSON.stringify({
          symptoms: form.get("symptoms").split(",").map((s) => s.trim()).filter(Boolean),
          age: Number(form.get("age")) || null,
          duration_days: Number(form.get("duration")) || null,
          severity: Number(form.get("severity")) || 4,
          language: form.get("language"),
        }),
      }));
    } catch (err) { setError(err.message); }
  }
  return <FormTool title="Symptom checker with follow-up questions" onSubmit={submit} error={error}>
    <input name="symptoms" placeholder="fever, cough, headache" required />
    <div className="row"><input name="age" placeholder="Age" /><input name="duration" placeholder="Duration days" /><input name="severity" placeholder="Severity 1-10" /></div>
    <select name="language"><option>English</option><option>Hindi</option><option>Tamil</option><option>Kannada</option><option>Telugu</option><option>Malayalam</option></select>
    <button className="btn primary">Analyze symptoms</button><ResultBox data={data} />
  </FormTool>;
}

function PredictionTool() {
  const [data, setData] = useState(null);
  async function submit(event) {
    event.preventDefault();
    const symptoms = new FormData(event.currentTarget).get("symptoms").split(",").map((s) => s.trim()).filter(Boolean);
    setData(await api("/api/ai/disease-prediction", { method: "POST", body: JSON.stringify({ symptoms }) }));
  }
  return <FormTool title="ML-based disease prediction" onSubmit={submit}><input name="symptoms" required placeholder="sore throat, fever" /><button className="btn primary">Predict</button><ResultBox data={data} /></FormTool>;
}

function ChatTool() {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    const message = form.get("message");
    event.currentTarget.reset();
    try {
      const result = await api("/api/ai/chat", { method: "POST", body: JSON.stringify({ message, language: form.get("language") || "English" }) });
      setMessages((prev) => [...prev, { message, result }]);
    } catch (err) { setError(err.message); }
  }
  return <FormTool title="Medical chatbot" onSubmit={submit} error={error}><textarea name="message" required placeholder="Ask a medical support question..." /><select name="language"><option>English</option><option>Hindi</option><option>Tamil</option></select><button className="btn primary">Send</button><ResultBox data={messages} /></FormTool>;
}

function ReportTool() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState("");
  async function submit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData();
    const file = event.currentTarget.file.files[0];
    form.append("file", file);
    try {
      setData(await api("/api/ai/report-ocr", { method: "POST", body: form }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <section className="panel wide-panel report-page">
      <div className="report-hero">
        <div>
          <span className="secure-badge"><ShieldCheck size={16} /> Protected OCR analysis</span>
          <h2>Medical report OCR analysis</h2>
          <p>Upload lab reports, prescriptions, or medical documents. MediGuide AI extracts text, summarizes key values, and flags items that may need a doctor review.</p>
        </div>
        <div className="report-stats">
          <div><strong>PDF/Image</strong><span>Accepted</span></div>
          <div><strong>AI Summary</strong><span>Guardrailed</span></div>
          <div><strong>Private</strong><span>JWT protected</span></div>
        </div>
      </div>

      <div className="report-workspace">
        <form className="report-upload-card" onSubmit={submit}>
          <div className="upload-dropzone">
            <Upload size={34} />
            <h3>Upload medical report</h3>
            <p>Supported formats: PDF, PNG, JPG, JPEG, and WEBP. Keep the report clear and readable for better OCR extraction.</p>
            <label className="file-picker">
              <input
                type="file"
                name="file"
                accept="image/png,image/jpeg,image/webp,application/pdf"
                required
                onChange={(event) => setFileName(event.target.files?.[0]?.name || "")}
              />
              <span>{fileName || "Choose a report file"}</span>
            </label>
          </div>
          {error && <div className="error">{error}</div>}
          <button className="btn primary report-action" disabled={loading}>{loading ? "Analyzing report..." : "Upload and analyze"}</button>
        </form>

        <aside className="report-result-card">
          <div className="card-heading">
            <div>
              <h3>AI report summary</h3>
              <p>Results appear here after OCR processing.</p>
            </div>
            <FileText size={24} />
          </div>
          {loading ? (
            <div className="empty report-empty">Scanning document and extracting medical values...</div>
          ) : data ? (
            <div className="report-result-layout">
              <div className="report-summary-strip">
                <span className="status-pill normal">OCR complete</span>
                <span className="status-pill info">AI reviewed</span>
                <span className="status-pill pending">Doctor approval advised</span>
              </div>
              <pre className="result report-result">{JSON.stringify(data, null, 2)}</pre>
            </div>
          ) : (
            <div className="report-empty-state">
              <FileText size={42} />
              <strong>No report analyzed yet</strong>
              <p>Choose a medical report on the left and run protected OCR analysis.</p>
            </div>
          )}
        </aside>
      </div>

      <div className="report-guide-grid">
        <article>
          <strong>What AI extracts</strong>
          <span>Report text, medication names, lab values, dates, and readable clinical notes.</span>
        </article>
        <article>
          <strong>Safety handling</strong>
          <span>Abnormal or unclear values are presented as informational and not final diagnosis.</span>
        </article>
        <article>
          <strong>Next step</strong>
          <span>Use the summary to prepare questions for your licensed medical professional.</span>
        </article>
      </div>
    </section>
  );
}

function AppointmentTool() {
  const [tab, setTab] = useState("book");
  const [recommendations, setRecommendations] = useState(null);
  const [appointments, setAppointments] = useState(null);
  const [history, setHistory] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastRequest, setLastRequest] = useState(null);
  const [patientNote, setPatientNote] = useState("");
  const [voiceStatus, setVoiceStatus] = useState("Voice note ready");
  const [doctors, setDoctors] = useState(null);
  const [doctorFilters, setDoctorFilters] = useState({ search: "", specialization: "" });
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [doctorAvailability, setDoctorAvailability] = useState(null);
  const recognitionRef = useRef(null);

  async function loadAppointments() {
    setAppointments(await api("/api/appointments"));
  }

  async function loadHistory() {
    setHistory(await api("/api/appointments/history"));
  }

  async function loadDoctors(filters = doctorFilters) {
    const params = new URLSearchParams();
    if (filters.search) params.set("search", filters.search);
    if (filters.specialization) params.set("specialization", filters.specialization);
    params.set("limit", "600");
    setDoctors(await api(`/api/doctors?${params.toString()}`));
  }

  useEffect(() => {
    loadAppointments().catch(() => setAppointments([]));
    loadHistory().catch(() => setHistory([]));
    loadDoctors().catch(() => setDoctors([]));
  }, []);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    const form = new FormData(event.currentTarget);
    const payload = {
      specialization: form.get("specialization"),
      urgency_level: form.get("urgency_level"),
      preferred_time_range: form.get("preferred_time_range"),
      current_datetime: form.get("current_datetime") || null,
      duration_minutes: Number(form.get("duration")) || 30,
      location: form.get("location") || "",
      doctor_gender: form.get("doctor_gender"),
      language: form.get("language") || "",
      confirm_booking_after_validation: form.get("confirm_booking") === "on",
      patient_note: patientNote.trim(),
    };

    try {
      const result = await api("/api/appointments/recommend", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setLastRequest(payload);
      setRecommendations(result);
      setTab(result.status === "confirmed" ? "appointments" : "book");
      if (result.status === "confirmed") setSuccess("Appointment request sent to the doctor after validation.");
      loadAppointments();
      loadHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function bookSlot(slot) {
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const booked = await api("/api/appointments/book", {
        method: "POST",
        body: JSON.stringify({
          doctor_id: slot.doctor_id,
          starts_at: slot.starts_at,
          duration_minutes: lastRequest?.duration_minutes || 30,
          urgency_level: lastRequest?.urgency_level || "medium",
          specialization: slot.specialization,
          reasoning: recommendations?.reasoning || "Booked from AI scheduling recommendation.",
          patient_note: lastRequest?.patient_note || "",
          preferred_time_range: lastRequest?.preferred_time_range || "",
          recommendation_reason: slot.recommendation_reason || recommendations?.reasoning || "",
        }),
      });
      setSuccess(`Appointment request sent to ${booked.doctor_name}. The doctor will accept, reject, or reschedule it.`);
      loadAppointments();
      loadHistory();
      setTab("appointments");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function cancelAppointment(id) {
    setError("");
    setSuccess("");
    try {
      await api(`/api/appointments/${id}/cancel`, {
        method: "PUT",
        body: JSON.stringify({ reason: "Cancelled by patient from dashboard." }),
      });
      setSuccess("Appointment cancelled. The slot is available again.");
      loadAppointments();
      loadHistory();
    } catch (err) {
      setError(err.message);
    }
  }

  function startVoiceNote() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceStatus("Speech recognition not supported");
      return;
    }
    if (recognitionRef.current) recognitionRef.current.stop();
    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onstart = () => setVoiceStatus("Listening...");
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript || "")
        .join(" ")
        .trim();
      if (transcript) {
        setPatientNote((current) => `${current}${current ? " " : ""}${transcript}`.trim());
        setVoiceStatus("Voice note added");
      }
    };
    recognition.onerror = () => setVoiceStatus("Speech recognition not supported");
    recognition.onend = () => {
      recognitionRef.current = null;
      setVoiceStatus((current) => current === "Listening..." ? "Processing..." : current);
    };
    recognitionRef.current = recognition;
    recognition.start();
  }

  function stopVoiceNote() {
    if (recognitionRef.current) {
      setVoiceStatus("Processing...");
      recognitionRef.current.stop();
    }
  }

  async function filterDoctors(event) {
    event.preventDefault();
    setError("");
    try {
      await loadDoctors(doctorFilters);
    } catch (err) {
      setError(err.message);
      setDoctors([]);
    }
  }

  async function viewDoctorAvailability(doctor) {
    setError("");
    setSuccess("");
    setSelectedDoctor(doctor);
    setDoctorAvailability(null);
    try {
      const params = new URLSearchParams({ duration_minutes: String(doctor.appointment_duration_minutes || 30) });
      setDoctorAvailability(await api(`/api/doctors/${doctor.id}/availability?${params.toString()}`));
    } catch (err) {
      setError(err.message);
      setDoctorAvailability({ availability: [] });
    }
  }

  async function bookSpecificDoctorSlot(slot) {
    if (!selectedDoctor) return;
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const booked = await api("/api/appointments/book", {
        method: "POST",
        body: JSON.stringify({
          doctor_id: slot.doctor_id,
          starts_at: slot.starts_at,
          duration_minutes: selectedDoctor.appointment_duration_minutes || 30,
          urgency_level: "medium",
          specialization: selectedDoctor.specialization,
          reasoning: `Patient selected ${selectedDoctor.name} from the doctor directory and requested a validated available slot.`,
          patient_note: "",
          preferred_time_range: "",
          recommendation_reason: "Direct doctor-specific booking from validated doctor availability.",
        }),
      });
      setSuccess(`Appointment request sent to ${booked.doctor_name}. The doctor will accept, reject, or reschedule it.`);
      loadAppointments();
      loadHistory();
      setTab("appointments");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const aiUnderstanding = recommendations?.ai_understanding;
  const tabLabels = {
    book: "Book Appointment",
    doctors: "Doctors",
    recommendations: "Recommendations",
    appointments: "My Appointments",
    history: "History",
  };

  return (
    <section className="panel wide-panel schedule-page schedule-wide">
      <h2>Schedule Appointment</h2>
      <p>
        AI scheduling uses doctor availability, patient preferences, urgency, specialization,
        location, language, gender preference, history, cancellations, and conflict checks.
      </p>
      <div className="schedule-tabs">
        {["book", "doctors", "recommendations", "appointments", "history"].map((item) => (
          <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>
            {tabLabels[item]}
          </button>
        ))}
      </div>
      {error && <div className="error">{error}</div>}
      {success && <div className="success modal-success">{success}</div>}
      {loading && <div className="empty">Running scheduling agent...</div>}

      {tab === "book" && (
        <form className="tool-form schedule-form" onSubmit={submit}>
          <div className="schedule-workspace">
            <section className="schedule-card schedule-form-card">
              <div>
                <h3>Appointment details</h3>
                <p>Choose the medical need and practical scheduling constraints.</p>
              </div>
              <div className="schedule-fields">
                <label>Specialization
                  <select name="specialization" defaultValue="General Medicine" required>
                    {medicalDepartments.map((department) => <option key={department}>{department}</option>)}
                  </select>
                </label>
                <label>Urgency
                  <select name="urgency_level" defaultValue="medium" required>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </label>
                <label>Preferred time
                  <select name="preferred_time_range" defaultValue="evening">
                    <option value="any">Any</option>
                    <option value="morning">Morning</option>
                    <option value="afternoon">Afternoon</option>
                    <option value="evening">Evening</option>
                  </select>
                </label>
                <label>Current date/time<input name="current_datetime" type="datetime-local" /></label>
                <label>Duration<input name="duration" type="number" min="15" max="120" defaultValue="30" required /></label>
                <label>Clinic/location<input name="location" placeholder="Central Clinic" /></label>
                <label>Doctor gender
                  <select name="doctor_gender" defaultValue="any">
                    <option value="any">Any</option>
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                  </select>
                </label>
                <label>Language<input name="language" placeholder="Hindi" /></label>
                <label className="checkbox-line inline-check"><input name="confirm_booking" type="checkbox" /> Confirm after validation</label>
              </div>
              <button className="btn primary schedule-run" disabled={loading}>{loading ? "Running agent..." : "Run Scheduling Agent"}</button>
            </section>

            <aside className="schedule-card ai-note-card">
              <div className="note-heading">
                <div>
                  <h3>Patient Note for AI Scheduler</h3>
                  <p>Tell the agent about symptoms, preferred doctor, unavailable times, travel needs, or follow-up context.</p>
                </div>
                <span className={`voice-status ${voiceStatus === "Listening..." ? "active" : ""}`}><Mic size={15} /> {voiceStatus}</span>
              </div>
              <div className="voice-actions">
                <button className="btn secondary" type="button" onClick={startVoiceNote}><Mic size={16} /> Start Voice Note</button>
                <button className="btn secondary" type="button" onClick={stopVoiceNote}>Stop Recording</button>
              </div>
              <textarea
                className="patient-note"
                value={patientNote}
                onChange={(event) => setPatientNote(event.target.value)}
                placeholder="Example: I prefer evening appointments after 5 PM. I need a Hindi-speaking doctor near Central Clinic. I cannot come on Monday morning."
              />
              <div className="ai-summary-panel">
                <h4>AI understanding summary</h4>
                {!aiUnderstanding ? (
                  <p className="muted">Run the scheduling agent to see how MediGuide AI interpreted your form and note.</p>
                ) : (
                  <div className="summary-chips">
                    <span>Need: {aiUnderstanding.structured_fields?.specialization}</span>
                    <span>Urgency: {aiUnderstanding.patient_note_intent?.urgency_hint || aiUnderstanding.structured_fields?.urgency}</span>
                    <span>Time: {aiUnderstanding.patient_note_intent?.preferred_time_range || aiUnderstanding.structured_fields?.preferred_time}</span>
                    <span>Language: {aiUnderstanding.patient_note_intent?.language || aiUnderstanding.structured_fields?.language || "Flexible"}</span>
                    <span>Location: {aiUnderstanding.patient_note_intent?.location || aiUnderstanding.structured_fields?.location || "Flexible"}</span>
                  </div>
                )}
              </div>
            </aside>
          </div>
        </form>
      )}

      {tab === "doctors" && (
        <section className="schedule-section doctors-directory-section">
          <div className="section-heading-row">
            <div>
              <h3>All doctors</h3>
              <p>Review available MediGuide doctors before sending an appointment request.</p>
            </div>
            <span className="status-pill info">{doctors?.length || 0} listed</span>
          </div>
          <form className="doctor-directory-filters" onSubmit={filterDoctors}>
            <label>Search doctors
              <input
                value={doctorFilters.search}
                onChange={(event) => setDoctorFilters((current) => ({ ...current, search: event.target.value }))}
                placeholder="Search name, clinic, language, city"
              />
            </label>
            <label>Specialization
              <select
                value={doctorFilters.specialization}
                onChange={(event) => setDoctorFilters((current) => ({ ...current, specialization: event.target.value }))}
              >
                <option value="">All specializations</option>
                {medicalDepartments.map((department) => <option key={department}>{department}</option>)}
              </select>
            </label>
            <button className="btn secondary" type="submit"><Search size={16} /> Filter</button>
          </form>
          {!doctors ? (
            <div className="empty">Loading doctors...</div>
          ) : !doctors.length ? (
            <EmptyState text="No doctors match the current filters." />
          ) : (
            <>
              {selectedDoctor && (
                <article className="selected-doctor-booking">
                  <div className="section-heading-row">
                    <div>
                      <h3>Book {selectedDoctor.name}</h3>
                      <p>{selectedDoctor.specialization} - {selectedDoctor.clinic?.name || selectedDoctor.location}</p>
                    </div>
                    <button className="btn secondary" type="button" onClick={() => { setSelectedDoctor(null); setDoctorAvailability(null); }}>Close</button>
                  </div>
                  {!doctorAvailability ? (
                    <div className="empty">Loading available time slots...</div>
                  ) : !doctorAvailability.availability?.length ? (
                    <EmptyState text="No open slots found for this doctor right now." />
                  ) : (
                    <div className="specific-slot-grid">
                      {doctorAvailability.availability.map((slot) => (
                        <article className="specific-slot-card" key={`${slot.doctor_id}-${slot.starts_at}`}>
                          <span className="status-pill normal">Available</span>
                          <strong>{slot.date}</strong>
                          <span>{slot.time}</span>
                          <small>{selectedDoctor.appointment_duration_minutes || 30} min consultation</small>
                          <button className="btn primary" type="button" disabled={loading} onClick={() => bookSpecificDoctorSlot(slot)}>
                            Request this time
                          </button>
                        </article>
                      ))}
                    </div>
                  )}
                </article>
              )}
              <div className="patient-doctor-grid">
                {doctors.map((doctor) => (
                  <article className="patient-doctor-card" key={doctor.id}>
                    <div className="doctor-card-top">
                      <div className="doctor-avatar-mark"><Stethoscope size={20} /></div>
                      <div>
                        <strong>{doctor.name}</strong>
                        <span>{doctor.specialization}</span>
                      </div>
                      <span className="status-pill normal">{doctor.rating ? `${doctor.rating} rating` : "Active"}</span>
                    </div>
                    <p>{doctor.about_doctor || `${doctor.qualification || "Medical specialist"} with ${doctor.experience_years || 0} years of experience.`}</p>
                    <div className="doctor-detail-list">
                      <span><b>Clinic</b>{doctor.clinic?.name || doctor.location}</span>
                      <span><b>Location</b>{[doctor.clinic?.area, doctor.clinic?.city].filter(Boolean).join(", ") || doctor.location}</span>
                      <span><b>Experience</b>{doctor.experience_years || 0} years</span>
                      <span><b>Fee</b>{doctor.consultation_fee ? `Rs ${doctor.consultation_fee}` : "Not listed"}</span>
                      <span><b>Gender</b>{doctor.gender}</span>
                      <span><b>Mode</b>{doctor.online_consultation ? "Online / clinic" : doctor.consultation_modes || "Clinic"}</span>
                    </div>
                    <div className="doctor-language-list">
                      {(doctor.languages || []).slice(0, 4).map((language) => <span key={language}>{language}</span>)}
                    </div>
                    <div className="doctor-card-actions">
                      <button className="btn primary" type="button" onClick={() => viewDoctorAvailability(doctor)}>Book this doctor</button>
                      <button
                        className="btn secondary"
                        type="button"
                        onClick={() => {
                          setDoctorFilters({ search: doctor.name, specialization: doctor.specialization });
                          loadDoctors({ search: doctor.name, specialization: doctor.specialization }).catch(() => setDoctors([]));
                          viewDoctorAvailability(doctor);
                        }}
                      >
                        View availability
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </>
          )}
        </section>
      )}
      {tab === "recommendations" && (
        <section className="schedule-section">
          <h3>Recommended appointment slots</h3>
          {!recommendations?.recommended_slots?.length ? <EmptyState text="No recommendations yet. Run the scheduling agent first." /> : (
            <div className="slot-grid">
              {recommendations.recommended_slots.map((slot) => (
                <article className="slot-card" key={`${slot.doctor_id}-${slot.starts_at}`}>
                  <span className="status-pill normal">Available</span>
                  <strong>{slot.doctor_name}</strong>
                  <p>{slot.specialization} - {slot.clinic}</p>
                  <b>{slot.date} at {slot.time}</b>
                  <small>Score {slot.score} - Confidence {Math.round((slot.confidence_score || 0) * 100)}% - {slot.language_match ? "Language match" : "Language flexible"}</small>
                  <p>{slot.recommendation_reason}</p>
                  <details><summary>Score details</summary><pre>{JSON.stringify(slot.score_breakdown, null, 2)}</pre></details>
                  <button className="btn primary" onClick={() => bookSlot(slot)}>Confirm this slot</button>
                </article>
              ))}
            </div>
          )}
          {recommendations?.reasoning && <p className="agent-reasoning">{recommendations.reasoning}</p>}
        </section>
      )}

      {tab === "appointments" && (
        <section className="schedule-section">
          <h3>My appointments</h3>
          {!appointments?.length ? <EmptyState text="No appointments booked yet." /> : (
            <div className="appointment-list">
              {appointments.map((item) => (
                <article key={item.id} className="appointment-item">
                  <strong>{item.doctor_name}</strong>
                  <span>{item.specialization}</span>
                  <span>{new Date(item.starts_at).toLocaleString()} - {item.status}</span>
                  {item.status === "confirmed" && (
                    <div className="row compact-actions">
                      <button className="btn secondary" onClick={() => setTab("book")}>Reschedule</button>
                      <button className="btn secondary danger" onClick={() => cancelAppointment(item.id)}>Cancel</button>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      {tab === "history" && (
        <section className="schedule-section">
          <h3>Appointment history</h3>
          {!history?.length ? <EmptyState text="No appointment history yet." /> : (
            <div className="appointment-list">
              {history.map((item) => (
                <article key={item.id} className="appointment-item">
                  <strong>{item.action}</strong>
                  <span>{item.details || "No details provided"}</span>
                  <span>{new Date(item.created_at).toLocaleString()}</span>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </section>
  );
}

function MedicationPage() {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadCatalog(nextSearch = search, nextCategory = category) {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (nextSearch.trim()) params.set("search", nextSearch.trim());
      if (nextCategory) params.set("category", nextCategory);
      params.set("limit", "80");
      const [catalog, categoryList] = await Promise.all([
        api(`/api/medications/catalog?${params.toString()}`),
        categories.length ? Promise.resolve(categories) : api("/api/medications/catalog/categories"),
      ]);
      setItems(catalog);
      setCategories(categoryList);
    } catch (err) {
      setError(err.message);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCatalog("", "");
  }, []);

  function submit(event) {
    event.preventDefault();
    loadCatalog(search, category);
  }

  return (
    <section className="panel wide-panel medication-page">
      <div className="profile-title-row">
        <div>
          <span className="secure-badge"><Pill size={16} /> Medication catalog</span>
          <h2>Medication tracker</h2>
          <p>Search the 200-medicine catalog for tracker display, common use labels, and prescription status.</p>
        </div>
      </div>

      <div className="medication-layout">
        <aside className="dash-card medication-reminders">
          <div className="card-heading"><h2>Today</h2></div>
          <div className="compact-list">
            {patientDashboard.medications.map((med) => (
              <div className="medicine-row" key={med.name}>
                <Pill size={18} />
                <div><strong>{med.name}</strong><span>{med.time}</span></div>
                <span className={`status-pill ${med.status.toLowerCase()}`}>{med.status}</span>
              </div>
            ))}
          </div>
          <p className="refill-note">Refill reminder: Metformin in 6 days</p>
        </aside>

        <div className="dash-card medication-catalog">
          <div className="card-heading">
            <div>
              <h2>Medicine catalog</h2>
              <p>For medication tracking only. Do not use this catalog for prescribing or dosing.</p>
            </div>
            <span className="status-pill info">{items.length} shown</span>
          </div>
          <form className="filter-row medication-filters" onSubmit={submit}>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by medicine, generic name, category, or use case" />
            <select value={category} onChange={(event) => { setCategory(event.target.value); loadCatalog(search, event.target.value); }}>
              <option value="">All categories</option>
              {categories.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <button className="btn primary" disabled={loading}>{loading ? "Searching..." : "Search"}</button>
          </form>
          {error && <div className="error">{error}</div>}
          {loading ? <EmptyState text="Loading medication catalog..." /> : !items.length ? <EmptyState text="No medicines found" /> : (
            <div className="medication-grid">
              {items.map((item) => (
                <article className="medication-card" key={item.med_code}>
                  <div className="medication-card-head">
                    <div>
                      <strong>{item.name}</strong>
                      <span>{item.generic_name}</span>
                    </div>
                    <span className={`status-pill ${item.rx_required ? "pending" : "normal"}`}>{item.rx_required ? "Rx" : "OTC"}</span>
                  </div>
                  <div className="medication-meta">
                    <span>{item.category}</span>
                    <span>{item.form}</span>
                    <span>{item.default_strength}</span>
                    <span>{item.route}</span>
                  </div>
                  <p>{item.common_uses}</p>
                  <small>{item.patient_note}</small>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function EmergencyPage() {
  return (
    <section className="panel wide-panel">
      <h2>Emergency information</h2>
      <p>Critical contacts and warnings are kept short and visible for quick action.</p>
      <EmergencySummary onOpen={() => {}} />
    </section>
  );
}

function ProfilePage({ profile, updateProfile }) {
  const [form, setForm] = useState(profile);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setForm(profile);
  }, [profile]);

  function change(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function submit(event) {
    event.preventDefault();
    updateProfile({ ...form, age: Number(form.age) || "" });
    setMessage("Profile updated. Dashboard summary refreshed.");
  }

  return (
    <section className="panel wide-panel">
      <div className="profile-title-row">
        <div>
          <h2>Patient profile</h2>
          <p>Update medical details used across the MediGuide AI dashboard.</p>
        </div>
        <span className="secure-badge"><ShieldCheck size={16} /> Privacy protected</span>
      </div>

      <div className="profile-overview">
        <div className="patient-avatar large">{profile.avatar}</div>
        <div>
          <strong>{profile.name}</strong>
          <span>Age {profile.age} - Blood group {profile.bloodGroup}</span>
          <span>Assigned doctor: {profile.assignedDoctor}</span>
        </div>
      </div>

      <form className="profile-form" onSubmit={submit}>
        <fieldset>
          <legend>Basic information</legend>
          <div className="form-grid">
            <label>Full name<input value={form.name} onChange={(e) => change("name", e.target.value)} required /></label>
            <label>Age<input type="number" min="0" max="120" value={form.age} onChange={(e) => change("age", e.target.value)} required /></label>
            <label>Gender<select value={form.gender} onChange={(e) => change("gender", e.target.value)}><option>Female</option><option>Male</option><option>Other</option><option>Prefer not to say</option></select></label>
            <label>Blood group<select value={form.bloodGroup} onChange={(e) => change("bloodGroup", e.target.value)}><option>A+</option><option>A-</option><option>B+</option><option>B-</option><option>AB+</option><option>AB-</option><option>O+</option><option>O-</option></select></label>
          </div>
        </fieldset>

        <fieldset>
          <legend>Contact details</legend>
          <div className="form-grid">
            <label>Phone number<input value={form.phone} onChange={(e) => change("phone", e.target.value)} /></label>
            <label>Email<input type="email" value={form.email} onChange={(e) => change("email", e.target.value)} /></label>
            <label>Address<input value={form.address} onChange={(e) => change("address", e.target.value)} /></label>
            <label>Emergency contact<input value={form.emergencyContact} onChange={(e) => change("emergencyContact", e.target.value)} /></label>
          </div>
        </fieldset>

        <fieldset>
          <legend>Medical details</legend>
          <div className="form-grid">
            <label>Current health status<select value={form.status} onChange={(e) => change("status", e.target.value)}><option>Stable</option><option>Needs monitoring</option><option>Recovering</option><option>Urgent review needed</option></select></label>
            <label>Risk level<select value={form.risk} onChange={(e) => change("risk", e.target.value)}><option>Low</option><option>Medium</option><option>High</option></select></label>
            <label>Last checkup date<input value={form.lastCheckup} onChange={(e) => change("lastCheckup", e.target.value)} /></label>
            <label>Assigned doctor<input value={form.assignedDoctor} onChange={(e) => change("assignedDoctor", e.target.value)} /></label>
            <label>Allergies<textarea value={form.allergies} onChange={(e) => change("allergies", e.target.value)} /></label>
            <label>Chronic conditions<textarea value={form.chronicConditions} onChange={(e) => change("chronicConditions", e.target.value)} /></label>
            <label>Current medications<textarea value={form.currentMedications} onChange={(e) => change("currentMedications", e.target.value)} /></label>
            <label>Insurance provider<input value={form.insuranceProvider} onChange={(e) => change("insuranceProvider", e.target.value)} /></label>
          </div>
        </fieldset>

        {message && <div className="success">{message}</div>}
        <button className="btn primary" type="submit">Save profile</button>
      </form>
    </section>
  );
}

function SettingsPage() {
  return (
    <section className="panel wide-panel">
      <h2>Settings</h2>
      <div className="settings-grid">
        <label className="checkbox-line"><input type="checkbox" defaultChecked /> Appointment reminders</label>
        <label className="checkbox-line"><input type="checkbox" defaultChecked /> Report notifications</label>
        <label className="checkbox-line"><input type="checkbox" defaultChecked /> Secure session indicator</label>
      </div>
    </section>
  );
}

function PlaceholderPage({ title }) {
  return <section className="panel"><h2>{title}</h2><EmptyState text="This secure patient section is ready for detailed records, filters, and workflow screens." /></section>;
}

function HistoryTool() {
  const [items, setItems] = useState(null);
  const [message, setMessage] = useState("");
  async function load() { setItems(await api("/api/health-history")); }
  async function save() {
    await api("/api/health-history", { method: "POST", body: JSON.stringify({ title: "Demo symptom review", category: "Symptom Checker", risk_level: "Low", risk_score: 24, summary: "Saved secure health history entry." }) });
    setMessage("Saved sample history item.");
    load();
  }
  useEffect(() => { load().catch(() => setItems([])); }, []);
  return <section className="panel"><h2>Health history save/fetch</h2><p>{message || "Your history is empty until analyses are saved."}</p><button className="btn primary" onClick={save}>Save sample history</button><ResultBox data={items} /></section>;
}

function RiskTool() {
  const [data, setData] = useState(null);
  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setData(await api("/api/ai/risk-score", { method: "POST", body: JSON.stringify({ symptoms: form.get("symptoms").split(","), severity: Number(form.get("severity")), duration_days: Number(form.get("duration")), age: Number(form.get("age")) || null }) }));
  }
  return <FormTool title="Risk score tracker" onSubmit={submit}><input name="symptoms" placeholder="symptoms" required /><div className="row"><input name="severity" placeholder="Severity" required /><input name="duration" placeholder="Duration" required /><input name="age" placeholder="Age" /></div><button className="btn primary">Calculate risk</button><ResultBox data={data} /></FormTool>;
}

function LanguageVoiceTool() {
  const [data, setData] = useState(null);
  return <section className="panel"><h2>Multi-language support + voice input</h2><p>Frontend supports language selection. Backend exposes a protected voice transcription endpoint for Whisper/Web Speech/Hugging Face integration.</p><button className="btn primary" onClick={() => api("/api/ai/voice-transcription", { method: "POST" }).then(setData)}>Check voice API</button><ResultBox data={data} /></section>;
}

function FormTool({ title, onSubmit, error, children }) {
  return <section className="panel"><h2>{title}</h2><form className="tool-form" onSubmit={onSubmit}>{children}</form>{error && <div className="error">{error}</div>}</section>;
}

function DoctorProtectedRoute({ children }) {
  return localStorage.getItem("mediguide_doctor_token") ? children : <Navigate to="/doctor/login" replace />;
}

function DoctorLoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "dentist@mediguide.ai", password: "Dentist@123" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await doctorApi("/api/doctor/login", { method: "POST", body: JSON.stringify(form) });
      localStorage.setItem("mediguide_doctor_token", result.access_token);
      localStorage.setItem("mediguide_doctor", JSON.stringify(result.doctor));
      navigate("/doctor/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell doctor-auth-shell">
      <Link className="brand" to="/"><span><Stethoscope size={22} /></span>MediGuide AI Doctor</Link>
      <form className="auth-card doctor-login-card" onSubmit={submit}>
        <span className="secure-badge"><ShieldCheck size={16} /> Doctor-only access</span>
        <h1>Doctor Login</h1>
        <p>Access appointments, patient requests, AI scheduling notes, and availability management.</p>
        <label>Email<input type="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label>
        <label>Password<input type="password" required minLength="8" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label>
        {error && <div className="error">{error}</div>}
        <button className="btn primary full" disabled={loading}>{loading ? "Signing in..." : "Login"}</button>
        <a href="#forgot">Forgot password?</a>
        <small>Dentist demo: dentist@mediguide.ai / Dentist@123</small>
      </form>
    </main>
  );
}

function DoctorPortal({ page }) {
  const navigate = useNavigate();
  const [doctor, setDoctor] = useState(() => {
    const stored = localStorage.getItem("mediguide_doctor");
    return stored ? JSON.parse(stored) : null;
  });
  const [toast, setToast] = useState("");
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [requestNotifications, setRequestNotifications] = useState([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem("mediguide_doctor_theme") || "light");
  const nav = [
    ["dashboard", "Dashboard", "/doctor/dashboard", Activity],
    ["appointments", "Appointments", "/doctor/appointments", CalendarClock],
    ["requests", "Patient Requests", "/doctor/patient-requests", ClipboardList],
    ["availability", "Availability", "/doctor/availability", CalendarClock],
    ["ai-notes", "AI Scheduling Notes", "/doctor/dashboard?tab=ai-notes", Bot],
    ["profile", "Profile", "/doctor/profile", User],
  ];

  useEffect(() => {
    doctorApi("/api/doctor/me").then(setDoctor).catch(() => logout());
  }, []);

  async function loadDoctorNotifications() {
    try {
      const items = await doctorApi("/api/doctor/patient-requests");
      setRequestNotifications(items.slice(0, 8));
    } catch {
      setRequestNotifications([]);
    }
  }

  useEffect(() => {
    loadDoctorNotifications();
    const timer = window.setInterval(loadDoctorNotifications, 30000);
    return () => window.clearInterval(timer);
  }, []);

  function logout() {
    localStorage.removeItem("mediguide_doctor_token");
    localStorage.removeItem("mediguide_doctor");
    navigate("/", { replace: true });
  }

  function toggleTheme() {
    const nextTheme = theme === "light" ? "dark" : "light";
    localStorage.setItem("mediguide_doctor_theme", nextTheme);
    setTheme(nextTheme);
  }

  function goToDoctor(path) {
    setMenuOpen(false);
    setNotificationsOpen(false);
    navigate(path);
  }

  function showToast(message) {
    setToast(message);
    setTimeout(() => setToast(""), 2600);
  }

  const active = page === "requests" ? "requests" : page === "availability" ? "availability" : page === "profile" ? "profile" : page === "appointments" ? "appointments" : "dashboard";
  return (
    <div className={`doctor-shell ${theme === "dark" ? "dark-theme" : ""}`}>
      <aside className="doctor-sidebar">
        <Link className="brand" to="/doctor/dashboard"><span><Stethoscope size={22} /></span>MediGuide Doctor</Link>
        <div className="doctor-card-mini">
          <div className="patient-avatar">{doctor?.full_name?.split(" ").map((p) => p[0]).slice(0, 2).join("") || "DR"}</div>
          <strong>{doctor?.full_name || "Doctor"}</strong>
          <span>{doctor?.specialization || "Specialist"}</span>
        </div>
        <nav className="sidebar-nav">
          {nav.map(([key, label, href, Icon]) => (
            <button key={key} className={active === key ? "active" : ""} onClick={() => navigate(href)}>
              <Icon size={18} /> {label}
            </button>
          ))}
        </nav>
        <button className="sidebar-logout" onClick={logout}><LogOut size={18} /> Logout</button>
      </aside>
      <main className="doctor-main">
        <header className="doctor-topbar">
          <div>
            <p>Doctor workspace</p>
            <h1>{page === "availability" ? "Availability" : page === "requests" ? "Patient Requests" : page === "profile" ? "Doctor Profile" : page === "appointments" ? "Appointments" : "Doctor Dashboard"}</h1>
          </div>
          <div className="header-actions">
            <div className="notification-wrap">
              <button
                className="icon-button"
                aria-label="Doctor notifications"
                aria-expanded={notificationsOpen}
                onClick={() => {
                  setMenuOpen(false);
                  setNotificationsOpen((open) => !open);
                  loadDoctorNotifications();
                }}
              >
                <Bell size={18} />
                {!!requestNotifications.length && <span className="notification-count">{requestNotifications.length}</span>}
              </button>
              {notificationsOpen && (
                <div className="notification-dropdown doctor-notifications">
                  <div className="profile-dropdown-head">
                    <strong>Patient requests</strong>
                    <span>{requestNotifications.length ? "New appointment requests" : "No pending patient requests"}</span>
                  </div>
                  {!requestNotifications.length ? (
                    <div className="notification-empty">New patient appointment requests will appear here.</div>
                  ) : requestNotifications.map((item) => (
                    <button key={item.id} onClick={() => { setNotificationsOpen(false); navigate("/doctor/patient-requests"); }}>
                      <span className="status-dot pending" />
                      <div>
                        <strong>{item.patient_name} requested an appointment</strong>
                        <span>{item.reason_for_visit} - {item.urgency_level} urgency</span>
                        <small>{new Date(item.appointment_time).toLocaleString()}</small>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="profile-menu-wrap">
              <button
                className="patient-avatar avatar-button"
                title="Open doctor account menu"
                aria-label="Open doctor account menu"
                aria-expanded={menuOpen}
                onClick={() => {
                  setNotificationsOpen(false);
                  setMenuOpen((open) => !open);
                }}
              >
                {doctor?.full_name?.split(" ").map((p) => p[0]).slice(0, 2).join("") || "DR"}
              </button>
              {menuOpen && (
                <div className="profile-dropdown doctor-profile-dropdown">
                  <div className="profile-dropdown-head">
                    <strong>{doctor?.full_name || "Doctor"}</strong>
                    <span>{doctor?.email || doctor?.specialization || "Doctor account"}</span>
                  </div>
                  <button onClick={() => goToDoctor("/doctor/profile")}><User size={16} /> Profile</button>
                  <button onClick={() => goToDoctor("/doctor/availability")}><Settings size={16} /> Settings</button>
                  <button onClick={toggleTheme}>
                    {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
                    {theme === "light" ? "Dark theme" : "Light theme"}
                  </button>
                  <button className="logout-menu-item" onClick={logout}><LogOut size={16} /> Logout</button>
                </div>
              )}
            </div>
          </div>
        </header>
        {toast && <div className="success doctor-toast">{toast}</div>}
        {page === "availability" ? <DoctorAvailabilityPage showToast={showToast} /> : page === "requests" ? <DoctorRequestsPage showToast={showToast} /> : page === "profile" ? <DoctorProfilePage doctor={doctor} setDoctor={setDoctor} showToast={showToast} /> : page === "appointments" ? <DoctorAppointmentsPage showToast={showToast} /> : <DoctorDashboardPage showToast={showToast} />}
      </main>
    </div>
  );
}

function DoctorDashboardPage({ showToast }) {
  const [data, setData] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      const [dashboard, appointmentList] = await Promise.all([
        doctorApi("/api/doctor/dashboard"),
        doctorApi("/api/doctor/appointments"),
      ]);
      setData(dashboard);
      setAppointments(appointmentList);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function action(id, type, body = {}) {
    await doctorApi(`/api/doctor/appointments/${id}/${type}`, { method: "PATCH", body: JSON.stringify(body) });
    showToast(`Appointment ${type} updated.`);
    load();
  }

  if (error) return <div className="error">{error}</div>;
  if (!data) return <EmptyState text="Loading doctor dashboard..." />;
  const cards = data.cards;
  const archivedStatuses = ["completed", "rejected", "cancelled"];
  const isArchived = (item) => archivedStatuses.includes(item.status);
  const activeAppointments = appointments.filter((item) => !isArchived(item));
  const upcomingAppointments = [...activeAppointments]
    .filter((item) => new Date(item.appointment_time).getTime() >= Date.now() - 60000)
    .sort((a, b) => new Date(a.appointment_time) - new Date(b.appointment_time))
    .slice(0, 6);
  return (
    <div className="doctor-page">
      <section className="doctor-profile-summary">
        <div>
          <span className="secure-badge"><ShieldCheck size={16} /> Active doctor account</span>
          <h2>{data.doctor.full_name}</h2>
          <p>{data.doctor.specialization} at {data.doctor.hospital_or_clinic_name}</p>
        </div>
        <div className="doctor-availability-pill">{data.availability_status}</div>
      </section>
      <section className="doctor-stat-grid">
        {[
          ["Today", cards.total_appointments_today],
          ["Pending", cards.pending_requests],
          ["Completed", cards.completed_consultations],
          ["Cancelled", cards.cancelled_appointments],
          ["Avg Duration", cards.average_consultation_duration],
          ["Next", cards.next_appointment_time ? new Date(cards.next_appointment_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "None"],
        ].map(([label, value]) => <article className="doctor-stat" key={label}><span>{label}</span><strong>{value}</strong></article>)}
      </section>
      <section className="doctor-grid-two">
        <DoctorAppointmentPanel title="Upcoming appointments" items={upcomingAppointments} onAction={action} />
        <DoctorAINotesPanel notes={data.ai_scheduling_suggestions} patientNotes={data.patient_notes} />
      </section>
    </div>
  );
}

function DoctorAppointmentsPage({ showToast }) {
  const [appointments, setAppointments] = useState([]);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const items = await doctorApi(`/api/doctor/appointments?search=${encodeURIComponent(search)}&status_filter=${encodeURIComponent(status)}`);
      setAppointments(items);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function action(id, type, body = {}) {
    await doctorApi(`/api/doctor/appointments/${id}/${type}`, { method: "PATCH", body: JSON.stringify(body) });
    showToast(`Appointment ${type} updated.`);
    load();
  }

  const archivedStatuses = ["completed", "rejected", "cancelled"];
  const isArchived = (item) => archivedStatuses.includes(item.status);
  const activeAppointments = [...appointments]
    .filter((item) => !isArchived(item))
    .sort((a, b) => new Date(a.appointment_time) - new Date(b.appointment_time));
  const archivedAppointments = [...appointments]
    .filter(isArchived)
    .sort((a, b) => new Date(b.appointment_time) - new Date(a.appointment_time));

  if (error) return <div className="doctor-page error">{error}</div>;

  return (
    <div className="doctor-page">
      <section className="dash-card doctor-appointments-panel">
        <div className="card-heading doctor-panel-heading">
          <div>
            <h2>Active appointments</h2>
            <p>Pending, accepted, and rescheduled appointments that still need doctor action.</p>
          </div>
          <span className="status-pill pending">{activeAppointments.filter((item) => item.status === "pending").length} pending</span>
        </div>
        <form className="doctor-filters" onSubmit={(e) => { e.preventDefault(); load(); }}>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search patient name" />
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            {["pending", "accepted", "rescheduled", "completed", "rejected", "cancelled"].map((item) => <option key={item}>{item}</option>)}
          </select>
          <button className="btn primary">Filter</button>
        </form>
        <DoctorAppointmentList items={activeAppointments} onAction={action} emptyText="No active appointments. Completed and rejected items are in the archive." />
      </section>
      <section className="dash-card doctor-appointments-panel archive-panel">
        <div className="card-heading doctor-panel-heading">
          <div>
            <h2>Archive</h2>
            <p>Completed, rejected, and cancelled appointments are stored here to keep active work clear.</p>
          </div>
          <span className="status-pill">{archivedAppointments.length} archived</span>
        </div>
        <DoctorAppointmentList items={archivedAppointments} onAction={action} compact emptyText="No archived appointments yet." />
      </section>
    </div>
  );
}

function DoctorAppointmentPanel({ title, items, onAction }) {
  return <section className="dash-card"><div className="card-heading"><h2>{title}</h2></div><DoctorAppointmentList items={items} onAction={onAction} compact emptyText="No upcoming active appointments." /></section>;
}

function DoctorAppointmentList({ items, onAction, compact = false, emptyText = "No appointments yet" }) {
  const [notes, setNotes] = useState({});
  if (!items?.length) return <EmptyState text={emptyText} />;
  return (
    <div className={compact ? "doctor-appointment-list compact" : "doctor-appointment-list"}>
      {items.map((item) => (
        <article className="doctor-appointment-card clean" key={item.id}>
          <div className="doctor-appointment-time">
            <strong>{new Date(item.appointment_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</strong>
            <span>{new Date(item.appointment_time).toLocaleDateString([], { month: "short", day: "numeric" })}</span>
          </div>
          <div className="doctor-appointment-body">
            <div className="doctor-appointment-title">
              <div>
                <strong>{item.patient_name}</strong>
                <span>{item.patient_email || "Patient"} - Age {item.patient_age || "N/A"}</span>
              </div>
              <span className={`status-pill ${item.status === "completed" ? "normal" : item.status === "pending" ? "pending" : item.status === "cancelled" || item.status === "rejected" ? "danger" : ""}`}>{item.status}</span>
            </div>
            <div className="doctor-appointment-meta">
              <span><b>Reason</b>{item.reason_for_visit}</span>
              <span><b>Urgency</b>{item.urgency_level}</span>
              <span><b>Best time</b>{item.suggested_best_time_slot}</span>
            </div>
            {(item.patient_note || item.symptoms || item.ai_recommendation) && (
              <div className="doctor-appointment-note">
                {item.patient_note && <p><b>Patient note:</b> {item.patient_note}</p>}
                {item.symptoms && <p><b>Symptoms:</b> {item.symptoms}</p>}
                <p><b>AI scheduling:</b> {item.ai_recommendation || "No AI recommendation yet"}</p>
              </div>
            )}
            {!compact && !["completed", "cancelled", "rejected"].includes(item.status) && (
              <textarea
                value={notes[item.id] || ""}
                onChange={(e) => setNotes((current) => ({ ...current, [item.id]: e.target.value }))}
                placeholder="Private doctor note before marking complete..."
              />
            )}
            <div className="doctor-actions">
              {item.status === "pending" && <button className="btn primary" onClick={() => onAction(item.id, "accept")}>Accept</button>}
              {item.status === "pending" && <button className="btn secondary danger" onClick={() => onAction(item.id, "reject", { reason: "Rejected by doctor from dashboard." })}>Reject</button>}
              {!["completed", "cancelled", "rejected"].includes(item.status) && <button className="btn secondary" onClick={() => onAction(item.id, "complete", { note_text: notes[item.id] || "" })}>Mark complete</button>}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function DoctorAINotesPanel({ notes, patientNotes }) {
  return (
    <section className="dash-card">
      <div className="card-heading"><h2>AI Scheduling Notes</h2></div>
      <div className="doctor-note-list">
        {!notes?.length ? <EmptyState text="No AI scheduling notes yet" /> : notes.map((note) => (
          <article key={note.id}>
            <strong>{note.suggested_slot}</strong>
            <span>{note.recommendation_text}</span>
            <small>{note.reason} • Confidence {Math.round(note.confidence_score * 100)}%</small>
          </article>
        ))}
      </div>
      <div className="card-heading secondary-heading"><h2>Patient Notes</h2></div>
      <div className="doctor-note-list">
        {!patientNotes?.length ? <EmptyState text="No patient notes submitted" /> : patientNotes.map((note) => (
          <article key={note.id}><strong>{note.urgency_level}</strong><span>{note.note_text}</span><small>{note.voice_transcription}</small></article>
        ))}
      </div>
    </section>
  );
}

function DoctorRequestsPage({ showToast }) {
  const [items, setItems] = useState([]);
  async function load() { setItems(await doctorApi("/api/doctor/patient-requests")); }
  useEffect(() => { load().catch(() => setItems([])); }, []);
  async function action(id, type) {
    await doctorApi(`/api/doctor/appointments/${id}/${type}`, { method: "PATCH", body: JSON.stringify({ reason: `${type} from patient requests.` }) });
    showToast(`Request ${type}.`);
    load();
  }
  return <section className="doctor-page dash-card"><div className="card-heading"><h2>Pending patient requests</h2><span className="status-pill pending">{items.length} pending</span></div><DoctorAppointmentList items={items} onAction={action} /></section>;
}

function DoctorAvailabilityPage({ showToast }) {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ day_of_week: 1, start_time: "09:00", end_time: "17:00", slot_duration_minutes: 30, is_available: true, max_patients_per_slot: 1, emergency_only: false });
  async function load() { setItems(await doctorApi("/api/doctor/availability")); }
  useEffect(() => { load().catch(() => setItems([])); }, []);
  async function submit(event) {
    event.preventDefault();
    await doctorApi("/api/doctor/availability", { method: "POST", body: JSON.stringify({ ...form, day_of_week: Number(form.day_of_week), slot_duration_minutes: Number(form.slot_duration_minutes), max_patients_per_slot: Number(form.max_patients_per_slot) }) });
    showToast("Availability added.");
    load();
  }
  async function remove(id) {
    await doctorApi(`/api/doctor/availability/${id}`, { method: "DELETE" });
    showToast("Availability removed.");
    load();
  }
  return (
    <div className="doctor-page doctor-grid-two">
      <form className="dash-card profile-form" onSubmit={submit}>
        <h2>Weekly availability</h2>
        <div className="form-grid">
          <label>Day<select value={form.day_of_week} onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}>{["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].map((d, i) => <option key={d} value={i}>{d}</option>)}</select></label>
          <label>Start time<input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} /></label>
          <label>End time<input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} /></label>
          <label>Duration<input type="number" value={form.slot_duration_minutes} onChange={(e) => setForm({ ...form, slot_duration_minutes: e.target.value })} /></label>
          <label>Max patients<input type="number" value={form.max_patients_per_slot} onChange={(e) => setForm({ ...form, max_patients_per_slot: e.target.value })} /></label>
          <label className="checkbox-line"><input type="checkbox" checked={form.emergency_only} onChange={(e) => setForm({ ...form, emergency_only: e.target.checked })} /> Emergency-only slot</label>
        </div>
        <button className="btn primary">Add availability</button>
      </form>
      <section className="dash-card">
        <div className="card-heading"><h2>Current slots</h2></div>
        <div className="doctor-note-list">
          {!items.length ? <EmptyState text="No availability added" /> : items.map((item) => <article key={item.id}><strong>Day {item.day_of_week}: {item.start_time} - {item.end_time}</strong><span>{item.slot_duration_minutes} min • max {item.max_patients_per_slot}</span><button className="btn danger" onClick={() => remove(item.id)}>Delete</button></article>)}
        </div>
      </section>
    </div>
  );
}

function DoctorProfilePage({ doctor, setDoctor, showToast }) {
  const [form, setForm] = useState(doctor || {});
  useEffect(() => setForm(doctor || {}), [doctor]);
  async function submit(event) {
    event.preventDefault();
    const updated = await doctorApi("/api/doctor/profile", { method: "PATCH", body: JSON.stringify(form) });
    setDoctor(updated);
    localStorage.setItem("mediguide_doctor", JSON.stringify(updated));
    showToast("Profile updated.");
  }
  if (!doctor) return <EmptyState text="Loading profile..." />;
  return (
    <form className="doctor-page dash-card profile-form" onSubmit={submit}>
      <div className="profile-title-row"><div><h2>Doctor profile</h2><p>Email and license number are locked for compliance.</p></div><span className="secure-badge">License {doctor.license_number}</span></div>
      <div className="form-grid">
        <label>Full name<input value={form.full_name || ""} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></label>
        <label>Email<input value={doctor.email} disabled /></label>
        <label>License number<input value={doctor.license_number} disabled /></label>
        <label>Specialization<input value={form.specialization || ""} onChange={(e) => setForm({ ...form, specialization: e.target.value })} /></label>
        <label>Phone<input value={form.phone_number || ""} onChange={(e) => setForm({ ...form, phone_number: e.target.value })} /></label>
        <label>Clinic/hospital<input value={form.hospital_or_clinic_name || ""} onChange={(e) => setForm({ ...form, hospital_or_clinic_name: e.target.value })} /></label>
        <label>Consultation fee<input type="number" value={form.consultation_fee || 0} onChange={(e) => setForm({ ...form, consultation_fee: Number(e.target.value) })} /></label>
        <label>Languages<input value={form.languages || ""} onChange={(e) => setForm({ ...form, languages: e.target.value })} /></label>
        <label>Experience years<input type="number" value={form.experience_years || 0} onChange={(e) => setForm({ ...form, experience_years: Number(e.target.value) })} /></label>
        <label>Mode<select value={form.consultation_modes || "both"} onChange={(e) => setForm({ ...form, consultation_modes: e.target.value })}><option>online</option><option>offline</option><option>both</option></select></label>
        <label>Profile photo URL<input value={form.profile_image || ""} onChange={(e) => setForm({ ...form, profile_image: e.target.value })} /></label>
        <label>About doctor<textarea value={form.about_doctor || ""} onChange={(e) => setForm({ ...form, about_doctor: e.target.value })} /></label>
      </div>
      <button className="btn primary">Save profile</button>
    </form>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/signup" element={<AuthPage mode="signup" />} />
          <Route path="/dashboard" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>} />
          <Route path="/doctor/login" element={<DoctorLoginPage />} />
          <Route path="/doctor/dashboard" element={<DoctorProtectedRoute><DoctorPortal page="dashboard" /></DoctorProtectedRoute>} />
          <Route path="/doctor/appointments" element={<DoctorProtectedRoute><DoctorPortal page="appointments" /></DoctorProtectedRoute>} />
          <Route path="/doctor/patient-requests" element={<DoctorProtectedRoute><DoctorPortal page="requests" /></DoctorProtectedRoute>} />
          <Route path="/doctor/availability" element={<DoctorProtectedRoute><DoctorPortal page="availability" /></DoctorProtectedRoute>} />
          <Route path="/doctor/profile" element={<DoctorProtectedRoute><DoctorPortal page="profile" /></DoctorProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")).render(<App />);
