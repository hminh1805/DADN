import { useState } from "react";
import {
  Thermometer, Droplets, Utensils, Droplet,
  Fan, Lightbulb, Volume2, PawPrint,
  Activity, Camera, AlertTriangle,
  CheckCircle, Info, X, Dog, Cat,
  Bell, Settings, Wifi, WifiOff,
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import { usePetDashboard } from "./hooks/usePetDashboard";

/* ─── Design tokens ─────────────────────────────────────── */
const T = {
  primary: "#2D7D6F", primary2: "#3A9B89",
  secondary: "#F4A03A", accent: "#E8604C",
  water: "#4AB8E8", soft: "#EAF6F4",
  bg: "#F3F8F7", card: "#FFFFFF",
  text: "#1A2E2A", muted: "#6B8E88",
  border: "rgba(45,125,111,0.14)",
};

const STATUS = {
  ok:      { bg: "#EAF6F0", text: "#1A7A4A", label: "Tốt" },
  warning: { bg: "#FFF3E0", text: "#B45A00", label: "Chú ý" },
  danger:  { bg: "#FEE9E8", text: "#C0392B", label: "Nguy hiểm" },
};

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
function statusOf(v, d, w) { return v < d ? "danger" : v < w ? "warning" : "ok"; }
function tempStatus(t)     { return t > 32 ? "danger" : (t > 29 || t < 22) ? "warning" : "ok"; }
const nowStr = () => new Date().toLocaleTimeString("vi-VN", { hour:"2-digit", minute:"2-digit" });

/* ─── Atom components ───────────────────────────────────── */
function Badge({ status, children }) {
  const c = STATUS[status] || STATUS.ok;
  return (
    <span style={{ padding:"2px 10px", borderRadius:20, fontSize:11, fontWeight:700,
      background:c.bg, color:c.text, display:"inline-block" }}>
      {children ?? c.label}
    </span>
  );
}

function Toggle({ on, onChange, disabled }) {
  return (
    <button onClick={() => !disabled && onChange(!on)} style={{
      width:42, height:24, borderRadius:12, border:"none",
      background: on ? T.primary : "#D1D5DB", position:"relative",
      cursor: disabled ? "not-allowed" : "pointer",
      transition:"background .25s", flexShrink:0, opacity: disabled ? 0.5 : 1,
    }}>
      <span style={{ position:"absolute", width:18, height:18, borderRadius:"50%",
        background:"#fff", top:3, left: on ? 21 : 3, transition:"left .25s",
        boxShadow:"0 1px 4px rgba(0,0,0,.25)" }} />
    </button>
  );
}

function Bar({ value, color }) {
  return (
    <div style={{ background:T.soft, borderRadius:20, height:8, overflow:"hidden" }}>
      <div style={{ width:`${clamp(value,0,100)}%`, height:"100%", borderRadius:20,
        background:color, transition:"width .5s ease" }} />
    </div>
  );
}

function Card({ children, style }) {
  return (
    <div style={{ background:T.card, borderRadius:16, border:`0.5px solid ${T.border}`,
      padding:"18px 20px", ...style }}>
      {children}
    </div>
  );
}

function CardTitle({ children, icon: Icon }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:8, fontSize:15,
      fontWeight:700, color:T.text, marginBottom:16 }}>
      {Icon && <Icon size={16} color={T.primary} />}{children}
    </div>
  );
}

function SensorCard({ title, value, unit, icon: Icon, status }) {
  const c = STATUS[status] || STATUS.ok;
  return (
    <Card style={{ textAlign:"center", padding:"18px 12px" }}>
      <div style={{ width:44, height:44, borderRadius:"50%", background:T.soft,
        margin:"0 auto 10px", display:"flex", alignItems:"center", justifyContent:"center" }}>
        <Icon size={20} color={T.primary} />
      </div>
      <div style={{ fontSize:26, fontWeight:700, color:c.text, lineHeight:1 }}>
        {value}<span style={{ fontSize:14, fontWeight:500 }}>{unit}</span>
      </div>
      <div style={{ fontSize:12, color:T.muted, margin:"5px 0 8px", fontWeight:600 }}>{title}</div>
      <Badge status={status} />
    </Card>
  );
}

