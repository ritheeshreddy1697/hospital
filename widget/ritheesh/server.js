const express = require('express');
const cors = require('cors');
const path = require('path');
const mongoose = require('mongoose');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/hospilot_db';
const HOSPILOT_API = process.env.HOSPILOT_API_BASE || 'https://hospilot.carer.ai';
const USERNAME = process.env.HOSPILOT_USERNAME || 'medcity_doc_1';
const PASSWORD = process.env.HOSPILOT_PASSWORD || '123456';
const RAG_SERVICE_URL = process.env.RAG_SERVICE_URL || 'http://localhost:8080';

// Serve static frontend files
app.use(express.static(__dirname));

// ── MongoDB Schemas & Connection ──
let isMongoConnected = false;

const userSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  full_name: String,
  title: String,
  employee_id: String,
  department: String,
  email: String,
  phone: String,
  gender: String,
  qualification: String,
  experience_years: String,
  license_number: String,
  shift_preference: String,
  bio: String,
  emergency_contact: String,
  role: { type: String, default: 'doctor' }
});

const User = mongoose.model('User', userSchema);

// Memory fallback store for high reliability if local Mongo server is offline
let memoryUser = {
  username: 'medcity_doc_1',
  password: '123456',
  full_name: "Dr. Neha Sharma",
  title: "Chief Medical Administrator",
  employee_id: "EMP-9042",
  department: "Emergency & Critical Care",
  email: "neha.sharma@careplus.org",
  phone: "+91 98765 43210",
  gender: "Female",
  qualification: "MBBS, MD (Critical Care), MHA",
  experience_years: "12 Years",
  license_number: "MCI-2012-44012",
  shift_preference: "Day Shift (08:00 - 16:00)",
  bio: "Senior medical administrator managing acute emergency workflows, bed allocations, and AI-assisted hospital coordination.",
  emergency_contact: "Dr. Arjun Patel (+91 98111 22233)",
  role: "doctor"
};

mongoose.connect(MONGODB_URI, { serverSelectionTimeoutMS: 2500 })
  .then(async () => {
    isMongoConnected = true;
    console.log('MongoDB Connected successfully at', MONGODB_URI);
    // Seed default user if database is empty
    const existing = await User.findOne({ username: 'medcity_doc_1' });
    if (!existing) {
      await User.create(memoryUser);
      console.log('Default doctor user seeded into MongoDB collection [users].');
    }
  })
  .catch(err => {
    console.log('MongoDB local connection bypassed (using active memory store fallback):', err.message);
  });

// Helper for Hospilot API fetch
async function hospilotFetch(endpoint, options = {}) {
  const url = `${HOSPILOT_API}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Hospilot API Error (${response.status}): ${errorText}`);
  }
  return response.json();
}

