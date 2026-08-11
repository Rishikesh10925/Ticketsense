import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import Shell from "./components/Shell";
import Dashboard from "./pages/Dashboard";
import Tickets from "./pages/Tickets";
import NewTicket from "./pages/NewTicket";
import TicketWorkspace from "./pages/TicketWorkspace";
import Knowledge from "./pages/Knowledge";
import Incidents from "./pages/Incidents";
import Notifications from "./pages/Notifications";
import Login from "./pages/Login";
import { AIMetrics, Audit, Integrations } from "./pages/AdminData";
import { Loading } from "./components/States";
import "./styles.css";

function Protected(){const {user,loading}=useAuth();const location=useLocation();if(loading)return <Loading label="Restoring secure session..."/>;if(!user)return <Navigate to="/login" state={{from:location.pathname}} replace/>;return <Shell><Routes><Route path="/dashboard" element={<Dashboard/>}/><Route path="/tickets" element={<Tickets/>}/><Route path="/queue" element={<Tickets/>}/><Route path="/escalations" element={<Tickets escalated/>}/><Route path="/tickets/new" element={<NewTicket/>}/><Route path="/tickets/:id" element={<TicketWorkspace/>}/><Route path="/knowledge" element={<Knowledge/>}/><Route path="/incidents" element={<Incidents/>}/><Route path="/notifications" element={<Notifications/>}/><Route path="/ai" element={<AIMetrics/>}/><Route path="/reports" element={<AIMetrics/>}/><Route path="/audit" element={<Audit/>}/><Route path="/integrations" element={<Integrations/>}/><Route path="/settings" element={<div className="content"><div className="page-title"><div><h1>Settings</h1><p>Configuration is managed through authorized backend endpoints. No editable settings endpoint is currently available.</p></div></div></div>}/><Route path="*" element={<Navigate to="/dashboard" replace/>}/></Routes></Shell>}
export default function App(){return <BrowserRouter><AuthProvider><Routes><Route path="/login" element={<Login/>}/><Route path="/*" element={<Protected/>}/></Routes></AuthProvider></BrowserRouter>}
