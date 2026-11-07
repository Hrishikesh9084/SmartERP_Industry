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
} from "lucide-react";


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

export default function App() {
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
        } else {
          setDash(await call("/api/dashboard", currentToken));
          setProducts(await call("/api/products", currentToken));
          setAi(await call("/api/ai/overview", currentToken));
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
          }${phoneData.otp ? ` Development OTP: ${phoneData.otp}` : ""}`,
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
        setNotice(
          `${data.message || "Mobile OTP sent successfully."}${
            data.otp ? ` Development OTP: ${data.otp}` : ""
          }`,
        );
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
      setNotice(
        `${data.message || "A new mobile OTP has been sent."}${
          data.otp ? ` Development OTP: ${data.otp}` : ""
        }`,
      );
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
          ["Settings", Settings],
        ] as const)
      : ([
          ["Dashboard", LayoutDashboard],
          ["Inventory", Boxes],
          ["Customers", Users],
          ["AI Analytics", BrainCircuit],
          ["Settings", Settings],
        ] as const);

  return (
    <div className="layout">
      <aside>
        <img src="3." alt="SmartERP" />

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
                        await call(
                          `/api/admin/companies/${companyItem.id}/status?active=${!companyItem.is_active}`,
                          token,
                          { method: "PATCH" },
                        );
                        await refresh();
                      } catch (e: any) {
                        setError(e.message || "Unable to update company.");
                      }
                    }}
                  >
                    {companyItem.is_active ? "Suspend" : "Activate"}
                  </button>
                </div>
              ))}
            </div>
          )}

          {user.role !== "super_admin" && page === "Dashboard" && dash && (
            <>
              <div className="stats">
                {[
                  ["Products", dash.kpis.products],
                  ["Customers", dash.kpis.customers],
                  ["Stock units", dash.kpis.stock_units],
                  [
                    "Total sales",
                    `₹${dash.kpis.total_sales.toLocaleString("en-IN")}`,
                  ],
                  [
                    "Expenses",
                    `₹${dash.kpis.total_expenses.toLocaleString("en-IN")}`,
                  ],
                  [
                    "Net result",
                    `₹${dash.kpis.net_operating_result.toLocaleString("en-IN")}`,
                  ],
                ].map(([label, value]) => (
                  <div className="stat" key={String(label)}>
                    <small>{label}</small>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>

              <div className="panel">
                <h3>Business snapshot</h3>
                <p>Company-specific metrics from your workspace database.</p>
                <p>
                  AI data readiness: {ai?.data_quality?.sales_records || 0}{" "}
                  sales records, {ai?.data_quality?.products || 0} products and{" "}
                  {ai?.data_quality?.customers || 0} customers.
                </p>
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
            </div>
          )}

          {page === "Settings" && (
            <div className="panel">
              <h3>Account</h3>
              <p>
                {user.full_name} • {user.email} • {user.role}
              </p>
              <p>Company ID: {user.company_id ?? "Platform-wide"}</p>
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