// 1. Auth Endpoint (MongoDB + Sandbox API Login)
app.post('/api/auth/login', async (req, res) => {
  try {
    const username = req.body.username || USERNAME;
    const password = req.body.password || PASSWORD;

    // Authenticate with Hospilot Sandbox API for JWT Token
    let token = "jwt_sandbox_token_default";
    try {
      const authRes = await hospilotFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username: USERNAME, password: PASSWORD })
      });
      token = authRes.token;
    } catch (e) {
      console.log('Hospilot API fallback login');
    }

    // Verify or fetch user profile from MongoDB
    let dbUser = memoryUser;
    if (isMongoConnected) {
      const found = await User.findOne({ username });
      if (found) {
        dbUser = found.toObject();
      } else {
        // Create user in MongoDB
        dbUser = await User.create({
          username,
          password,
          full_name: username === 'medcity_doc_1' ? "Dr. Neha Sharma" : username,
          title: "Medical Specialist",
          employee_id: "EMP-" + Math.floor(1000 + Math.random() * 9000),
          department: "General Medicine"
        });
      }
    }

    res.json({
      success: true,
      token,
      user: dbUser,
      mongo_connected: isMongoConnected
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 2. Create Session Endpoint
app.post('/api/sessions', async (req, res) => {
  try {
    const token = req.headers.authorization;
    if (!token) return res.status(401).json({ error: 'Missing Authorization header' });
    const { goal, constraints = '', autonomous = false } = req.body;
    const data = await hospilotFetch('/api/sessions', {
      method: 'POST',
      headers: { Authorization: token },
      body: JSON.stringify({ goal, constraints, autonomous })
    });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 3. Poll Session Status Endpoint
app.get('/api/sessions/:id', async (req, res) => {
  try {
    const token = req.headers.authorization;
    if (!token) return res.status(401).json({ error: 'Missing Authorization header' });
    const data = await hospilotFetch(`/api/sessions/${req.params.id}`, {
      method: 'GET',
      headers: { Authorization: token }
    });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 4. Integrated Plan Route
app.post('/api/plan', async (req, res) => {
  try {
    const goal = req.body.goal || '[CANDIDATE-ritheesh] Check ICU bed capacity for tonight';

    // Step A: Login
    const authRes = await hospilotFetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username: USERNAME, password: PASSWORD })
    });
    const token = authRes.token;

    // Step B: Create Session
    const sessRes = await hospilotFetch('/api/sessions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ goal, constraints: '', autonomous: false })
    });
    const sessionId = sessRes.session_id;

    // Step C: Poll for completion
    let pipeline = null;
    let pollAttempts = 0;
    const maxAttempts = 25;

    while (pollAttempts < maxAttempts) {
      await new Promise((r) => setTimeout(r, 2000));
      pollAttempts++;

      const pollRes = await hospilotFetch(`/api/sessions/${sessionId}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (pollRes.pipeline && pollRes.pipeline.length > 0) {
        pipeline = pollRes.pipeline;
        break;
      }
    }

    res.json({
      success: true,
      token,
      sessionId,
      pipeline,
      attempts: pollAttempts
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 5. RAG Proxy Endpoint
app.post('/api/ask', async (req, res) => {
  try {
    const { question } = req.body;
    if (!question) return res.status(400).json({ error: 'Question is required' });

    const ragResponse = await fetch(`${RAG_SERVICE_URL}/api/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });

    if (!ragResponse.ok) throw new Error(`RAG Service error: ${ragResponse.statusText}`);

    const data = await ragResponse.json();
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 6. MongoDB User Profile Endpoints
app.get('/api/his/profile', async (req, res) => {
  try {
    if (isMongoConnected) {
      const u = await User.findOne({ username: 'medcity_doc_1' });
      if (u) return res.json(u);
    }
    res.json(memoryUser);
  } catch (err) {
    res.json(memoryUser);
  }
});

app.post('/api/his/profile', async (req, res) => {
  try {
    if (isMongoConnected) {
      let u = await User.findOne({ username: 'medcity_doc_1' });
      if (u) {
        Object.assign(u, req.body);
        await u.save();
        return res.json({ success: true, profile: u, source: 'MongoDB' });
      }
    }
    memoryUser = { ...memoryUser, ...req.body };
    res.json({ success: true, profile: memoryUser, source: 'MemoryStore' });
  } catch (err) {
    memoryUser = { ...memoryUser, ...req.body };
    res.json({ success: true, profile: memoryUser, error: err.message });
  }
});

// 7. Dynamic HIS Endpoints
app.get('/api/his/beds', (req, res) => {
  res.json({
    summary: { total: 104, occupied: 52, available: 22, reserved: 26, dirty: 4 },
    wards: [
      { name: "ICU", total: 30, available: 6, occupied: 17, reserved: 3, dirty: 4 },
      { name: "General Ward", total: 19, available: 4, occupied: 6, reserved: 9, dirty: 0 },
      { name: "Semi-Private Ward", total: 6, available: 1, occupied: 3, reserved: 2, dirty: 0 },
      { name: "Private Ward", total: 8, available: 2, occupied: 2, reserved: 4, dirty: 0 },
      { name: "Emergency", total: 13, available: 4, occupied: 3, reserved: 6, dirty: 0 },
      { name: "Cardiology", total: 8, available: 2, occupied: 2, reserved: 4, dirty: 0 },
      { name: "Orthopedics", total: 8, available: 1, occupied: 1, reserved: 6, dirty: 0 },
      { name: "Pediatrics", total: 8, available: 2, occupied: 2, reserved: 4, dirty: 0 }
    ]
  });
});

app.get('/api/his/ipd', (req, res) => {
  res.json([
    { id: "ADM-101", name: "Rajesh Kumar", uhid: "UHID-9821", bed: "ICU-102", ward: "ICU", doctor: "Dr. Neha Sharma", admitted: "2026-08-11", status: "Critical", discharge_ready: false },
    { id: "ADM-102", name: "Ananya Roy", uhid: "UHID-9822", bed: "GW-204", ward: "General Ward", doctor: "Dr. Arjun Patel", admitted: "2026-08-10", status: "Stable", discharge_ready: true },
    { id: "ADM-103", name: "Vikram Singh", uhid: "UHID-9823", bed: "PV-401", ward: "Private Ward", doctor: "Dr. Meera Iyer", admitted: "2026-08-12", status: "Recovering", discharge_ready: false },
    { id: "ADM-104", name: "Suresh Gupta", uhid: "UHID-9824", bed: "CARD-602", ward: "Cardiology", doctor: "Dr. Rahul Verma", admitted: "2026-08-09", status: "Under Observation", discharge_ready: true }
  ]);
});

app.get('/api/his/opd', (req, res) => {
  res.json({
    slots: [
      { doctor: "Dr. Neha Sharma", spec: "General Medicine", time: "09:00 AM - 01:00 PM", status: "Available", max: 15, booked: 12 },
      { doctor: "Dr. Arjun Patel", spec: "General Surgery", time: "10:00 AM - 02:00 PM", status: "Full", max: 12, booked: 12 },
      { doctor: "Dr. Meera Iyer", spec: "Orthopedics", time: "02:00 PM - 06:00 PM", status: "Available", max: 10, booked: 6 },
      { doctor: "Dr. Priya Das", spec: "Pediatrics", time: "09:00 AM - 01:00 PM", status: "Available", max: 20, booked: 14 }
    ],
    waitlist: [
      { name: "Karan Mehta", phone: "+91 9876543210", spec: "Cardiology", priority: "High", reason: "Chest Pain follow-up" },
      { name: "Sunita Devi", phone: "+91 9876543211", spec: "Orthopedics", priority: "Medium", reason: "Joint Pain consultation" }
    ]
  });
});

app.get('/api/his/er', (req, res) => {
  res.json([
    { id: "ER-501", name: "Amit Shah", age: 45, complaint: "Acute Shortness of Breath", triage_score: 1, status: "Intubated", wait_time: "5m", critical: true },
    { id: "ER-502", name: "Priya Malhotra", age: 29, complaint: "Abdominal Pain & Fever", triage_score: 2, status: "Triage Exam", wait_time: "15m", critical: false },
    { id: "ER-503", name: "Rohan Verma", age: 62, complaint: "Suspected Fracture Right Leg", triage_score: 3, status: "X-Ray Pending", wait_time: "34m", critical: false },
    { id: "ER-504", name: "Geeta Joshi", age: 54, complaint: "High Blood Pressure", triage_score: 2, status: "Monitoring", wait_time: "22m", critical: true }
  ]);
});

app.get('/api/his/lab', (req, res) => {
  res.json([
    { order_id: "LAB-901", patient: "Rajesh Kumar", test: "ABG & Electrolytes", priority: "STAT", status: "Completed", flag: "Critical High", result: "pH 7.21, pCO2 55" },
    { order_id: "LAB-902", patient: "Priya Malhotra", test: "Complete Blood Count", priority: "Urgent", status: "In Progress", flag: "Normal", result: "Pending" },
    { order_id: "LAB-903", patient: "Rohan Verma", test: "X-Ray Right Femur", priority: "Routine", status: "Completed", flag: "Abnormal", result: "Fracture shaft of femur" }
  ]);
});

app.get('/api/his/pharmacy', (req, res) => {
  res.json([
    { code: "MED-101", name: "Inj. Noradrenaline 4mg", category: "ICU Emergency", stock: 45, min_stock: 50, status: "Low Stock" },
    { code: "MED-102", name: "Tab. Augmentin 625mg", category: "Antibiotic", stock: 450, min_stock: 100, status: "Adequate" },
    { code: "MED-103", name: "Inj. Heparin 5000 IU", category: "Anticoagulant", stock: 18, min_stock: 30, status: "Critical" },
    { code: "MED-104", name: "IV Normal Saline 500ml", category: "Fluids", stock: 800, min_stock: 200, status: "Adequate" }
  ]);
});

app.get('/api/his/billing', (req, res) => {
  res.json({
    summary: { total_billed: "₹14,50,000", total_collected: "₹11,20,000", pending_claims: "₹3,30,000" },
    claims: [
      { claim_no: "CLM-8801", patient: "Rajesh Kumar", tpa: "Star Health Insurance", amount: "₹2,50,000", status: "Under Review", risk: "Low" },
      { claim_no: "CLM-8802", patient: "Ananya Roy", tpa: "HDFC ERGO", amount: "₹1,20,000", status: "Approved", risk: "Low" },
      { claim_no: "CLM-8803", patient: "Suresh Gupta", tpa: "Niva Bupa", amount: "₹3,80,000", status: "Query Raised", risk: "Medium" }
    ]
  });
});

app.get('/api/his/reports', (req, res) => {
  res.json({
    occupancy_rate: "82%",
    avg_length_of_stay: "4.2 Days",
    er_turnaround_time: "34 mins",
    daily_collections: { cash: "₹1,20,000", upi: "₹3,40,000", card: "₹4,10,000", insurance: "₹2,50,000" }
  });
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Hospilot MongoDB Backend Server running on http://localhost:${PORT}`);
  });
}

module.exports = app;
