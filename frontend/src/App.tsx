import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Boxes,
  Users,
  BrainCircuit,
  Settings,
  LogOut,
  Building2,
  ShieldCheck,
  Bell,
  Plus,
  Eye,
  EyeOff,
  ArrowRight,
  Check,
  Moon,
  Sun,
  BarChart3,
  AlertTriangle,
  Activity,
  Wallet,
  ShoppingCart,
  ClipboardCheck,
  UserCog,
  UsersRound,
  ServerCog,
  FileClock,
} from "lucide-react";
import "./dashboard.css";


const API = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(
  /\/$/,
  "",
);

type User = {
  id: number;
  full_name: string;
  email: string;
  role: string;
  company_id: number | null;
};

function StartupSplash() {
  return (
    <div className="startup-splash" role="status" aria-label="Loading SMARTERP">
      <div className="startup-orbit startup-orbit-one" />
      <div className="startup-orbit startup-orbit-two" />
      <div className="startup-logo-wrap">
        <span className="startup-logo">S</span>
      </div>
      <div className="startup-wordmark">SMARTERP</div>
      <p>Smart enterprise resource planning</p>
      <div className="startup-progress"><span /></div>
    </div>
  );
}

async function call(path: string, token: string, opts: RequestInit = {}) {
  const response = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || data.message || "Request failed");
  }

  return data;
}