function AlertRow({ type, title, message, onClose }) {
  const cfg = {
    warning: { bg:"#FFF8EF", border:"#F4A03A", Icon:AlertTriangle, color:"#B45A00" },
    error:   { bg:"#FEF0EF", border:"#E8604C", Icon:AlertTriangle, color:"#C0392B" },
    info:    { bg:"#EFF8FF", border:"#4AB8E8", Icon:Info,          color:"#0369A1" },
    success: { bg:"#EAF6F0", border:"#2D7D6F", Icon:CheckCircle,   color:"#1A7A4A" },
  }[type] ?? {};
  return (
    <div style={{ display:"flex", alignItems:"flex-start", gap:10,
      background:cfg.bg, border:`1px solid ${cfg.border}`,
      borderRadius:12, padding:"10px 14px" }}>
      <cfg.Icon size={16} color={cfg.color} style={{ marginTop:1, flexShrink:0 }} />
      <div style={{ flex:1 }}>
        <div style={{ fontSize:13, fontWeight:700, color:cfg.color }}>{title}</div>
        <div style={{ fontSize:12, color:T.text, marginTop:2 }}>{message}</div>
      </div>
      {onClose && (
        <button onClick={onClose} style={{ border:"none", background:"none", cursor:"pointer" }}>
          <X size={14} color={T.muted} />
        </button>
      )}
    </div>
  );
}

function ActionBtn({ icon: Icon, label, onClick, disabled, color = T.primary }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      display:"flex", flexDirection:"column", alignItems:"center", gap:6,
      padding:"12px 8px", borderRadius:14,
      border:`1.5px solid ${disabled ? T.border : color+"44"}`,
      background: disabled ? "#F9FAFB" : T.soft,
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.55 : 1, flex:1, minWidth:70,
      transition:"all .2s", fontFamily:"inherit",
    }}>
      <Icon size={20} color={disabled ? T.muted : color} />
      <span style={{ fontSize:11, fontWeight:700, color: disabled ? T.muted : color }}>{label}</span>
    </button>
  );
}

function TabBar({ tabs, active, onChange }) {
  return (
    <div style={{ display:"flex", gap:4, background:"#F1F5F3",
      borderRadius:12, padding:4, marginBottom:20 }}>
      {tabs.map(t => (
        <button key={t.id} onClick={() => onChange(t.id)} style={{
          flex:1, padding:"8px 12px", borderRadius:10, border:"none",
          cursor:"pointer",
          background: active === t.id ? T.card : "transparent",
          color: active === t.id ? T.primary : T.muted,
          fontWeight: active === t.id ? 700 : 500,
          fontSize:13, fontFamily:"inherit",
          boxShadow: active === t.id ? "0 1px 4px rgba(0,0,0,.08)" : "none",
          transition:"all .2s", display:"flex", alignItems:"center",
          justifyContent:"center", gap:6,
        }}>
          {t.icon && <t.icon size={14} />}{t.label}
        </button>
      ))}
    </div>
  );
}

