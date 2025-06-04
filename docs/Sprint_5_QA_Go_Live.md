# Sprint 5 – QA, Polish, Go-Live

**Duration**: 1 week  
**Goal**: Finalize the MVP, run comprehensive tests, polish user flows, and deploy the public demo line.

---

## ✅ Step-by-Step Tasks

### 1. QA and Regression Testing
- [ ] Test all flows (appointment booking, objections, lead capture)
- [ ] Use at least 10 test calls with real-time feedback
- [ ] Validate:
  - Audio clarity and timing
  - Memory consistency
  - Error handling and fallbacks
- [ ] Manually review:
  - Dashboard UI
  - Prompt response quality
  - Stored data formats

### 2. Final Prompt Tuning
- [ ] Review improvement logs from Vertex feedback agent
- [ ] Choose optimal response versions
- [ ] Lock in v1.0.0 of prompt and backup

### 3. Performance and Latency Checks
- [ ] Test cold start time from Vapi → ADK → LLM response
- [ ] Add logging timestamps in backend
- [ ] Target: end-to-end response < 2 seconds

### 4. Configure Demo Phone Line
- [ ] Assign dedicated Twilio/Vapi number for Roxy demo
- [ ] Add intro script: “Hi, this is Roxy, a VoiceHive assistant. How can I help today?”
- [ ] Record a voicemail fallback if response fails
- [ ] Enable call tracking and logging

### 5. Deployment & Launch
- [ ] Confirm all Cloud Functions, Run services, dashboard, Mem0, Vertex agents are stable
- [ ] Push to GitHub main with MVP release tag
- [ ] Deploy public site with embedded demo number

---

## 📦 Deliverables
- Fully tested MVP agent live on demo line
- Clean prompts, fast performance
- Monitored infrastructure
- Publicly accessible dashboard with admin login

## ✅ Launch Checklist
- [ ] Vapi webhook stable
- [ ] Dashboard deployed
- [ ] Monitoring rules active
- [ ] Demo number call works start to finish
- [ ] GitHub repo tagged and cleaned

---

**Congrats — MVP is live. Time to start onboarding customers.**