function AuthScreen({ onAuthenticated }: { onAuthenticated: (token: string) => void }) {
  const [screen, setScreen] = useState<"login" | "register">("login");
  const [email, setEmail] = useState(localStorage.getItem("smarterp_pending_email") || "");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [dark, setDark] = useState(localStorage.getItem("smarterp_auth_theme") === "dark");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleTransition, setGoogleTransition] = useState(false);
  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotStep, setForgotStep] = useState<"request" | "reset">("request");
  const [resetPassword, setResetPassword] = useState("");
  const [resetConfirm, setResetConfirm] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    firstName: "", lastName: "", phone: "", company: "", businessType: "Private Limited",
    country: "India", state: "", city: "", gstin: "", website: "", confirmPassword: "", terms: false,
  });
  useEffect(() => {
    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const oauthToken = hash.get("oauth_token");
    const oauthError = hash.get("oauth_error");
    if (oauthToken) {
      window.history.replaceState({}, document.title, window.location.pathname);
      onAuthenticated(oauthToken);
    } else if (oauthError) {
      setError(decodeURIComponent(oauthError));
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [onAuthenticated]);

  const update = (key: keyof typeof form, value: string | boolean) =>
    setForm((current) => ({ ...current, [key]: value }));
  const passwordChecks = {
    length: password.length >= 8,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };
  const passwordScore = Object.values(passwordChecks).filter(Boolean).length;
  const run = async (action: () => Promise<void>) => {
    setLoading(true); setError(""); setNotice("");
    try { await action(); } catch (e: any) { setError(e.message || "Something went wrong. Please try again."); }
    finally { setLoading(false); }
  };
  const startGoogleAuth = () => {
    setError("");
    setNotice("");
    setGoogleLoading(true);
    setGoogleTransition(true);
    window.setTimeout(() => {
      window.location.href = `${API}/api/auth/google/login`;
    }, 1100);
  };
  const submitForgot = async (event: React.FormEvent) => {
    event.preventDefault();
    await run(async () => {
      if (forgotStep === "request") {
        await call("/api/auth/forgot-password", "", {
          method: "POST",
          body: JSON.stringify({ email }),
        });
        setForgotStep("reset");
        setNotice("If the account exists, a reset code has been sent.");
      } else {
        const checks = {
          length: resetPassword.length >= 8,
          upper: /[A-Z]/.test(resetPassword),
          lower: /[a-z]/.test(resetPassword),
          number: /\d/.test(resetPassword),
          special: /[^A-Za-z0-9]/.test(resetPassword),
        };
        if (Object.values(checks).some((valid) => !valid)) {
          throw new Error("Use at least 8 characters with uppercase, lowercase, number, and special character.");
        }
        if (resetPassword !== resetConfirm) throw new Error("Passwords do not match.");
        await call("/api/auth/reset-password", "", {
          method: "POST",
          body: JSON.stringify({ email, otp, password: resetPassword }),
        });
        setForgotOpen(false);
        setForgotStep("request");
        setOtp("");
        setResetPassword("");
        setResetConfirm("");
        setNotice("Password updated successfully. You can now sign in.");
      }
    });
  };
  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (screen === "login") return run(async () => {
      const data = await call("/api/auth/login", "", { method: "POST", body: JSON.stringify({ email, password }) });
      if (remember) localStorage.setItem("smarterp_token", data.access_token);
      onAuthenticated(data.access_token);
    });
    if (screen === "register") {
      if (passwordScore < 5) { setError("Choose a stronger password that meets every requirement."); return; }
      if (password !== form.confirmPassword) { setError("Passwords do not match."); return; }
      if (!form.terms) { setError("Accept the Terms of Service and Privacy Policy to continue."); return; }
      return run(async () => {
        await call("/api/auth/register", "", { method: "POST", body: JSON.stringify({
          first_name: form.firstName, last_name: form.lastName, full_name: `${form.firstName} ${form.lastName}`,
          email, phone: form.phone, password, company_name: form.company, business_type: form.businessType,
          country: form.country, state: form.state, city: form.city, gstin: form.gstin || null,
          website: form.website || null,
        }) });
        localStorage.setItem("smarterp_pending_email", email);
        setScreen("login"); setNotice("Account created. Check your email and complete verification before signing in.");
      });
    }
  };

  const title = screen === "login" ? "Welcome back" : "Create your SMARTERP account";
  const subtitle = screen === "login" ? "Sign in to manage your business smarter." :
    "Start managing your business with a smarter, more powerful ERP platform.";

  return (
    <div className={`auth-shell ${dark ? "auth-dark" : ""}`}>
      <div className="auth-glow auth-glow-one" /><div className="auth-glow auth-glow-two" />
      <div className="auth-topbar">
        <button className="auth-brand" onClick={() => setScreen("login")}><span className="auth-logo">S</span><span>SMARTERP</span></button>
        <button className="theme-toggle" onClick={() => { const next = !dark; setDark(next); localStorage.setItem("smarterp_auth_theme", next ? "dark" : "light"); }}>
          {dark ? <Sun size={16} /> : <Moon size={16} />} {dark ? "Light mode" : "Dark mode"}
        </button>
      </div>
      <div className="auth-layout">
        <section className="auth-visual">
          <div className="visual-kicker"><span className="visual-kicker-dot" /> ONE PLATFORM. EVERY BUSINESS.</div>
          <h2>Run your business with clarity and confidence.</h2>
          <p>Bring finance, people, inventory, sales, and operations together in one beautifully connected workspace.</p>
          <div className="visual-dashboard">
            <div className="visual-dashboard-top"><span>Business overview</span><span className="visual-live"><i /> Live</span></div>
            <div className="visual-metric-row"><div><small>Net revenue</small><strong>₹24.8L</strong></div><div><small>Growth</small><strong className="visual-positive">+18.6%</strong></div></div>
            <div className="visual-chart"><i /><i /><i /><i /><i /><i /><i /><i /></div>
            <div className="visual-dashboard-bottom"><span>All systems connected</span><b>●</b></div>
          </div>
          <div className="visual-points"><span><Check size={14} /> Real-time insights</span><span><Check size={14} /> Secure by design</span></div>
        </section>
        <main className={`auth-card ${screen === "register" ? "auth-card-wide" : ""} ${screen === "login" ? "auth-login-card" : "auth-register-card"}`}>
          <div className="auth-card-heading"><span className="eyebrow">{screen === "login" ? "WELCOME TO SMARTERP" : "SMART ENTERPRISE RESOURCE PLANNING"}</span><h1>{title}</h1><p>{subtitle}</p></div>
          <form onSubmit={submit} className="auth-form">
          {screen === "register" && <div className="auth-section">
            <h2>Personal information</h2><div className="auth-grid">
              <label>First name<input required value={form.firstName} onChange={(e) => update("firstName", e.target.value)} placeholder="Aarav" /></label>
              <label>Last name<input required value={form.lastName} onChange={(e) => update("lastName", e.target.value)} placeholder="Sharma" /></label>
              <label>Email address<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" /></label>
              <label>Mobile number<input required type="tel" value={form.phone} onChange={(e) => update("phone", e.target.value)} placeholder="+91 98765 43210" /></label>
            </div></div>}
          <label>Email address<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" autoComplete="email" /></label>
          {screen === "register" && <div className="auth-section"><h2>Company information</h2><div className="auth-grid">
            <label className="auth-span">Company name<input required value={form.company} onChange={(e) => update("company", e.target.value)} placeholder="Acme Industries Pvt. Ltd." /></label>
            <label>Business type<select value={form.businessType} onChange={(e) => update("businessType", e.target.value)}><option>Private Limited</option><option>Partnership</option><option>Sole Proprietorship</option><option>Public Limited</option><option>LLP</option><option>Other</option></select></label>
            <label>Country<input required value={form.country} onChange={(e) => update("country", e.target.value)} /></label>
            <label>State<input required value={form.state} onChange={(e) => update("state", e.target.value)} placeholder="Maharashtra" /></label>
            <label>City<input required value={form.city} onChange={(e) => update("city", e.target.value)} placeholder="Mumbai" /></label>
            <label>GSTIN <span className="optional">Optional</span><input value={form.gstin} onChange={(e) => update("gstin", e.target.value)} placeholder="22AAAAA0000A1Z5" /></label>
            <label className="auth-span">Company website <span className="optional">Optional</span><input type="url" value={form.website} onChange={(e) => update("website", e.target.value)} placeholder="https://company.com" /></label>
          </div></div>}
          {(screen === "login" || screen === "register") && <label>Password
            <span className="password-wrap"><input required type={showPassword ? "text" : "password"} minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={screen === "login" ? "current-password" : "new-password"} placeholder="Enter your password" /><button type="button" onClick={() => setShowPassword(!showPassword)} aria-label="Toggle password visibility">{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></span>
          </label>}
          {screen === "register" && <div className="password-meter"><div className="meter-bars">{[1,2,3,4,5].map((n) => <i key={n} className={passwordScore >= n ? "filled" : ""} />)}</div><small>{passwordScore < 3 ? "Use a stronger password" : passwordScore < 5 ? "Almost there" : "Strong password"}</small></div>}
          {screen === "register" && <><label>Confirm password<span className="password-wrap"><input required type={showPassword ? "text" : "password"} value={form.confirmPassword} onChange={(e) => update("confirmPassword", e.target.value)} placeholder="Repeat your password" /><span className="match-icon">{form.confirmPassword && password === form.confirmPassword ? <Check size={16} /> : ""}</span></span></label><div className="requirements">{Object.entries({ length: "8+ characters", upper: "One uppercase letter", lower: "One lowercase letter", number: "One number", special: "One special character" }).map(([key, text]) => <span className={passwordChecks[key as keyof typeof passwordChecks] ? "valid" : ""} key={key}>{passwordChecks[key as keyof typeof passwordChecks] ? <Check size={12} /> : "○"} {text}</span>)}</div><label className="terms"><input type="checkbox" checked={form.terms} onChange={(e) => update("terms", e.target.checked)} /> <span>I agree to the <a href="/terms">Terms of Service</a> and <a href="/privacy">Privacy Policy</a>.</span></label></>}
          {error && <div className="auth-alert auth-error">{error}</div>}{notice && <div className="auth-alert auth-notice">{notice}</div>}
          <button className="auth-submit" disabled={loading}>{loading ? <span className="spinner" /> : <>{screen === "login" ? "Sign in" : "Create my account"} <ArrowRight size={17} /></>}</button>
        </form>
        {screen === "login" && <><div className="auth-options"><label className="remember"><input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} /> Remember me</label><button className="link-button" type="button" onClick={() => { setForgotOpen(true); setError(""); setNotice(""); }}>Forgot password?</button></div><div className="auth-divider"><span>OR CONTINUE WITH</span></div><div className="social-row social-single"><button type="button" className="google-button" disabled={googleLoading} onClick={startGoogleAuth}><span className="google-g" aria-hidden="true">G</span>Continue with Google<ArrowRight size={15} /></button></div></>}
        {screen === "register" && <div className="auth-social-signup"><div className="auth-divider"><span>OR SIGN UP WITH</span></div><button type="button" className="google-button" disabled={googleLoading} onClick={startGoogleAuth}><span className="google-g" aria-hidden="true">G</span>Sign up with Google<ArrowRight size={15} /></button><p>Google securely verifies your email and creates your workspace account.</p></div>}
          <div className="auth-footer">{screen === "login" ? <>Don't have an account? <button onClick={() => { setScreen("register"); setError(""); setNotice(""); }}>Create an account</button></> : <button onClick={() => { setScreen("login"); setError(""); setNotice(""); }}>Back to sign in</button>}</div>
        </main>
      </div>
      {forgotOpen && <div className="auth-modal-backdrop" role="presentation">
        <form className="auth-modal" onSubmit={submitForgot}>
          <button type="button" className="auth-modal-close" onClick={() => { setForgotOpen(false); setError(""); }}>×</button>
          <span className="auth-modal-icon">↗</span>
          <h2>{forgotStep === "request" ? "Forgot your password?" : "Create a new password"}</h2>
          <p>{forgotStep === "request" ? "Enter your email and we’ll send a secure, time-limited reset code." : "Enter the code from your email and choose a strong new password."}</p>
          <label>Email address<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
          {forgotStep === "reset" && <><label>Reset code<input required inputMode="numeric" pattern="[0-9]{6}" maxLength={6} value={otp} onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))} placeholder="6-digit code" /></label><label>New password<input required type="password" minLength={8} value={resetPassword} onChange={(e) => setResetPassword(e.target.value)} /></label><label>Confirm password<input required type="password" minLength={8} value={resetConfirm} onChange={(e) => setResetConfirm(e.target.value)} /></label></>}
          {error && <div className="auth-alert auth-error">{error}</div>}
          <button className="auth-submit" disabled={loading}>{loading ? <span className="spinner" /> : forgotStep === "request" ? "Send reset code" : "Update password"}</button>
          {forgotStep === "reset" && <button type="button" className="link-button auth-modal-resend" onClick={() => { setForgotStep("request"); setOtp(""); setError(""); }}>Send a new code</button>}
        </form>
      </div>}
      {googleTransition && <div className="google-transition" role="status" aria-live="polite">
        <div className="google-transition-card">
          <div className="google-transition-logo">G</div>
          <div className="google-transition-loader"><i /><i /><i /></div>
          <h2>Continue with Google</h2>
          <p>{email ? `Continuing as ${email}` : "Opening Google secure sign-in…"}</p>
        </div>
      </div>}
      <p className="auth-trust">Protected by enterprise-grade security <span>•</span> Your data stays yours</p>
    </div>
  );
}

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [token, setToken] = useState(
    localStorage.getItem("smarterp_token") || "",
  );
  const [user, setUser] = useState<User | null>(null);

  const [mode, setMode] = useState("register");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [industry, setIndustry] = useState("General");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");

  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [page, setPage] = useState("Dashboard");
  const [dash, setDash] = useState<any>(null);
  const [admin, setAdmin] = useState<any>(null);
  const [ai, setAi] = useState<any>(null);
  const [companies, setCompanies] = useState<any[]>([]);
  const [adminUsers, setAdminUsers] = useState<any[]>([]);
  const [adminPermissions, setAdminPermissions] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [platformUsers, setPlatformUsers] = useState<any[]>([]);
  const [platformAuditLogs, setPlatformAuditLogs] = useState<any[]>([]);
  const [adminForm, setAdminForm] = useState({
    company_id: "", full_name: "", email: "", password: "",
  });
  const [adminCreatedMessage, setAdminCreatedMessage] = useState("");
  const [settingsCompany, setSettingsCompany] = useState<any>(null);
  const [branches, setBranches] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [settingsTab, setSettingsTab] = useState("Company profile");
  const [settingsForm, setSettingsForm] = useState({
    name: "", industry: "", business_type: "", country: "India",
    state: "", city: "", gstin: "", website: "",
  });

  useEffect(() => {
    const timer = window.setTimeout(() => setShowSplash(false), 1900);
    return () => window.clearTimeout(timer);
  }, []);
  const [organizationForm, setOrganizationForm] = useState({
    name: "", code: "", address: "", city: "", state: "", branch_id: "",
  });

  const [products, setProducts] = useState<any[]>([]);
  const [product, setProduct] = useState({
    name: "",
    sku: "",
    category: "General",
    quantity: 0,
    reorder_level: 5,
    unit_price: 0,
  });
  const [showProduct, setShowProduct] = useState(false);

  // The same OTP input is used for email OTP, registration phone OTP,
  // and mobile-login OTP. The backend endpoints are kept separate.

  async function refresh(currentToken = token) {
    try {
      const me = await call("/api/auth/me", currentToken).catch(() => null);

      if (me) {
        setUser(me);

        if (me.role === "super_admin") {
          setAdmin(await call("/api/admin/overview", currentToken));
          setCompanies(await call("/api/admin/companies", currentToken));
          setPlatformUsers(await call("/api/admin/users", currentToken));
          setPlatformAuditLogs(await call("/api/admin/audit-logs", currentToken));
        } else {
          setDash(await call("/api/dashboard", currentToken));
          setProducts(await call("/api/products", currentToken));
          setAi(await call("/api/ai/overview", currentToken));
          const [companyData, branchData, departmentData, warehouseData] =
            await Promise.all([
              call("/api/organization/company", currentToken),
              call("/api/organization/branches", currentToken),
              call("/api/organization/departments", currentToken),
              call("/api/organization/warehouses", currentToken),
            ]);
          setSettingsCompany(companyData);
          setSettingsForm({
            name: companyData.name || "",
            industry: companyData.industry || "",
            business_type: companyData.business_type || "",
            country: companyData.country || "India",
            state: companyData.state || "",
            city: companyData.city || "",
            gstin: companyData.gstin || "",
            website: companyData.website || "",
          });
          setBranches(branchData);
          setDepartments(departmentData);
          setWarehouses(warehouseData);
          if (me.role === "owner" || me.role === "manager") {
            const [usersData, permissionsData, logsData] = await Promise.all([
              call("/api/company-admin/users", currentToken).catch(() => []),
              call("/api/admin/permissions", currentToken).catch(() => []),
              call("/api/company-admin/audit-logs", currentToken).catch(() => []),
            ]);
            setAdminUsers(usersData);
            setAdminPermissions(permissionsData);
            setAuditLogs(logsData);
          }
        }
      } else {
        setUser(null);
        localStorage.removeItem("smarterp_token");
        setToken("");
      }
    } catch (e: any) {
      setError(e.message || "Unable to load your account.");
    }
  }

  useEffect(() => {
    if (token) {
      refresh(token);
    }
    // refresh only when the authentication token changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function auth(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");

    try {
      if (mode === "register") {
        const data = await call("/api/auth/register", "", {
          method: "POST",
          body: JSON.stringify({
            company_name: company,
            industry,
            full_name: name,
            email,
            phone,
            password,
          }),
        });

        setMode("verify");
        setOtp("");
        setNotice(
          data.message ||
            "Verification OTP sent. Check your email or backend development logs.",
        );
      } else if (mode === "verify") {
        const data = await call("/api/auth/verify-email", "", {
          method: "POST",
          body: JSON.stringify({ email, otp }),
        });

        // Email verification is followed immediately by registration phone OTP.
        const phoneData = await call("/api/auth/phone/send-otp", "", {
          method: "POST",
          body: JSON.stringify({ phone_number: phone }),
        });

        setMode("mobileVerify");
        setOtp("");
        setNotice(
          `${data.message || "Email verified."} ${
            phoneData.message || "Mobile OTP sent successfully."
          }`,
        );
      } else if (mode === "mobileVerify") {
        const data = await call("/api/auth/phone/verify-otp", "", {
          method: "POST",
          body: JSON.stringify({ phone_number: phone, otp }),
        });

        setMode("login");
        setOtp("");
        setNotice(
          data.message ||
            "Email and mobile verified. Your account is ready to sign in.",
        );
      } else if (mode === "otp") {
        const data = await call("/api/auth/verify-login-otp", "", {
          method: "POST",
          body: JSON.stringify({ email, otp }),
        });

        localStorage.setItem("smarterp_token", data.access_token);
        setToken(data.access_token);
      } else if (mode === "mobile") {
        const data = await call("/api/auth/mobile-login/send-otp", "", {
          method: "POST",
          body: JSON.stringify({ phone_number: phone }),
        });

        setMode("mobileOtp");
        setOtp("");
        setNotice(data.message || "Mobile OTP sent successfully.");
      } else if (mode === "mobileOtp") {
        const data = await call("/api/auth/mobile-login/verify-otp", "", {
          method: "POST",
          body: JSON.stringify({ phone_number: phone, otp }),
        });

        localStorage.setItem("smarterp_token", data.access_token);
        setToken(data.access_token);
      } else {
        const data = await call("/api/auth/login", "", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });

        localStorage.setItem("smarterp_token", data.access_token);
        setToken(data.access_token);
      }
    } catch (e: any) {
      setError(e.message || "Authentication failed. Please try again.");
    }
  }

  async function requestOtp() {
    setError("");
    setNotice("");

    try {
      const data = await call("/api/auth/request-login-otp", "", {
        method: "POST",
        body: JSON.stringify({ email }),
      });

      setNotice(data.message || "Email OTP sent successfully.");
      setOtp("");
      setMode("otp");
    } catch (e: any) {
      setError(e.message || "Unable to send email OTP.");
    }
  }

  async function resendPhoneOtp() {
    setError("");
    setNotice("");

    try {
      const endpoint =
        mode === "mobileVerify"
          ? "/api/auth/phone/send-otp"
          : "/api/auth/mobile-login/send-otp";

      const data = await call(endpoint, "", {
        method: "POST",
        body: JSON.stringify({ phone_number: phone }),
      });

      setOtp("");
      setNotice(data.message || "A new mobile OTP has been sent.");
    } catch (e: any) {
      setError(e.message || "Unable to resend mobile OTP.");
    }
  }

  async function addProduct(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    try {
      await call("/api/products", token, {
        method: "POST",
        body: JSON.stringify(product),
      });

      setShowProduct(false);
      setProduct({
        name: "",
        sku: "",
        category: "General",
        quantity: 0,
        reorder_level: 5,
        unit_price: 0,
      });
      await refresh();
    } catch (e: any) {
      setError(e.message || "Unable to add product.");
    }

  }

  async function saveCompanySettings(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");
    try {
      const updated = await call("/api/organization/company", token, {
        method: "PUT",
        body: JSON.stringify({
          ...settingsForm,
          gstin: settingsForm.gstin || null,
          website: settingsForm.website || null,
        }),
      });
      setSettingsCompany(updated);
      setNotice("Company settings saved successfully.");
    } catch (e: any) {
      setError(e.message || "Unable to save company settings.");
    }
  }

  async function addOrganizationRecord(kind: "branches" | "departments" | "warehouses") {
    setError("");
    setNotice("");
    try {
      const payload = kind === "departments"
        ? { name: organizationForm.name, code: organizationForm.code }
        : kind === "branches"
          ? {
              name: organizationForm.name, code: organizationForm.code,
              address: organizationForm.address || null,
              city: organizationForm.city || null, state: organizationForm.state || null,
            }

          : {
              name: organizationForm.name, code: organizationForm.code,
              address: organizationForm.address || null,
              branch_id: organizationForm.branch_id ? Number(organizationForm.branch_id) : null,
            };
      await call(`/api/organization/${kind}`, token, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const [branchData, departmentData, warehouseData] = await Promise.all([
        call("/api/organization/branches", token),
        call("/api/organization/departments", token),
        call("/api/organization/warehouses", token),
      ]);
      setBranches(branchData);
      setDepartments(departmentData);
      setWarehouses(warehouseData);
      setOrganizationForm({ name: "", code: "", address: "", city: "", state: "", branch_id: "" });
      setNotice(`${kind.slice(0, -1)} added successfully.`);
    } catch (e: any) {
      setError(e.message || `Unable to add ${kind.slice(0, -1)}.`);
    }
  }

  async function createCompanyAdmin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setAdminCreatedMessage("");
    try {
      const result = await call("/api/admin/company-admins", token, {
        method: "POST",
        body: JSON.stringify({
          ...adminForm,
          company_id: Number(adminForm.company_id),
        }),
      });
      setAdminCreatedMessage(`Admin login created: ${result.email}`);
      setAdminForm({ company_id: "", full_name: "", email: "", password: "" });
      await refresh();
    } catch (e: any) {
      setError(e.message || "Unable to create company administrator.");
    }
  }

  function logout() {
    localStorage.removeItem("smarterp_token");
    setToken("");
    setUser(null);
    setDash(null);
    setAdmin(null);
    setAi(null);
    setCompanies([]);
    setProducts([]);
    setMode("login");
  }

  if (!user) {
    if (showSplash) return <StartupSplash />;
    return <AuthScreen onAuthenticated={(accessToken) => { localStorage.setItem("smarterp_token", accessToken); setToken(accessToken); }} />;
  }

  if (false) {
    return (
      <div className="auth">
        <form className="authbox" onSubmit={auth}>
          <div className="mark">S</div>
          <small>UNIVERSAL ENTERPRISE PLATFORM</small>

          <h1>
            {mode === "register"
              ? "Create your company workspace"
              : mode === "verify"
                ? "Verify your email"
                : mode === "otp"
                  ? "Email OTP sign in"
                  : mode === "mobile"
                    ? "Login with mobile number"
                    : mode === "mobileOtp"
                      ? "Verify mobile OTP"
                      : "Welcome to SmartERP"}
          </h1>

          <p>One secure workspace to manage your business.</p>

          {mode === "register" && (
            <>
              <label>
                Company name
                <input
                  required
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                />
              </label>

              <label>
                Industry
                <select
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                >
                  {[
                    "General",
                    "IT & Software",
                    "Manufacturing",
                    "Retail",
                    "Wholesale",
                    "Healthcare",
                    "Education",
                    "Construction",
                    "Hospitality",
                    "Logistics",
                    "E-commerce",
                    "Services",
                  ].map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Your name
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </label>

              <label>
                Phone (include country code for SMS)
                <input
                  type="tel"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.trim())}
                  placeholder="+919876543210"
                />
              </label>
            </>
          )}

          {!["mobile", "mobileOtp", "mobileVerify"].includes(mode) && (
            <label>
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
          )}

          {["mobile", "mobileOtp", "mobileVerify"].includes(mode) && (
            <label>
              Mobile number
              <input
                type="tel"
                required
                disabled={mode === "mobileOtp" || mode === "mobileVerify"}
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+919876543210"
                pattern="\+[1-9]\d{7,14}"
                title="Enter your number with country code, for example +919876543210"
              />
            </label>
          )}

          {mode === "register" || mode === "login" ? (
            <label>
              Password
              <input
                type="password"
                required
                minLength={mode === "register" ? 10 : 1}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
          ) : null}

          {["verify", "otp", "mobileOtp", "mobileVerify"].includes(mode) && (
            <label>
              {mode === "mobileOtp" || mode === "mobileVerify"
                ? "6-digit mobile OTP"
                : "6-digit email OTP"}
              <input
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                minLength={6}
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                placeholder="Enter OTP"
              />
            </label>
          )}

          {error && <div className="error">{error}</div>}
          {notice && <div className="notice">{notice}</div>}

          <button className="primary" type="submit">
            {mode === "register"
              ? "Create account"
              : mode === "verify"
                ? "Verify email"
                : mode === "otp" || mode === "mobileOtp"
                  ? "Verify OTP"
                  : mode === "mobile"
                    ? "Send mobile OTP"
                    : "Sign in"}
          </button>

          {mode === "login" && (
            <>
              <button type="button" className="text" onClick={requestOtp}>
                Sign in with email OTP
              </button>
              <button
                type="button"
                className="text"
                onClick={() => {
                  setError("");
                  setNotice("");
                  setOtp("");
                  setPhone("");
                  setMode("mobile");
                }}
              >
                Sign in with mobile number
              </button>
            </>
          )}

          {(mode === "mobileOtp" || mode === "mobileVerify") && (
            <button type="button" className="text" onClick={resendPhoneOtp}>
              Resend mobile OTP
            </button>
          )}

          {mode === "verify" && (
            <button
              type="button"
              className="text"
              onClick={async () => {
                setError("");
                setNotice("");
                try {
                  const data = await call("/api/auth/resend-verification", "", {
                    method: "POST",
                    body: JSON.stringify({ email }),
                  });
                  setNotice(data.message || "Verification OTP resent.");
                } catch (e: any) {
                  setError(e.message || "Unable to resend verification OTP.");
                }
              }}
            >
              Resend email verification OTP
            </button>
          )}

          <div className="switch">
            {mode !== "register" ? (
              <button
                type="button"
                onClick={() => {
                  setError("");
                  setNotice("");
                  setOtp("");
                  setMode("login");
                }}
              >
                Back to login
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setError("");
                  setNotice("");
                  setMode("login");
                }}
              >
                Already registered? Sign in
              </button>
            )}

            {mode === "login" && (
              <button
                type="button"
                onClick={() => {
                  setError("");
                  setNotice("");
                  setMode("register");
                }}
              >
                Create company
              </button>
            )}
          </div>
        </form>
      </div>
    );
  }

  const nav =
    user.role === "super_admin"
      ? ([
          ["Dashboard", LayoutDashboard],
          ["Companies", Building2],
          ["Platform Admin", ServerCog],
          ["Settings", Settings],
        ] as const)
      : ([
          ["Dashboard", LayoutDashboard],
          ["Inventory", Boxes],
          ["Customers", Users],
          ["AI Analytics", BrainCircuit],
          ...(user.role === "owner" || user.role === "manager"
            ? ([["Admin Panel", UserCog]] as const)
            : []),
          ["Settings", Settings],
        ] as const);
  const isAdminPanel = page === "Admin Panel";

  return (
    <div className="layout">
      <aside>
        <div className="mark sm" aria-label="SmartERP">
          S
        </div>

        <div className="account">
          <ShieldCheck size={17} />
          <div>
            <b>
              {user.role === "super_admin"
                ? "Platform Admin"
                : dash?.company || "Company Workspace"}
            </b>
            <small>{user.role}</small>
          </div>
        </div>

        <small className="navlabel">WORKSPACE</small>
        {nav.map(([label, Icon]) => (
          <button
            key={label}
            className={page === label ? "active" : ""}
            onClick={() => setPage(label)}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}

        <div className="bottom">
          <div className="profile">
            <div className="avatar">{user.full_name?.[0] || "U"}</div>
            <div>
              <b>{user.full_name}</b>
              <small>{user.email}</small>
            </div>
          </div>
          <button onClick={logout}>
            <LogOut size={17} /> Sign out
          </button>
        </div>
      </aside>

      <main>
        <header>
          <span>SmartERP / {page}</span>
          <Bell size={19} />
        </header>

        <section className="content">
          <div className="title">
            <div>
              <small>WORKSPACE OVERVIEW</small>
              <h1>{page}</h1>
              <p>Manage operations and make data-informed decisions.</p>
            </div>

            {page === "Inventory" && (
              <button
                className="primary smallbtn"
                onClick={() => setShowProduct(true)}
              >
                <Plus size={16} /> Add product
              </button>
            )}
          </div>

          {error && <div className="error">{error}</div>}

          {user.role === "super_admin" && page === "Dashboard" && admin && (
            <div className="stats">
              {[
                ["Companies", admin.companies],
                ["Users", admin.users],
                ["Verified users", admin.verified_users],
                ["Sales records", admin.sales_records],
              ].map(([label, value]) => (
                <div className="stat" key={String(label)}>
                  <small>{label}</small>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          )}

          {user.role === "super_admin" && page === "Companies" && (
            <div className="panel">
              <h3>Registered companies</h3>
              {companies.map((companyItem) => (
                <div className="row" key={companyItem.id}>
                  <div>
                    <b>{companyItem.name}</b>
                    <small>
                      {companyItem.industry} •{" "}
                      {companyItem.is_active ? "Active" : "Suspended"}
                    </small>
                  </div>
                  <button
                    className="text"
                    onClick={async () => {
                      try {
                        const result = await call(
                          `/api/admin/companies/${companyItem.id}/status?active=${!companyItem.is_active}`,
                          token,
                          { method: "PATCH" },
                        );
                        setNotice(result.notification?.message || "Workspace status updated.");
                        await refresh();
                      } catch (e: any) {
                        setError(e.message || "Unable to update company.");
                      }
                    }}
                  >
                    {companyItem.deleted ? "Deleted" : companyItem.is_active ? "Suspend" : "Activate"}
                  </button>
                  {companyItem.deleted ? (
                    <button className="text" onClick={async () => {
                      try {
                        await call(`/api/admin/companies/${companyItem.id}/restore`, token, { method: "POST" });
                        setNotice("Workspace restored.");
                        await refresh();
                      } catch (e: any) {
                        setError(e.message || "Unable to restore workspace.");
                      }
                    }}>Restore</button>
                  ) : (
                    <button className="text danger-text" onClick={async () => {
                      if (!window.confirm("Soft-delete this workspace? Its data will be retained but access will be disabled.")) return;
                      try {
                        await call(`/api/admin/companies/${companyItem.id}`, token, { method: "DELETE" });
                        setNotice("Workspace soft-deleted. Data was retained.");
                        await refresh();
                      } catch (e: any) {
                        setError(e.message || "Unable to delete workspace.");
                      }
                    }}>Delete</button>
                  )}
                </div>
              ))}
            </div>
          )}

          {user.role === "super_admin" && page === "Platform Admin" && (
            <div className="admin-console">
              <div className="stats">
                {[
                  ["Companies", admin?.companies || 0],
                  ["Users", admin?.users || 0],
                  ["Verified users", admin?.verified_users || 0],
                  ["Sales records", admin?.sales_records || 0],
                ].map(([label, value]) => <div className="stat" key={String(label)}><small>{label}</small><strong>{value}</strong></div>)}
              </div>
              <div className="admin-grid">
                <form className="panel" onSubmit={createCompanyAdmin}>
                  <div className="panel-heading"><div><UserCog size={18} /><h3>Create company admin</h3></div><span>Super Admin only</span></div>
                  <p>Create an owner-level administrator who can sign in to a selected company workspace.</p>
                  <label className="admin-field">Company<select required value={adminForm.company_id} onChange={(e) => setAdminForm({ ...adminForm, company_id: e.target.value })}><option value="">Select company</option>{companies.filter((item) => item.is_active).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
                  <label className="admin-field">Full name<input required value={adminForm.full_name} onChange={(e) => setAdminForm({ ...adminForm, full_name: e.target.value })} /></label>
                  <label className="admin-field">Login email<input required type="email" value={adminForm.email} onChange={(e) => setAdminForm({ ...adminForm, email: e.target.value })} /></label>
                  <label className="admin-field">Temporary password<input required minLength={12} type="password" value={adminForm.password} onChange={(e) => setAdminForm({ ...adminForm, password: e.target.value })} placeholder="12+ chars, upper/lower/number/symbol" /></label>
                  {adminCreatedMessage && <div className="notice">{adminCreatedMessage}</div>}
                  <button className="primary" type="submit">Create admin login</button>
                </form>
                <div className="panel">
                  <div className="panel-heading"><div><UsersRound size={18} /><h3>Platform users</h3></div><span>{platformUsers.length} users</span></div>
                  {platformUsers.slice(0, 10).map((item) => <div className="admin-row" key={item.id}><div><b>{item.full_name}</b><small>{item.email} · Company #{item.company_id ?? "platform"}</small></div><span className="status">{item.role}</span></div>)}
                </div>
                <div className="panel">
                  <div className="panel-heading"><div><FileClock size={18} /><h3>Platform activity</h3></div></div>
                  {platformAuditLogs.length ? platformAuditLogs.slice(0, 8).map((item) => <div className="admin-row" key={item.id}><div><b>{item.action}</b><small>{item.resource} · {new Date(item.created_at).toLocaleString("en-IN")}</small></div></div>) : <p>No audit activity recorded yet.</p>}
                </div>
                <div className="panel danger-panel">
                  <div className="panel-heading"><div><ShieldCheck size={18} /><h3>Delete workspace</h3></div></div>
                  <p>Soft-deleting this workspace disables access but retains all company records for restoration by Super Admin.</p>
                  <button className="danger-button" onClick={async () => {
                    if (!window.confirm("Soft-delete this workspace? Data will be retained and access will be disabled.")) return;
                    try {
                      await call("/api/company-admin/workspace", token, { method: "DELETE" });
                      logout();
                    } catch (e: any) {
                      setError(e.message || "Unable to delete workspace.");
                    }
                  }}>Delete my workspace</button>
                </div>
              </div>
            </div>
          )}

          {user.role !== "super_admin" && page === "Dashboard" && dash && (
            <>
              <div className="stats">
                {[
                  ["Revenue", `₹${dash.kpis.total_sales.toLocaleString("en-IN")}`],
                  ["Net profit", `₹${dash.kpis.net_operating_result.toLocaleString("en-IN")}`],
                  ["Outstanding", `₹${dash.kpis.outstanding_payments.toLocaleString("en-IN")}`],
                  ["Customers", dash.kpis.customers],
                  ["Suppliers", dash.kpis.suppliers],
                  ["Inventory value", `₹${dash.kpis.inventory_value.toLocaleString("en-IN")}`],
                  [
                    "Products",
                    `${dash.kpis.products} · ${dash.kpis.stock_units} units`,
                  ],
                ].map(([label, value]) => (
                  <div className="stat" key={String(label)}>
                    <small>{label}</small>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>

              <div className="dashboard-grid">
                <div className="panel chart-panel">
                  <div className="panel-heading">
                    <div><BarChart3 size={18} /><h3>Revenue overview</h3></div>
                    <span>Last 6 months</span>
                  </div>
                  <div className="bar-chart">
                    {dash.monthly_revenue.map((item: any) => {
                      const max = Math.max(...dash.monthly_revenue.map((entry: any) => entry.revenue), 1);
                      return <div className="bar-item" key={item.month}>
                        <div className="bar-track"><div className="bar-fill" style={{ height: `${Math.max((item.revenue / max) * 100, item.revenue ? 8 : 2)}%` }} /></div>
                        <small>{item.month.slice(5)}</small>
                      </div>;
                    })}
                  </div>
                </div>
                <div className="panel">
                  <div className="panel-heading"><div><Activity size={18} /><h3>Business activity</h3></div></div>
                  {dash.recent_transactions.length ? dash.recent_transactions.slice(0, 5).map((item: any, index: number) => (
                    <div className="activity-row" key={`${item.type}-${item.date}-${index}`}>
                      <span className={`activity-icon ${item.type}`}><Wallet size={15} /></span>
                      <div><b>{item.description}</b><small>{new Date(item.date).toLocaleDateString("en-IN")}</small></div>
                      <strong className={item.type === "expense" ? "negative" : "positive"}>{item.type === "expense" ? "-" : "+"}₹{item.amount.toLocaleString("en-IN")}</strong>
                    </div>
                  )) : <p>No transactions recorded yet.</p>}
                </div>
              </div>
              <div className="dashboard-grid dashboard-grid-three">
                <div className="panel">
                  <div className="panel-heading"><div><AlertTriangle size={18} /><h3>Low-stock alerts</h3></div><span className="pill warning">{dash.low_stock.length}</span></div>
                  {dash.low_stock.length ? dash.low_stock.slice(0, 4).map((item: any) => <div className="compact-row" key={item.id}><span>{item.name}<small>{item.sku}</small></span><b>{item.quantity} / {item.reorder_level}</b></div>) : <p>All products are above reorder level.</p>}
                </div>
                <div className="panel">
                  <div className="panel-heading"><div><ClipboardCheck size={18} /><h3>Pending approvals</h3></div></div>
                  <div className="approval-card"><span>Leave requests</span><b>{dash.pending_approvals.leave_requests}</b></div>
                  <div className="approval-card"><span>Purchase orders</span><b>{dash.pending_approvals.purchase_orders}</b></div>
                </div>
                <div className="panel">
                  <div className="panel-heading"><div><ShoppingCart size={18} /><h3>Expense tracking</h3></div></div>
                  <div className="expense-total">₹{dash.kpis.total_expenses.toLocaleString("en-IN")}</div>
                  <p>Total expenses recorded for this company workspace.</p>
                </div>
              </div>
            </>
          )}

          {user.role !== "super_admin" && page === "Inventory" && (
            <div className="panel">
              <h3>Inventory</h3>
              <div className="table">
                <div className="thead">
                  <span>Product</span>
                  <span>SKU</span>
                  <span>Quantity</span>
                  <span>Unit price</span>
                </div>
                {products.map((item) => (
                  <div className="tr" key={item.id || item.sku || item.name}>
                    <span>{item.name}</span>
                    <span>{item.sku}</span>
                    <span>{item.quantity}</span>
                    <span>₹{item.unit_price}</span>
                  </div>
                ))}
              </div>
              {!products.length && <p>No products yet. Add your first item.</p>}
            </div>
          )}

          {user.role !== "super_admin" && page === "Customers" && (
            <div className="panel">
              <h3>Customers</h3>
              <p>
                Customer management API is ready. Customer form is the next UI
                increment.
              </p>
            </div>
          )}

          {user.role !== "super_admin" && page === "AI Analytics" && (
            <div className="ai-grid">
              <div className="panel">
                <BrainCircuit />
                <h3>AI Data Readiness</h3>
                <p>{ai?.message}</p>
                <p>Sales records: {ai?.data_quality?.sales_records || 0}</p>
                <button
                  className="text"
                  onClick={async () => {
                    try {
                      setAi({
                        ...ai,
                        forecast: await call(
                          "/api/ai/sales-forecast?periods=3",
                          token,
                        ),
                        inventory: await call(
                          "/api/ai/inventory-recommendations",
                          token,
                        ),
                        segments: await call(
                          "/api/ai/customer-segments",
                          token,
                        ),
                        anomalies: await call("/api/ai/anomaly-review", token),
                      });
                    } catch (e: any) {
                      setError(e.message || "Unable to run AI analysis.");
                    }
                  }}
                >
                  Run AI analysis
                </button>
              </div>

              {ai?.forecast && (
                <div className="panel">
                  <h3>Sales forecast</h3>
                  <pre>{JSON.stringify(ai.forecast, null, 2)}</pre>
                  <h3>Inventory recommendations</h3>
                  <pre>{JSON.stringify(ai.inventory, null, 2)}</pre>
                  <h3>Customer segments</h3>
                  <pre>{JSON.stringify(ai.segments, null, 2)}</pre>
                  <h3>Anomaly review</h3>
                  <pre>{JSON.stringify(ai.anomalies, null, 2)}</pre>
                </div>
              )}

              {isAdminPanel && user.role !== "super_admin" && (
                <div className="admin-console">
                  <div className="admin-grid">
                    <div className="panel">
                      <div className="panel-heading"><div><UsersRound size={18} /><h3>Team members</h3></div><span>{adminUsers.length} users</span></div>
                      {adminUsers.map((item) => <div className="admin-row" key={item.id}><div><b>{item.full_name}</b><small>{item.email}</small></div><span className="status">{item.role}</span></div>)}
                      {!adminUsers.length && <p>No team members found or you do not have RBAC permission.</p>}
                    </div>
                    <div className="panel">
                      <div className="panel-heading"><div><ShieldCheck size={18} /><h3>Role permissions</h3></div><span>{adminPermissions.length} rules</span></div>
                      {adminPermissions.slice(0, 12).map((item) => <div className="admin-row" key={item.id}><div><b>{item.role}</b><small>{item.permission}</small></div><span className={item.allowed ? "status" : "status inactive"}>{item.allowed ? "Allowed" : "Blocked"}</span></div>)}
                      {!adminPermissions.length && <p>No permission rules found.</p>}
                    </div>
                  </div>
                  <div className="panel">
                    <div className="panel-heading"><div><FileClock size={18} /><h3>Company audit log</h3></div><span>{auditLogs.length} entries</span></div>
                    {auditLogs.length ? auditLogs.slice(0, 10).map((item) => <div className="admin-row" key={item.id}><div><b>{item.action}</b><small>{item.resource} · {new Date(item.created_at).toLocaleString("en-IN")}</small></div></div>) : <p>No audit activity recorded yet.</p>}
                  </div>
                </div>
              )}
            </div>
          )}

          {page === "Settings" && (
            <div className="settings-layout">
              <div className="settings-tabs">
                {["Company profile", "Branches", "Departments", "Warehouses", "Account"].map((tab) => (
                  <button key={tab} className={settingsTab === tab ? "active" : ""} onClick={() => setSettingsTab(tab)}>
                    {tab}
                  </button>
                ))}
              </div>
              {settingsTab === "Company profile" && (
                <form className="panel settings-panel" onSubmit={saveCompanySettings}>
                  <div className="panel-heading"><div><Building2 size={18} /><h3>Company profile</h3></div><span>Company ID: {user.company_id}</span></div>
                  <p>Update the business identity used across invoices, reports, and the workspace.</p>
                  <div className="settings-form-grid">
                    {([
                      ["name", "Company name"], ["industry", "Industry"], ["business_type", "Business type"],
                      ["country", "Country"], ["state", "State"], ["city", "City"], ["gstin", "GSTIN"], ["website", "Website"],
                    ] as const).map(([key, label]) => (
                      <label key={key}>{label}<input value={settingsForm[key]} onChange={(e) => setSettingsForm({ ...settingsForm, [key]: e.target.value })} placeholder={label} /></label>
                    ))}
                  </div>
                  <div className="settings-actions"><button className="primary" type="submit">Save company settings</button></div>
                </form>
              )}
              {(["Branches", "Departments", "Warehouses"] as const).includes(settingsTab as any) && (
                <div className="settings-management">
                  <form className="panel settings-panel" onSubmit={(e) => { e.preventDefault(); void addOrganizationRecord(settingsTab.toLowerCase() as "branches" | "departments" | "warehouses"); }}>
                    <div className="panel-heading"><div><Plus size={18} /><h3>Add {settingsTab.slice(0, -1).toLowerCase()}</h3></div></div>
                    <div className="settings-form-grid">
                      <label>Name<input required value={organizationForm.name} onChange={(e) => setOrganizationForm({ ...organizationForm, name: e.target.value })} /></label>
                      <label>Code<input required value={organizationForm.code} onChange={(e) => setOrganizationForm({ ...organizationForm, code: e.target.value.toUpperCase() })} /></label>
                      {settingsTab === "Warehouses" && <label>Branch<select value={organizationForm.branch_id} onChange={(e) => setOrganizationForm({ ...organizationForm, branch_id: e.target.value })}><option value="">No branch</option>{branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label>}
                      {settingsTab !== "Departments" && <><label>Address<input value={organizationForm.address} onChange={(e) => setOrganizationForm({ ...organizationForm, address: e.target.value })} /></label><label>City<input value={organizationForm.city} onChange={(e) => setOrganizationForm({ ...organizationForm, city: e.target.value })} /></label><label>State<input value={organizationForm.state} onChange={(e) => setOrganizationForm({ ...organizationForm, state: e.target.value })} /></label></>}
                    </div>
                    <div className="settings-actions"><button className="primary" type="submit">Add {settingsTab.slice(0, -1).toLowerCase()}</button></div>
                  </form>
                  <div className="panel">
                    <div className="panel-heading"><div><Settings size={18} /><h3>{settingsTab}</h3></div><span>{settingsTab === "Branches" ? branches.length : settingsTab === "Departments" ? departments.length : warehouses.length} records</span></div>
                    <div className="settings-records">
                      {(settingsTab === "Branches" ? branches : settingsTab === "Departments" ? departments : warehouses).map((item) => <div className="settings-record" key={item.id}><div><b>{item.name}</b><small>{item.code}{item.city ? ` · ${item.city}` : ""}{item.branch_id ? ` · Branch #${item.branch_id}` : ""}</small></div><span className={item.is_active === false ? "status inactive" : "status"}>{item.is_active === false ? "Inactive" : "Active"}</span></div>)}
                      {!(settingsTab === "Branches" ? branches : settingsTab === "Departments" ? departments : warehouses).length && <p>No {settingsTab.toLowerCase()} configured yet.</p>}
                    </div>
                  </div>
                </div>
              )}
              {settingsTab === "Account" && (
                <div className="panel settings-panel">
                  <div className="panel-heading"><div><ShieldCheck size={18} /><h3>Account and security</h3></div></div>
                  <div className="account-settings-card"><div className="avatar">{user.full_name?.[0] || "U"}</div><div><b>{user.full_name}</b><small>{user.email}</small></div><span className="status">{user.role}</span></div>
                  <p>Your session is protected with JWT authentication and company-scoped access controls. Sign out from the sidebar when using a shared device.</p>
                  <button className="primary" onClick={logout}>Sign out</button>
                </div>
              )}
            </div>
          )}
        </section>
      </main>

      {showProduct && (
        <div className="overlay">
          <form className="modal" onSubmit={addProduct}>
            <button
              type="button"
              className="close"
              onClick={() => setShowProduct(false)}
            >
              ×
            </button>
            <h3>Add inventory item</h3>

            {(["name", "sku", "category"] as const).map((key) => (
              <label key={key}>
                {key}
                <input
                  required={key !== "category"}
                  value={product[key]}
                  onChange={(e) =>
                    setProduct({ ...product, [key]: e.target.value })
                  }
                />
              </label>
            ))}

            <label>
              Quantity
              <input
                type="number"
                min="0"
                value={product.quantity}
                onChange={(e) =>
                  setProduct({ ...product, quantity: Number(e.target.value) })
                }
              />
            </label>

            <label>
              Reorder level
              <input
                type="number"
                min="0"
                value={product.reorder_level}
                onChange={(e) =>
                  setProduct({
                    ...product,
                    reorder_level: Number(e.target.value),
                  })
                }
              />
            </label>

            <label>
              Unit price
              <input
                type="number"
                min="0"
                step="0.01"
                value={product.unit_price}
                onChange={(e) =>
                  setProduct({ ...product, unit_price: Number(e.target.value) })
                }
              />
            </label>

            <button className="primary" type="submit">
              Save product
            </button>
          </form>
        </div>
      )}
    </div>
  );
}