/* ─── Main Dashboard ────────────────────────────────────── */
export default function PawHomeDashboard() {
  const dash = usePetDashboard();
  const [tab,      setTab]      = useState("overview");
  const [alerts,   setAlerts]   = useState([]);
  const [dismissed, setDismiss] = useState(new Set());

  // Tạo alerts từ sensor state
  const activeAlerts = [
    dash.dogFood  < 20 && { id:"df", type:"warning", title:"Thức ăn chó sắp hết",  message:`Còn ${Math.round(dash.dogFood)}% — vui lòng nạp thêm.` },
    dash.catFood  < 20 && { id:"cf", type:"warning", title:"Thức ăn mèo sắp hết",  message:`Còn ${Math.round(dash.catFood)}% — vui lòng nạp thêm.` },
    dash.water    < 20 && { id:"wl", type:"warning", title:"Bình nước sắp cạn",     message:"Hệ thống đang tự bơm thêm nước." },
    dash.temp     > 32 && { id:"th", type:"error",   title:"Nhiệt độ quá cao",      message:`${Math.round(dash.temp)}°C — quạt đang được kích hoạt.` },
    dash.temp     < 20 && { id:"tl", type:"error",   title:"Nhiệt độ quá thấp",     message:`${Math.round(dash.temp)}°C — đèn sưởi đang hoạt động.` },
    dash.motion && dash.speakerOn && { id:"mv", type:"info", title:"Phát hiện chuyển động", message:"Thú cưng vào khu vực cấm! Đang phát cảnh báo." },
  ].filter(Boolean).filter(a => !dismissed.has(a.id));

  const advice = dash.temp > 29 ? "Nhiệt độ hơi cao, nên bật quạt làm mát."
    : dash.temp < 22 ? "Nhiệt độ thấp, bật đèn sưởi để giữ ấm."
    : "Môi trường ổn định, thú cưng khỏe mạnh! 🐾";

  return (
    <div style={{ minHeight:"100vh", background:T.bg, padding:"16px",
      fontFamily:"'Nunito','Segoe UI',sans-serif", color:T.text }}>
      <div style={{ maxWidth:920, margin:"0 auto" }}>

        {/* Header */}
        <div style={{ background:`linear-gradient(135deg,${T.primary},${T.primary2})`,
          borderRadius:20, padding:"20px 24px", display:"flex", flexWrap:"wrap",
          alignItems:"center", justifyContent:"space-between", gap:16, marginBottom:16 }}>
          <div style={{ display:"flex", alignItems:"center", gap:14 }}>
            <div style={{ width:48, height:48, borderRadius:"50%",
              background:"rgba(255,255,255,.2)", display:"flex",
              alignItems:"center", justifyContent:"center" }}>
              <PawPrint size={24} color="#fff" />
            </div>
            <div>
              <h1 style={{ margin:0, fontSize:22, fontWeight:800, color:"#fff" }}>PawHome Dashboard</h1>
              <p style={{ margin:0, fontSize:13, color:"rgba(255,255,255,.8)" }}>Hệ thống chăm sóc thú cưng thông minh</p>
            </div>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:10, flexWrap:"wrap" }}>
            <div style={{ display:"flex", alignItems:"center", gap:6,
              background:"rgba(255,255,255,.18)", borderRadius:10, padding:"7px 14px" }}>
              {dash.connected
                ? <><span style={{ width:8, height:8, borderRadius:"50%", background:"#4ADE80",
                    display:"inline-block", animation:"pulse 2s infinite" }} /><Wifi size={14} color="#fff" /></>
                : <><WifiOff size={14} color="#fca5a5" /><span style={{ color:"#fca5a5", fontSize:12 }}>Mất kết nối</span></>
              }
              {dash.connected && <span style={{ color:"#fff", fontSize:13 }}>Đang kết nối</span>}
            </div>
            <div style={{ display:"flex", alignItems:"center", gap:10,
              background:"#fff", borderRadius:12, padding:"8px 16px",
              boxShadow:"0 2px 8px rgba(0,0,0,.1)" }}>
              <span style={{ fontSize:13, fontWeight:700, color:T.primary }}>
                {dash.autoMode ? "🤖 Tự động" : "🎛️ Thủ công"}
              </span>
              <Toggle on={dash.autoMode} onChange={dash.setAutoMode} />
            </div>
          </div>
        </div>

        {/* Alerts */}
        {activeAlerts.length > 0 && (
          <div style={{ display:"flex", flexDirection:"column", gap:8, marginBottom:16 }}>
            {activeAlerts.map(a => (
              <AlertRow key={a.id} type={a.type} title={a.title} message={a.message}
                onClose={() => setDismiss(s => new Set([...s, a.id]))} />
            ))}
          </div>
        )}

        {/* Tabs */}
        <TabBar tabs={[
          { id:"overview",  label:"Tổng quan",  icon:Activity  },
          { id:"controls",  label:"Điều khiển", icon:Settings  },
          { id:"analytics", label:"Phân tích",  icon:Bell      },
        ]} active={tab} onChange={setTab} />

        {/* ══ TAB TỔNG QUAN ══ */}
        {tab === "overview" && (
          <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(155px,1fr))", gap:12 }}>
              <SensorCard title="Nhiệt độ"    value={dash.temp.toFixed(1)}        unit="°C" icon={Thermometer} status={tempStatus(dash.temp)} />
              <SensorCard title="Độ ẩm"       value={Math.round(dash.humidity)}   unit="%"  icon={Droplets}    status="ok" />
              <SensorCard title="Ăn chó"      value={Math.round(dash.dogFood)}    unit="%"  icon={Utensils}    status={statusOf(dash.dogFood,20,40)} />
              <SensorCard title="Ăn mèo"      value={Math.round(dash.catFood)}    unit="%"  icon={Utensils}    status={statusOf(dash.catFood,20,40)} />
              <SensorCard title="Mực nước"    value={Math.round(dash.water)}      unit="%"  icon={Droplet}     status={statusOf(dash.water,20,40)} />
            </div>

            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))", gap:14 }}>
              {/* Pet recognition */}
              <Card>
                <CardTitle icon={PawPrint}>Nhận diện thú cưng</CardTitle>
                {[
                  { id:"dog", name:"Buddy",  sub:"Golden Retriever · 3 tuổi", bg:"#FFF3D0", Icon:Dog, color:"#E8A020", activeBg:"#FFF9EC", activeBorder:T.secondary },
                  { id:"cat", name:"Mochi",  sub:"Mèo Anh lông ngắn · 2 tuổi", bg:"#F0E8FF", Icon:Cat, color:"#7C3AED", activeBg:"#F5F0FF", activeBorder:"#A78BFA" },
                ].map(p => (
                  <div key={p.id} style={{
                    display:"flex", alignItems:"center", gap:12, padding:"10px 14px",
                    borderRadius:12, marginBottom:8,
                    background: dash.detected === p.id ? p.activeBg : T.soft,
                    border:`1.5px solid ${dash.detected === p.id ? p.activeBorder : T.border}`,
                    transition:"all .3s",
                  }}>
                    <div style={{ width:40, height:40, borderRadius:"50%", background:p.bg,
                      display:"flex", alignItems:"center", justifyContent:"center" }}>
                      <p.Icon size={20} color={p.color} />
                    </div>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:13, fontWeight:700 }}>{p.name}</div>
                      <div style={{ fontSize:11, color:T.muted }}>{p.sub}</div>
                    </div>
                    <Badge status={dash.detected === p.id ? "ok" : "warning"}>
                      {dash.detected === p.id ? "Đã phát hiện" : "Không thấy"}
                    </Badge>
                  </div>
                ))}
                <div style={{ background:T.soft, borderRadius:10, padding:"10px 12px",
                  fontSize:12, color:T.text, lineHeight:1.6 }}>
                  <strong style={{ color:T.primary }}>💡 </strong>{advice}
                </div>
              </Card>

              {/* Mức dự trữ */}
              <Card>
                <CardTitle icon={Activity}>Mức dự trữ</CardTitle>
                {[
                  { label:"Thức ăn Buddy", val:dash.dogFood, color:T.secondary },
                  { label:"Thức ăn Mochi", val:dash.catFood, color:"#A78BFA" },
                  { label:"Nước uống",     val:dash.water,   color:T.water },
                ].map(r => (
                  <div key={r.label} style={{ marginBottom:14 }}>
                    <div style={{ display:"flex", justifyContent:"space-between",
                      marginBottom:5, fontSize:13 }}>
                      <span style={{ fontWeight:600, color:T.muted }}>{r.label}</span>
                      <span style={{ fontWeight:700 }}>{Math.round(r.val)}%</span>
                    </div>
                    <Bar value={r.val} color={r.color} />
                  </div>
                ))}
              </Card>
            </div>

            {/* Quick actions */}
            <Card>
              <CardTitle icon={Activity}>Thao tác nhanh</CardTitle>
              {dash.autoMode && (
                <p style={{ fontSize:12, color:T.muted, marginBottom:12 }}>
                  ⚙️ Đang ở chế độ tự động — chuyển sang Thủ công để kích hoạt
                </p>
              )}
              <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                <ActionBtn icon={Utensils} label="Nhả ăn chó"  onClick={dash.feedDog}     disabled={dash.autoMode} color={T.secondary} />
                <ActionBtn icon={Utensils} label="Nhả ăn mèo"  onClick={dash.feedCat}     disabled={dash.autoMode} color="#A78BFA" />
                <ActionBtn icon={Droplet}  label="Bơm nước"    onClick={dash.refillWater} disabled={dash.autoMode} color={T.water} />
                <ActionBtn icon={Camera}   label="Chụp ảnh"    onClick={() => dash.addActivity("info","Đã chụp ảnh")} disabled={false} color={T.primary} />
              </div>
            </Card>

            {/* Device status */}
            <Card>
              <CardTitle icon={Settings}>Trạng thái thiết bị</CardTitle>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(120px,1fr))", gap:10 }}>
                {[
                  { icon:Fan,      label:"Quạt",        on:dash.fanOn,     color:T.primary },
                  { icon:Lightbulb,label:"Đèn sưởi",    on:dash.heaterOn,  color:T.secondary },
                  { icon:Droplet,  label:"Máy bơm",     on:dash.pumpOn,    color:T.water },
                  { icon:Volume2,  label:"Loa cảnh báo",on:dash.speakerOn, color:T.accent },
                ].map(d => (
                  <div key={d.label} style={{ textAlign:"center", padding:"14px 8px",
                    background: d.on ? T.soft : "#F9FAFB", borderRadius:12,
                    border:`0.5px solid ${d.on ? d.color+"44" : T.border}`,
                    transition:"all .25s" }}>
                    <d.icon size={24} color={d.on ? d.color : "#D1D5DB"} />
                    <div style={{ fontSize:11, fontWeight:700, marginTop:8, color:T.text }}>{d.label}</div>
                    <Badge status={d.on ? "ok" : "warning"}>{d.on ? "Bật" : "Tắt"}</Badge>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* ══ TAB ĐIỀU KHIỂN ══ */}
        {tab === "controls" && (
          <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
            {dash.autoMode ? (
              <Card>
                <CardTitle icon={Settings}>Chế độ tự động đang bật</CardTitle>
                <p style={{ fontSize:13, color:T.muted, marginBottom:14 }}>
                  Hệ thống tự điều khiển theo cảm biến. Bật Thủ công để điều khiển trực tiếp.
                </p>
                <div style={{ background:T.soft, borderRadius:12, padding:"14px 16px",
                  display:"flex", flexDirection:"column", gap:8 }}>
                  {["✓ Quạt bật khi nhiệt độ > 30°C","✓ Đèn sưởi bật khi nhiệt độ < 22°C",
                    "✓ Máy bơm tự động khi nước < 20%","✓ Máy ăn chỉ mở khi nhận diện đúng con",
                    "✓ Loa báo khi phát hiện chuyển động khu cấm"
                  ].map(r => <p key={r} style={{ margin:0, fontSize:13 }}>{r}</p>)}
                </div>
              </Card>
            ) : (
              <>
                <Card>
                  <CardTitle icon={Settings}>Điều khiển thiết bị thủ công</CardTitle>
                  <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                    {[
                      { key:"fan",     label:"Quạt mini",    desc:"Làm mát môi trường",        on:dash.fanOn,     color:T.primary,   icon:Fan },
                      { key:"heater",  label:"Đèn sưởi",     desc:"Giữ ấm khi lạnh",           on:dash.heaterOn,  color:T.secondary, icon:Lightbulb },
                      { key:"pump",    label:"Máy bơm nước", desc:"Bơm vào bình chứa",         on:dash.pumpOn,    color:T.water,     icon:Droplet },
                      { key:"speaker", label:"Loa cảnh báo", desc:"Phát âm báo khu vực cấm",   on:dash.speakerOn, color:T.accent,    icon:Volume2 },
                    ].map(d => (
                      <div key={d.key} style={{ display:"flex", alignItems:"center",
                        justifyContent:"space-between", padding:"12px 14px", borderRadius:12,
                        background: d.on ? T.soft : "#F9FAFB",
                        border:`0.5px solid ${d.on ? d.color+"44" : T.border}`,
                        transition:"all .25s" }}>
                        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
                          <div style={{ width:38, height:38, borderRadius:10,
                            background: d.on ? d.color+"22" : "#F3F4F6",
                            display:"flex", alignItems:"center", justifyContent:"center" }}>
                            <d.icon size={18} color={d.on ? d.color : "#9CA3AF"} />
                          </div>
                          <div>
                            <div style={{ fontSize:13, fontWeight:700 }}>{d.label}</div>
                            <div style={{ fontSize:11, color:T.muted }}>{d.desc}</div>
                          </div>
                        </div>
                        <Toggle on={d.on} onChange={() => dash.toggleDevice(d.key, d.on)} />
                      </div>
                    ))}
                  </div>
                </Card>
                <Card>
                  <CardTitle icon={Utensils}>Nhả thức ăn / bơm nước thủ công</CardTitle>
                  <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                    <ActionBtn icon={Utensils} label="Buddy"   onClick={dash.feedDog}     disabled={false} color={T.secondary} />
                    <ActionBtn icon={Utensils} label="Mochi"   onClick={dash.feedCat}     disabled={false} color="#A78BFA" />
                    <ActionBtn icon={Droplet}  label="Bơm nước" onClick={dash.refillWater} disabled={false} color={T.water} />
                  </div>
                </Card>
              </>
            )}
          </div>
        )}

        {/* ══ TAB PHÂN TÍCH ══ */}
        {tab === "analytics" && (
          <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(300px,1fr))", gap:14 }}>
              {[
                { title:"Nhiệt độ (°C)", key:"temp", color:T.accent },
                { title:"Độ ẩm (%)",     key:"hum",  color:T.water },
              ].map(ch => (
                <Card key={ch.key}>
                  <CardTitle>{ch.title}</CardTitle>
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={dash.chartData} margin={{ top:4, right:8, left:-20, bottom:0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                      <XAxis dataKey="time" tick={{ fontSize:11, fill:T.muted }} />
                      <YAxis tick={{ fontSize:11, fill:T.muted }} />
                      <Tooltip contentStyle={{ borderRadius:10, fontSize:12 }} />
                      <Line type="monotone" dataKey={ch.key} stroke={ch.color} strokeWidth={2.5} dot={{ r:3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              ))}
            </div>

            <Card>
              <CardTitle icon={Bell}>Nhật ký hoạt động</CardTitle>
              <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
                {dash.activities.map(a => {
                  const dot = { success:"#22C55E", info:T.primary, warning:"#F4A03A", error:"#E8604C" }[a.type];
                  const ts  = new Date(a.timestamp).toLocaleTimeString("vi-VN", { hour:"2-digit", minute:"2-digit" });
                  return (
                    <div key={a.id} style={{ display:"flex", gap:12, alignItems:"flex-start" }}>
                      <div style={{ width:10, height:10, borderRadius:"50%", background:dot, marginTop:4, flexShrink:0 }} />
                      <div>
                        <div style={{ fontSize:13, color:T.text, fontWeight:500 }}>{a.message}</div>
                        <div style={{ fontSize:11, color:T.muted, marginTop:2 }}>{ts}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          </div>
        )}

        <p style={{ textAlign:"center", fontSize:11, color:T.muted, marginTop:24, paddingBottom:12 }}>
          PawHome v1.0 · Cập nhật lúc {nowStr()}
        </p>
      </div>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
        * { box-sizing:border-box; }
        button:focus { outline:none; }
      `}</style>
    </div>
  );
}
