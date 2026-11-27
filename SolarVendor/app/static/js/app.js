/**
 * SolarPulse ERP - Main Client JavaScript Application
 * Generic Solar Vendor Management & CRM Suite
 */

let currentRole = "Admin";
let charts = {};
let currentLeads = [];
let currentProjects = [];
let companySettings = {};

// DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initApp();
  lucide.createIcons();
});

async function initApp() {
  await loadTrialStatus();
  await loadCompanySettings();
  await loadDashboard();
  setupGlobalSearch();

  // Listen to hash change for tab navigation
  window.addEventListener("hashchange", () => {
    const hash = window.location.hash.replace("#", "") || "dashboard";
    switchTab(hash);
  });

  // Run initial calculator sizing
  runLiveCalculator();

  // Auto-check updates on background launch
  setTimeout(() => {
    checkUpdates(false);
  }, 1500);
}

async function loadTrialStatus() {
  try {
    const res = await fetch("/api/trial-status");
    const data = await res.json();
    const badgeText = document.getElementById("trialBadgeText");
    const badge = document.getElementById("trialBadge");
    if (badgeText && badge) {
      if (data.unlocked) {
        badge.className = "bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-300 flex items-center space-x-1";
        badgeText.innerText = "Full License: Lifetime Active";
      } else if (data.is_expired) {
        badge.className = "bg-red-100 text-red-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-red-300 flex items-center space-x-1";
        badgeText.innerText = "Demo Expired (Locked)";
      } else {
        badge.className = "bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-amber-300 flex items-center space-x-1";
        badgeText.innerText = `7-Day Demo: ${data.days_left} Days Left`;
      }
    }
  } catch (err) {
    console.error("Error loading trial status:", err);
  }
}

// ================= NAVIGATION & TABS =================
function switchTab(tabName) {
  // Update nav items
  document.querySelectorAll(".nav-item").forEach(item => {
    item.classList.remove("active");
    if (item.getAttribute("data-tab") === tabName) {
      item.classList.add("active");
    }
  });

  // Update tab content
  document.querySelectorAll(".tab-content").forEach(tab => {
    tab.classList.remove("active");
  });
  const activeTab = document.getElementById(`tab-${tabName}`);
  if (activeTab) {
    activeTab.classList.add("active");
  }

  window.location.hash = tabName;

  // Load specific tab data
  if (tabName === "dashboard") loadDashboard();
  else if (tabName === "leads") loadLeads();
  else if (tabName === "surveys") loadSurveys();
  else if (tabName === "calculator") runLiveCalculator();
  else if (tabName === "quotations") loadQuotations();
  else if (tabName === "projects") loadProjects();
  else if (tabName === "discom") loadDiscom();
  else if (tabName === "invoices") loadInvoices();
  else if (tabName === "payments") loadPayments();
  else if (tabName === "updates") loadUpdatesTab();

  lucide.createIcons();
}

// ================= ROLE SWITCHER =================
function changeDemoRole(role) {
  currentRole = role;
  const roleDescriptions = {
    "Admin": "Full Administrative & Financial Access (Executive KPIs, All Controls)",
    "Sales": "Sales Mode: Focused on Leads, Calculator & Quotations generation",
    "Survey": "Site Engineer Mode: Focused on Roof Feasibility & Shadow Analysis",
    "Project": "Project Head Mode: Focused on Installation Milestones & Material Delivery",
    "DISCOM": "DISCOM Officer Mode: Focused on Net Metering Applications & Meter Sync",
    "Accounts": "Accounts Mode: Focused on Tax Invoices, Balance Aging & Payment Receipts"
  };

  showToast(`Switched view to ${role}: ${roleDescriptions[role]}`, "info");
}

// ================= TOAST NOTIFICATION =================
function showToast(message, type = "success") {
  const toast = document.getElementById("toastNotification");
  const msgEl = document.getElementById("toastMsg");
  const iconEl = document.getElementById("toastIcon");

  msgEl.innerText = message;
  if (type === "success") {
    iconEl.className = "text-emerald-400";
    iconEl.innerHTML = `<i data-lucide="check-circle" class="w-5 h-5"></i>`;
  } else if (type === "info") {
    iconEl.className = "text-blue-400";
    iconEl.innerHTML = `<i data-lucide="info" class="w-5 h-5"></i>`;
  } else {
    iconEl.className = "text-red-400";
    iconEl.innerHTML = `<i data-lucide="alert-circle" class="w-5 h-5"></i>`;
  }
  lucide.createIcons();

  toast.classList.remove("translate-y-20", "opacity-0", "pointer-events-none");
  setTimeout(() => {
    toast.classList.add("translate-y-20", "opacity-0", "pointer-events-none");
  }, 3500);
}

// ================= COMPANY SETTINGS / WHITE-LABEL =================
async function loadCompanySettings() {
  try {
    const res = await fetch("/api/settings");
    companySettings = await res.json();
    if (companySettings.company_name) {
      document.getElementById("brandCompanyName").innerText = companySettings.company_name;
      document.getElementById("brandTagline").innerText = companySettings.tagline || "Rooftop Solar ERP";
    }
  } catch (err) {
    console.error("Error loading settings:", err);
  }
}

function openSettingsModal() {
  document.getElementById("setCompanyName").value = companySettings.company_name || "";
  document.getElementById("setTagline").value = companySettings.tagline || "";
  document.getElementById("setPhone").value = companySettings.phone || "";
  document.getElementById("setEmail").value = companySettings.email || "";
  document.getElementById("setAddress").value = companySettings.address || "";
  document.getElementById("setGstin").value = companySettings.gstin || "";
  document.getElementById("setPan").value = companySettings.pan || "";
  document.getElementById("setBankName").value = companySettings.bank_name || "";
  document.getElementById("setAccountNo").value = companySettings.account_no || "";
  document.getElementById("setIfsc").value = companySettings.ifsc_code || "";
  document.getElementById("setUpi").value = companySettings.upi_id || "";

  openModal("settingsModal");
}

async function handleSettingsSubmit(e) {
  e.preventDefault();
  const payload = {
    company_name: document.getElementById("setCompanyName").value,
    tagline: document.getElementById("setTagline").value,
    phone: document.getElementById("setPhone").value,
    email: document.getElementById("setEmail").value,
    address: document.getElementById("setAddress").value,
    gstin: document.getElementById("setGstin").value,
    pan: document.getElementById("setPan").value,
    bank_name: document.getElementById("setBankName").value,
    account_no: document.getElementById("setAccountNo").value,
    ifsc_code: document.getElementById("setIfsc").value,
    upi_id: document.getElementById("setUpi").value,
    default_state: "Odisha",
    default_discom: "TPCODL",
    theme_color: "#0f766e"
  };

  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      closeModal("settingsModal");
      showToast("Vendor Profile & Branding updated!");
      await loadCompanySettings();
    }
  } catch (err) {
    showToast("Error updating settings", "error");
  }
}

async function resetDemoData() {
  if (confirm("Reset application to pristine demo state with Odisha DISCOMs and default realistic data?")) {
    try {
      const res = await fetch("/api/reset-demo", { method: "POST" });
      if (res.ok) {
        showToast("Demo data successfully reset!");
        await loadCompanySettings();
        await loadDashboard();
      }
    } catch (err) {
      showToast("Error resetting demo", "error");
    }
  }
}

// ================= MODAL HELPERS =================
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove("hidden");
    lucide.createIcons();
  }
}
function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add("hidden");
}

// ================= DASHBOARD & CHARTS =================
async function loadDashboard() {
  try {
    const res = await fetch("/api/dashboard");
    const data = await res.json();
    const m = data.metrics;

    // Update KPI cards
    document.getElementById("kpiTotalLeads").innerText = m.total_leads;
    document.getElementById("kpiWonLeads").innerText = `${m.won_leads} won`;
    document.getElementById("kpiConversionRate").innerText = `${m.conversion_rate}%`;
    document.getElementById("leadCountBadge").innerText = m.total_leads;

    document.getElementById("kpiActiveProjects").innerText = m.active_projects;
    document.getElementById("kpiCommissionedProjects").innerText = m.commissioned_projects;
    document.getElementById("activeProjectsBadge").innerText = m.active_projects;

    document.getElementById("kpiInstalledKw").innerText = m.installed_kw;
    document.getElementById("kpiPipelineKw").innerText = m.pipeline_kw;

    document.getElementById("kpiTotalContract").innerText = `₹${(m.total_contract_value / 100000).toFixed(1)}L`;
    document.getElementById("kpiPendingCollection").innerText = `₹${(m.pending_collection / 1000).toFixed(0)}k`;
    document.getElementById("kpiCollected").innerText = `${(m.total_collected / 100000).toFixed(1)}L`;

    document.getElementById("kpiDiscomPending").innerText = m.discom_pending;
    document.getElementById("kpiSubsidyPipeline").innerText = `${(m.subsidy_pipeline / 1000).toFixed(0)}k`;

    // Render Dashboard Projects Table
    const pTable = document.getElementById("dashboardProjectsTable");
    pTable.innerHTML = "";
    data.active_projects.forEach(p => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition cursor-pointer";
      tr.onclick = () => switchTab("projects");
      tr.innerHTML = `
        <td class="py-2.5 px-3 font-bold text-slate-800">${p.project_code}</td>
        <td class="py-2.5 px-3">
          <div class="font-semibold text-slate-800">${p.customer_name}</div>
          <div class="text-[10px] text-slate-400">${p.city}</div>
        </td>
        <td class="py-2.5 px-3 font-semibold text-solar-700">${p.capacity_kw} kW</td>
        <td class="py-2.5 px-3"><span class="bg-slate-100 text-slate-700 font-mono px-1.5 py-0.5 rounded text-[10px]">${p.discom}</span></td>
        <td class="py-2.5 px-3">
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
            p.stage === 'Commissioned' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
          }">${p.stage}</span>
        </td>
        <td class="py-2.5 px-3">
          <div class="w-24 bg-slate-200 rounded-full h-1.5 overflow-hidden">
            <div class="bg-solar-600 h-1.5 rounded-full" style="width: ${p.progress_pct}%"></div>
          </div>
          <span class="text-[9px] text-slate-400">${p.progress_pct}%</span>
        </td>
      `;
      pTable.appendChild(tr);
    });

    // Render Growth Chart
    renderGrowthChart(data.charts.months, data.charts.monthly_kw, data.charts.monthly_revenue_lakhs);

    // Render Funnel Chart
    renderFunnelChart(data.charts.funnel);

    // Render DISCOM Status Chart
    renderDiscomChart(data.charts.discom_breakdown);

  } catch (err) {
    console.error("Dashboard load error:", err);
  }
}

function renderGrowthChart(labels, kwData, revData) {
  const ctx = document.getElementById("growthChart").getContext("2d");
  if (charts.growth) charts.growth.destroy();

  charts.growth = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Installed Capacity (kW)",
          data: kwData,
          backgroundColor: "rgba(15, 118, 110, 0.8)",
          borderRadius: 6,
          yAxisID: "y"
        },
        {
          label: "Revenue (₹ Lakhs)",
          data: revData,
          type: "line",
          borderColor: "#f59e0b",
          backgroundColor: "#f59e0b",
          borderWidth: 3,
          tension: 0.3,
          yAxisID: "y1"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { boxWidth: 12, font: { size: 11 } } }
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          title: { display: true, text: "Capacity (kW)", font: { size: 10 } }
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          grid: { drawOnChartArea: false },
          title: { display: true, text: "Revenue (₹ Lakhs)", font: { size: 10 } }
        }
      }
    }
  });
}

function renderFunnelChart(funnel) {
  const ctx = document.getElementById("funnelChart").getContext("2d");
  if (charts.funnel) charts.funnel.destroy();

  charts.funnel = new Chart(ctx, {
    type: "bar",
    data: {
      labels: Object.keys(funnel),
      datasets: [{
        label: "Projects / Enquiries",
        data: Object.values(funnel),
        backgroundColor: [
          "#3b82f6",
          "#6366f1",
          "#f59e0b",
          "#0d9488",
          "#10b981"
        ],
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { beginAtZero: true }
      }
    }
  });
}

function renderDiscomChart(discomBreakdown) {
  const ctx = document.getElementById("discomChart").getContext("2d");
  if (charts.discom) charts.discom.destroy();

  const labels = Object.keys(discomBreakdown);
  const data = Object.values(discomBreakdown);

  charts.discom = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels.length ? labels : ["Applied", "Approved", "Commissioned"],
      datasets: [{
        data: data.length ? data : [1, 2, 1],
        backgroundColor: ["#38bdf8", "#818cf8", "#34d399", "#fbbf24"]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 10 } } }
      }
    }
  });
}

// ================= LEADS & CRM =================
async function loadLeads() {
  const status = document.getElementById("leadStatusFilter").value;
  const discom = document.getElementById("leadDiscomFilter").value;

  try {
    let url = `/api/leads?status=${status}&discom=${discom}`;
    const res = await fetch(url);
    currentLeads = await res.json();

    document.getElementById("leadsFilteredCount").innerText = currentLeads.length;
    const tbody = document.getElementById("leadsTableBody");
    tbody.innerHTML = "";

    currentLeads.forEach(lead => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      tr.innerHTML = `
        <td class="py-3 px-4">
          <div class="font-bold text-slate-800">${lead.name}</div>
          <div class="text-[10px] text-slate-400">Assigned: ${lead.assigned_to}</div>
        </td>
        <td class="py-3 px-4">
          <div class="font-medium text-slate-700">${lead.phone}</div>
          <div class="text-[10px] text-slate-400">${lead.email || 'No email'}</div>
        </td>
        <td class="py-3 px-4">
          <div class="text-slate-800 font-medium">${lead.city}, ${lead.state}</div>
          <div class="text-[10px] text-slate-400 max-w-xs truncate">${lead.address}</div>
        </td>
        <td class="py-3 px-4">
          <span class="font-mono bg-slate-100 text-slate-800 px-2 py-0.5 rounded text-[11px] font-semibold">${lead.consumer_no}</span>
          <div class="text-[10px] font-bold text-solar-700 mt-0.5">${lead.discom} (${lead.category})</div>
        </td>
        <td class="py-3 px-4">
          <div class="font-bold text-slate-800">₹${lead.avg_monthly_bill} / mo</div>
          <div class="text-[10px] text-slate-500">${lead.sanctioned_load} kW Load • <b class="text-solar-700">${lead.proposed_capacity_kw} kW Solar</b></div>
        </td>
        <td class="py-3 px-4">
          <span class="px-2 py-1 rounded-full text-[10px] font-bold ${
            lead.status === 'Won' ? 'bg-emerald-100 text-emerald-800' :
            lead.status === 'Quoted' ? 'bg-blue-100 text-blue-800' :
            lead.status === 'Survey Scheduled' ? 'bg-purple-100 text-purple-800' :
            'bg-amber-100 text-amber-800'
          }">${lead.status}</span>
        </td>
        <td class="py-3 px-4 text-right space-x-1">
          <button onclick="quickSizeLead(${lead.id})" title="Size in Calculator" class="p-1.5 text-solar-700 hover:bg-solar-50 rounded">
            <i data-lucide="calculator" class="w-4 h-4"></i>
          </button>
          <button onclick="createQuoteForLead(${lead.id})" title="Generate Quotation" class="p-1.5 text-amber-600 hover:bg-amber-50 rounded">
            <i data-lucide="file-text" class="w-4 h-4"></i>
          </button>
          <button onclick="deleteLead(${lead.id})" title="Delete Lead" class="p-1.5 text-red-500 hover:bg-red-50 rounded">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading leads:", err);
  }
}

function openLeadModal() {
  document.getElementById("leadForm").reset();
  openModal("leadModal");
}

async function handleLeadSubmit(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById("leadName").value,
    phone: document.getElementById("leadPhone").value,
    email: document.getElementById("leadEmail").value,
    consumer_no: document.getElementById("leadConsumerNo").value,
    state: document.getElementById("leadState").value,
    city: document.getElementById("leadCity").value,
    discom: document.getElementById("leadDiscom").value,
    address: document.getElementById("leadAddress").value,
    avg_monthly_bill: parseFloat(document.getElementById("leadBill").value) || 4500,
    sanctioned_load: parseFloat(document.getElementById("leadLoad").value) || 5,
    proposed_capacity_kw: parseFloat(document.getElementById("leadProposedKw").value) || 5,
    notes: document.getElementById("leadNotes").value,
    category: "Residential",
    status: "New"
  };

  try {
    const res = await fetch("/api/leads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      closeModal("leadModal");
      showToast("Customer Lead added successfully!");
      loadLeads();
      loadDashboard();
    }
  } catch (err) {
    showToast("Error adding lead", "error");
  }
}

async function deleteLead(id) {
  if (confirm("Are you sure you want to delete this lead?")) {
    try {
      await fetch(`/api/leads/${id}`, { method: "DELETE" });
      showToast("Lead deleted");
      loadLeads();
      loadDashboard();
    } catch (err) {
      showToast("Error deleting lead", "error");
    }
  }
}

function quickSizeLead(id) {
  const lead = currentLeads.find(l => l.id === id);
  if (lead) {
    document.getElementById("calcBillInput").value = lead.avg_monthly_bill;
    document.getElementById("calcLoadInput").value = lead.sanctioned_load;
    document.getElementById("calcRoofInput").value = lead.roof_area_sqft || 600;
    switchTab("calculator");
  }
}

// ================= SITE SURVEY =================
async function loadSurveys() {
  try {
    const res = await fetch("/api/surveys");
    const surveys = await res.json();
    const container = document.getElementById("surveysCardsContainer");
    container.innerHTML = "";

    surveys.forEach(s => {
      const card = document.createElement("div");
      card.className = "bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3";
      card.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400">Date: ${s.survey_date || 'Recent'}</span>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${
            s.feasibility_status === 'Feasible' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
          }">${s.feasibility_status}</span>
        </div>
        <div>
          <h4 class="font-bold text-slate-800 text-base">${s.customer_name}</h4>
          <p class="text-xs text-slate-500">${s.address} • <b class="text-slate-700">${s.discom}</b></p>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-2.5 rounded-lg border border-slate-100">
          <div><span class="text-slate-500">Roof Area:</span> <b class="text-slate-800">${s.available_roof_area} sqft</b></div>
          <div><span class="text-slate-500">Shadow-Free:</span> <b class="text-emerald-700">${s.shadow_free_area} sqft</b></div>
          <div><span class="text-slate-500">Structure:</span> <b class="text-slate-800">${s.roof_type}</b></div>
          <div><span class="text-slate-500">Recommended:</span> <b class="text-solar-700 font-bold">${s.recommended_capacity_kw} kW</b></div>
        </div>
        <div class="text-[11px] text-slate-500 flex items-center justify-between pt-1">
          <span>Surveyor: <b>${s.surveyor_name}</b></span>
          <span>DC: ${s.cable_distance_dc_m}m | AC: ${s.cable_distance_ac_m}m</span>
        </div>
        <div class="pt-2 border-t border-slate-100 flex justify-end space-x-2">
          <button onclick="createQuoteForLead(${s.lead_id})" class="text-xs font-semibold text-solar-700 hover:underline">
            Generate Proposal →
          </button>
        </div>
      `;
      container.appendChild(card);
    });

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading surveys:", err);
  }
}

async function openSurveyModal() {
  // Populate Leads Dropdown
  const sel = document.getElementById("surveyLeadId");
  sel.innerHTML = "";
  if (!currentLeads.length) await loadLeads();

  currentLeads.forEach(l => {
    const opt = document.createElement("option");
    opt.value = l.id;
    opt.innerText = `${l.name} (${l.consumer_no} - ${l.city})`;
    sel.appendChild(opt);
  });

  openModal("surveyModal");
}

async function handleSurveySubmit(e) {
  e.preventDefault();
  const payload = {
    lead_id: parseInt(document.getElementById("surveyLeadId").value),
    surveyor_name: document.getElementById("surveyorName").value,
    roof_type: document.getElementById("surveyRoofType").value,
    available_roof_area: parseFloat(document.getElementById("surveyTotalArea").value),
    shadow_free_area: parseFloat(document.getElementById("surveyShadowFree").value),
    recommended_capacity_kw: parseFloat(document.getElementById("surveyRecommendedKw").value),
    cable_distance_dc_m: parseFloat(document.getElementById("surveyDcDist").value),
    cable_distance_ac_m: parseFloat(document.getElementById("surveyAcDist").value),
    feasibility_status: document.getElementById("surveyStatus").value,
    remarks: "Survey verified"
  };

  try {
    const res = await fetch("/api/surveys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      closeModal("surveyModal");
      showToast("Site Feasibility Survey recorded!");
      loadSurveys();
      loadDashboard();
    }
  } catch (err) {
    showToast("Error saving survey", "error");
  }
}

// ================= SOLAR CALCULATOR =================
let lastCalcResult = null;

async function runLiveCalculator() {
  const bill = parseFloat(document.getElementById("calcBillInput")?.value) || 3000;
  const load = parseFloat(document.getElementById("calcLoadInput")?.value) || 4.0;
  const roof = parseFloat(document.getElementById("calcRoofInput")?.value) || 450;
  const desiredCap = parseFloat(document.getElementById("calcDesiredCapInput")?.value) || null;
  const unitsDay = parseFloat(document.getElementById("calcUnitsDayInput")?.value) || null;
  const manualGross = parseFloat(document.getElementById("calcGrossCostInput")?.value) || null;
  const gstRate = parseFloat(document.getElementById("calcGstRateInput")?.value) ?? 5.0;
  const netMeterCost = parseFloat(document.getElementById("calcNetMeterCostInput")?.value) ?? 3500;
  const transportCost = parseFloat(document.getElementById("calcTransportCostInput")?.value) ?? 2500;
  const subsidy = parseFloat(document.getElementById("calcSubsidyInput")?.value) ?? 138000;
  const category = document.getElementById("calcCategoryInput")?.value || "Residential";
  const tariff = parseFloat(document.getElementById("calcTariffInput")?.value) || 6.5;

  let url = `/api/calculator/calculate?monthly_bill=${bill}&sanctioned_load=${load}&roof_area=${roof}&tariff=${tariff}&category=${category}&gst_rate=${gstRate}&net_meter_cost=${netMeterCost}&transportation_cost=${transportCost}`;
  if (desiredCap) url += `&desired_capacity=${desiredCap}`;
  if (unitsDay) url += `&units_per_day=${unitsDay}`;
  if (manualGross) url += `&manual_gross_cost=${manualGross}`;
  if (subsidy !== null && !isNaN(subsidy)) url += `&manual_subsidy=${subsidy}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    lastCalcResult = data;

    // Update Highlight Cards
    const elCap = document.getElementById("calcResCapacity");
    if (elCap) elCap.innerText = data.capacity_kw;

    const elPanels = document.getElementById("calcResPanels");
    if (elPanels) elPanels.innerText = data.panel_qty;

    const elDailyDisp = document.getElementById("calcResDailyGenDisplay");
    if (elDailyDisp) elDailyDisp.innerText = data.units_per_day;

    const elSubsidy = document.getElementById("calcResSubsidy");
    if (elSubsidy) elSubsidy.innerText = data.subsidy_eligible.toLocaleString('en-IN');

    const elNetCost = document.getElementById("calcResNetCost");
    if (elNetCost) elNetCost.innerText = data.net_cost.toLocaleString('en-IN');

    const elPayback = document.getElementById("calcResPayback");
    if (elPayback) elPayback.innerText = data.payback_years;

    // Detailed Metrics
    const elDailyGen = document.getElementById("calcResDailyGen");
    if (elDailyGen) elDailyGen.innerText = data.units_per_day;

    const elMonthlyGen = document.getElementById("calcResMonthlyGen");
    if (elMonthlyGen) elMonthlyGen.innerText = data.monthly_generation_kwh;

    const elMonthlySave = document.getElementById("calcResMonthlySave");
    if (elMonthlySave) elMonthlySave.innerText = data.monthly_savings.toLocaleString('en-IN');

    const elLifetimeSave = document.getElementById("calcResLifetimeSave");
    if (elLifetimeSave) elLifetimeSave.innerText = (data.lifetime_savings_inr / 100000).toFixed(1);

    const elCO2 = document.getElementById("calcResCO2");
    if (elCO2) elCO2.innerText = data.co2_saved_tonnes_per_year;

    const elTrees = document.getElementById("calcResTrees");
    if (elTrees) elTrees.innerText = data.trees_equivalent;

    // Cost Breakdown Table
    const elGrossCost = document.getElementById("calcResGrossCost");
    if (elGrossCost) elGrossCost.innerText = data.base_cost.toLocaleString('en-IN');

    const elGstRate = document.getElementById("calcResGstRate");
    if (elGstRate) elGstRate.innerText = `${data.gst_rate}%`;

    const elGst = document.getElementById("calcResGst");
    if (elGst) elGst.innerText = data.gst_amount.toLocaleString('en-IN');

    const elNetMeter = document.getElementById("calcResNetMeter");
    if (elNetMeter) elNetMeter.innerText = (data.net_meter_cost || 0).toLocaleString('en-IN');

    const elTransport = document.getElementById("calcResTransport");
    if (elTransport) elTransport.innerText = (data.transportation_cost || 0).toLocaleString('en-IN');

    const elTotalCost = document.getElementById("calcResTotalCost");
    if (elTotalCost) elTotalCost.innerText = data.total_cost.toLocaleString('en-IN');

    const elSubsidyDeduct = document.getElementById("calcResSubsidyDeduct");
    if (elSubsidyDeduct) elSubsidyDeduct.innerText = data.subsidy_eligible.toLocaleString('en-IN');

    const elNetCostFinal = document.getElementById("calcResNetCostFinal");
    if (elNetCostFinal) elNetCostFinal.innerText = data.net_cost.toLocaleString('en-IN');

  } catch (err) {
    console.error("Calculator error:", err);
  }
}

async function createQuotationFromCalc() {
  if (!lastCalcResult) await runLiveCalculator();
  if (!currentLeads.length) await loadLeads();

  const lead = currentLeads[0];
  if (!lead) {
    alert("Please add at least one customer lead first!");
    return;
  }

  const payload = {
    lead_id: lead.id,
    capacity_kw: lastCalcResult.capacity_kw,
    panel_make: "Waaree 550Wp Mono PERC Bifacial",
    panel_qty: lastCalcResult.panel_qty,
    inverter_make: lastCalcResult.inverter_spec,
    structure_type: "HDG Heavy Duty Rooftop (Wind 150 km/h)",
    bos_details: "Polycab 4sqmm DC Cable, Type-II SPD, Dual Chemical Earthing",
    system_cost: lastCalcResult.base_cost,
    gst_rate: lastCalcResult.gst_rate || 5.0,
    gst_amount: lastCalcResult.gst_amount,
    net_meter_cost: lastCalcResult.net_meter_cost || 0.0,
    transportation_cost: lastCalcResult.transportation_cost || 0.0,
    total_project_cost: lastCalcResult.total_cost,
    subsidy_eligible: lastCalcResult.subsidy_eligible,
    net_customer_cost: lastCalcResult.net_cost,
    daily_generation_kwh: lastCalcResult.units_per_day,
    monthly_generation_kwh: lastCalcResult.monthly_generation_kwh,
    monthly_savings: lastCalcResult.monthly_savings,
    payback_period_years: lastCalcResult.payback_years,
    status: "Draft"
  };

  try {
    const res = await fetch("/api/quotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (res.ok) {
      showToast(`Quotation ${result.quote_no} created successfully for ${lead.name}!`);
      switchTab("quotations");
    } else {
      showToast(result.detail || "Error creating quotation", "error");
    }
  } catch (err) {
    showToast("Error creating quotation", "error");
  }
}

async function createQuoteForLead(leadId) {
  const lead = currentLeads.find(l => l.id === leadId);
  if (!lead) return;

  document.getElementById("calcBillInput").value = lead.avg_monthly_bill;
  document.getElementById("calcLoadInput").value = lead.sanctioned_load;
  await runLiveCalculator();

  const payload = {
    lead_id: lead.id,
    capacity_kw: lastCalcResult.capacity_kw,
    panel_make: "Waaree 550Wp Mono PERC Bifacial",
    panel_qty: lastCalcResult.panel_qty,
    inverter_make: lastCalcResult.inverter_spec,
    structure_type: "HDG Heavy Duty Rooftop",
    bos_details: "Polycab 4sqmm UV DC Cable, Type-II SPD, Dual Earthing",
    system_cost: lastCalcResult.base_cost,
    gst_rate: lastCalcResult.gst_rate || 5.0,
    gst_amount: lastCalcResult.gst_amount,
    net_meter_cost: lastCalcResult.net_meter_cost || 0.0,
    transportation_cost: lastCalcResult.transportation_cost || 0.0,
    total_project_cost: lastCalcResult.total_cost,
    subsidy_eligible: lastCalcResult.subsidy_eligible,
    net_customer_cost: lastCalcResult.net_cost,
    daily_generation_kwh: lastCalcResult.units_per_day,
    monthly_generation_kwh: lastCalcResult.monthly_generation_kwh,
    monthly_savings: lastCalcResult.monthly_savings,
    payback_period_years: lastCalcResult.payback_years,
    status: "Draft"
  };

  try {
    const res = await fetch("/api/quotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (res.ok) {
      showToast(`Quotation ${result.quote_no} generated for ${lead.name}!`);
      switchTab("quotations");
    }
  } catch (err) {
    showToast("Error creating quote", "error");
  }
}

// ================= QUOTATIONS =================
async function loadQuotations() {
  try {
    const res = await fetch("/api/quotations");
    const quotes = await res.json();
    const tbody = document.getElementById("quotationsTableBody");
    tbody.innerHTML = "";

    quotes.forEach(q => {
      const additionalCost = (q.net_meter_cost || 0) + (q.transportation_cost || 0);
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      tr.innerHTML = `
        <td class="py-3 px-4">
          <div class="font-bold text-slate-800">${q.quote_no}</div>
          <div class="text-[10px] text-slate-400">${q.created_at ? q.created_at.slice(0, 10) : ''}</div>
        </td>
        <td class="py-3 px-4">
          <div class="font-bold text-slate-800">${q.customer_name}</div>
          <div class="text-[10px] text-slate-500">${q.discom} • Consumer: ${q.consumer_no}</div>
        </td>
        <td class="py-3 px-4">
          <div class="font-bold text-solar-700">${q.capacity_kw} kW System</div>
          <div class="text-[10px] text-slate-500">${q.panel_qty}x ${q.panel_make}</div>
        </td>
        <td class="py-3 px-4 font-semibold text-slate-700">₹${(q.system_cost || 0).toLocaleString('en-IN')}</td>
        <td class="py-3 px-4 font-semibold text-slate-600">₹${(q.gst_amount || 0).toLocaleString('en-IN')} <span class="text-[10px] text-slate-400">(${q.gst_rate || 5}%)</span></td>
        <td class="py-3 px-4 font-semibold text-slate-600">₹${additionalCost.toLocaleString('en-IN')}</td>
        <td class="py-3 px-4 font-bold text-amber-600">- ₹${(q.subsidy_eligible || 0).toLocaleString('en-IN')}</td>
        <td class="py-3 px-4 font-black text-emerald-700 text-sm">₹${(q.net_customer_cost || 0).toLocaleString('en-IN')}</td>
        <td class="py-3 px-4">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${
            q.status === 'Accepted' ? 'bg-emerald-100 text-emerald-800' : 
            q.status === 'Sent' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-700'
          }">${q.status || 'Draft'}</span>
        </td>
        <td class="py-3 px-4 text-right space-x-1 whitespace-nowrap">
          <a href="/api/pdf/quotation/${q.id}" target="_blank" title="Download Official Proposal PDF" class="inline-flex items-center space-x-1 px-2 py-1 bg-solar-700 hover:bg-solar-800 text-white rounded text-[11px] font-semibold transition">
            <i data-lucide="file-down" class="w-3.5 h-3.5"></i>
            <span>PDF</span>
          </a>
          <button onclick="sendQuotationWhatsApp(${q.id}, '${q.quote_no}', '${q.phone}', '${q.customer_name}', ${q.capacity_kw}, ${q.net_customer_cost})" title="Send Quotation on WhatsApp & Mark Sent" class="inline-flex items-center space-x-1 px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-semibold transition">
            <i data-lucide="send" class="w-3.5 h-3.5"></i>
            <span>WhatsApp</span>
          </button>
          ${q.status !== 'Accepted' ? `
            <button onclick="convertQuoteToProject(${q.id})" title="Confirm Order & Generate Proforma Invoice" class="inline-flex items-center space-x-1 px-2 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded text-[11px] font-semibold transition">
              <i data-lucide="check" class="w-3.5 h-3.5"></i>
              <span>Book Project</span>
            </button>
          ` : ''}
          <button onclick="deleteQuotation(${q.id}, '${q.quote_no}')" title="Delete Quotation" class="inline-flex items-center p-1 text-red-500 hover:bg-red-50 rounded transition">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading quotes:", err);
  }
}

async function sendQuotationWhatsApp(id, quoteNo, phone, customerName, capacityKw, netCost) {
  try {
    // 1. Mark as Sent in backend
    await fetch(`/api/quotations/${id}/send`, { method: "POST" });
    showToast(`Quotation ${quoteNo} marked as Sent!`);
    loadQuotations();

    // 2. Format phone number
    let cleanPhone = (phone || "").replace(/[^0-9]/g, "");
    if (cleanPhone.length === 10) {
      cleanPhone = "91" + cleanPhone;
    }

    const message = `Namaste ${customerName} Ji! Aapka Solar Rooftop Proposal (${capacityKw} kW System) taiyaar hai.\n\n` +
      `📄 Quotation Ref: ${quoteNo}\n` +
      `⚡ Capacity: ${capacityKw} kW Rooftop Solar\n` +
      `🏛️ PM Surya Ghar + Odisha Subsidy: ₹1,38,000 (DBT Credit)\n` +
      `💰 Net Customer Capex: ₹${Number(netCost).toLocaleString('en-IN')}\n\n` +
      `Official PDF Quotation aur site installation details ke liye please connect karein.\n` +
      `- ${companySettings.company_name || 'SuryaTech Clean Energy'}`;

    const waUrl = `https://api.whatsapp.com/send?phone=${cleanPhone}&text=${encodeURIComponent(message)}`;
    window.open(waUrl, "_blank");
  } catch (err) {
    showToast("Error sending on WhatsApp", "error");
  }
}

async function deleteQuotation(quoteId, quoteNo) {
  if (confirm(`Are you sure you want to delete quotation ${quoteNo}? This action cannot be undone.`)) {
    try {
      const res = await fetch(`/api/quotations/${quoteId}`, { method: "DELETE" });
      if (res.ok) {
        showToast(`Quotation ${quoteNo} deleted successfully.`);
        loadQuotations();
        loadDashboard();
      } else {
        showToast("Error deleting quotation", "error");
      }
    } catch (err) {
      showToast("Error deleting quotation", "error");
    }
  }
}

async function convertQuoteToProject(quoteId) {
  if (confirm("Book this quotation into an Active Solar Installation Project? (Generates Project Code & creates Advance Proforma Invoice)")) {
    try {
      const res = await fetch(`/api/quotations/${quoteId}/convert-to-project`, { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        showToast(`Project ${data.project_code} booked! Proforma Invoice ${data.invoice_no} created.`);
        switchTab("projects");
      } else {
        showToast(data.detail || "Error converting quotation to project", "error");
      }
    } catch (err) {
      showToast("Error converting to project", "error");
    }
  }
}

// ================= PROJECTS & INSTALLATION =================
const PROJECT_STAGES = [
  "Order Confirmed",
  "Site Survey",
  "DISCOM Application",
  "Feasibility Approved",
  "Material Dispatched",
  "Structure & Mounting",
  "Joint Inspection & Meter",
  "Commissioned"
];

async function loadProjects() {
  try {
    const res = await fetch("/api/projects");
    currentProjects = await res.json();
    const container = document.getElementById("projectsListContainer");
    container.innerHTML = "";

    currentProjects.forEach(p => {
      const card = document.createElement("div");
      card.className = "bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4";
      
      const currentStageIndex = PROJECT_STAGES.indexOf(p.stage);

      card.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-3 border-b border-slate-100">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-base font-extrabold text-slate-900">${p.project_code}</span>
              <span class="bg-solar-100 text-solar-800 text-xs px-2 py-0.5 rounded font-bold">${p.capacity_kw} kW Rooftop</span>
              <span class="bg-slate-100 text-slate-700 text-xs px-2 py-0.5 rounded font-mono">${p.discom}</span>
            </div>
            <div class="text-xs text-slate-500 mt-0.5">Customer: <b class="text-slate-800">${p.customer_name}</b> (${p.phone}) • Consumer No: <b class="font-mono text-slate-700">${p.consumer_no}</b></div>
          </div>
          <div class="text-right">
            <span class="text-xs text-slate-400">Order Value:</span>
            <div class="text-base font-bold text-slate-900">₹${p.contract_value.toLocaleString('en-IN')}</div>
          </div>
        </div>

        <!-- Visual Milestone Step Progress Bar -->
        <div class="space-y-1">
          <div class="flex justify-between text-[11px] font-semibold text-slate-600">
            <span>Current Stage: <b class="text-solar-700">${p.stage}</b></span>
            <span>Progress: <b class="text-solar-800">${p.progress_pct}%</b></span>
          </div>
          <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div class="bg-gradient-to-r from-solar-600 to-emerald-500 h-2 rounded-full transition-all duration-500" style="width: ${p.progress_pct}%"></div>
          </div>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600 pt-1">
          <div>Lead Engineer: <b class="text-slate-800">${p.project_manager}</b></div>
          <div>Target Sync Date: <b class="text-slate-800">${p.target_commissioning_date || 'In Progress'}</b></div>
          <div class="flex items-center space-x-2">
            ${currentStageIndex < PROJECT_STAGES.length - 1 ? `
              <button onclick="advanceProjectStage(${p.id}, ${currentStageIndex})" class="px-3 py-1 bg-solar-700 hover:bg-solar-800 text-white rounded text-xs font-semibold shadow-sm transition">
                Advance Stage →
              </button>
            ` : `
              <span class="px-2 py-1 bg-emerald-100 text-emerald-800 rounded font-bold text-xs flex items-center space-x-1">
                <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
                <span>Commissioned & Generating</span>
              </span>
            `}
          </div>
        </div>
      `;
      container.appendChild(card);
    });

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading projects:", err);
  }
}

async function advanceProjectStage(projectId, currentIndex) {
  const nextStage = PROJECT_STAGES[currentIndex + 1];
  const nextPct = Math.min(100, Math.round(((currentIndex + 2) / PROJECT_STAGES.length) * 100));

  try {
    const res = await fetch(`/api/projects/${projectId}/stage`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        stage: nextStage,
        progress_pct: nextPct,
        notes: `Advanced to ${nextStage}`
      })
    });
    if (res.ok) {
      showToast(`Project advanced to ${nextStage} (${nextPct}%)`);
      loadProjects();
      loadDashboard();
    }
  } catch (err) {
    showToast("Error updating project", "error");
  }
}

// ================= DISCOM & NET METERING =================
async function loadDiscom() {
  try {
    const res = await fetch("/api/discom");
    const apps = await res.json();
    const tbody = document.getElementById("discomTableBody");
    tbody.innerHTML = "";

    apps.forEach(d => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      tr.innerHTML = `
        <td class="py-3 px-4 font-mono font-bold text-slate-800">${d.application_ref_no}</td>
        <td class="py-3 px-4">
          <div class="font-bold text-slate-800">${d.customer_name}</div>
          <div class="text-[10px] text-slate-500">${d.project_code}</div>
        </td>
        <td class="py-3 px-4">
          <div class="font-bold text-solar-700">${d.discom_name}</div>
          <div class="text-[10px] text-slate-400">${d.division || 'Central'}</div>
        </td>
        <td class="py-3 px-4 font-mono text-slate-700">${d.consumer_no}</td>
        <td class="py-3 px-4 font-bold text-slate-800">${d.applied_capacity_kw} kW / ${d.sanctioned_load_kw} kW Load</td>
        <td class="py-3 px-4">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${
            d.feasibility_status === 'Commissioned' ? 'bg-emerald-100 text-emerald-800' :
            d.feasibility_status === 'Feasibility Approved' ? 'bg-blue-100 text-blue-800' :
            'bg-amber-100 text-amber-800'
          }">${d.feasibility_status}</span>
        </td>
        <td class="py-3 px-4 font-mono text-xs text-slate-600">${d.bi_directional_meter_no || 'Pending Sync'}</td>
        <td class="py-3 px-4">
          <div class="font-bold text-emerald-700">₹${d.subsidy_amount.toLocaleString('en-IN')}</div>
          <div class="text-[10px] text-slate-500">${d.subsidy_status}</div>
        </td>
        <td class="py-3 px-4 text-right">
          <button onclick="updateDiscomStatusPrompt(${d.id})" class="text-xs font-semibold text-solar-700 hover:underline">
            Update →
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading DISCOM:", err);
  }
}

async function updateDiscomStatusPrompt(id) {
  const newStatus = prompt("Update DISCOM Status (e.g. Feasibility Approved, Demand Note Paid, Meter Test Done, Net Meter Installed, Commissioned):", "Commissioned");
  if (newStatus) {
    const meterNo = prompt("Enter Bi-directional Net Meter Number (if installed):", "MTR-2026-9901");
    try {
      await fetch(`/api/discom/${id}?status=${encodeURIComponent(newStatus)}&meter_no=${encodeURIComponent(meterNo || '')}`, { method: "PUT" });
      showToast("DISCOM Status updated!");
      loadDiscom();
      loadDashboard();
    } catch (err) {
      showToast("Error updating DISCOM", "error");
    }
  }
}

// ================= INVOICING & BILLING =================
let currentInvoiceFilter = "All";

async function loadInvoices(categoryFilter = currentInvoiceFilter) {
  currentInvoiceFilter = categoryFilter;

  // Update Category Tab UI
  document.querySelectorAll(".inv-filter-btn").forEach(btn => {
    btn.className = "inv-filter-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition border border-slate-200";
  });
  if (categoryFilter === "All") {
    const el = document.getElementById("invTabAll");
    if (el) el.className = "inv-filter-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-solar-700 text-white shadow-sm transition";
  } else if (categoryFilter === "Proforma Invoice") {
    const el = document.getElementById("invTabProforma");
    if (el) el.className = "inv-filter-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-blue-700 text-white shadow-sm transition";
  } else if (categoryFilter === "Tax Invoice") {
    const el = document.getElementById("invTabTax");
    if (el) el.className = "inv-filter-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-emerald-700 text-white shadow-sm transition";
  }

  try {
    // 1. Fetch filtered list
    let url = `/api/invoices?invoice_type=${encodeURIComponent(categoryFilter)}`;
    const res = await fetch(url);
    const invoices = await res.json();

    // 2. Also fetch all invoices to update count badges and total invoiced sum
    const allRes = await fetch("/api/invoices?invoice_type=All");
    const allInvoices = await allRes.json();

    const countAll = allInvoices.length;
    const countProforma = allInvoices.filter(i => i.invoice_type === "Proforma Invoice").length;
    const countTax = allInvoices.filter(i => i.invoice_type === "Tax Invoice").length;
    const totalVal = allInvoices.reduce((acc, i) => acc + (i.total_amount || 0), 0);

    const elCountAll = document.getElementById("invCountAll");
    if (elCountAll) elCountAll.innerText = countAll;
    const elCountPro = document.getElementById("invCountProforma");
    if (elCountPro) elCountPro.innerText = countProforma;
    const elCountTax = document.getElementById("invCountTax");
    if (elCountTax) elCountTax.innerText = countTax;
    const elTotalVal = document.getElementById("invTotalValueText");
    if (elTotalVal) elTotalVal.innerText = `₹${totalVal.toLocaleString('en-IN')}`;

    const tbody = document.getElementById("invoicesTableBody");
    tbody.innerHTML = "";

    invoices.forEach(inv => {
      const isProforma = inv.invoice_type === "Proforma Invoice";
      const addCost = (inv.net_meter_cost || 0) + (inv.transportation_cost || 0);

      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      tr.innerHTML = `
        <td class="py-3 px-4">
          <div class="font-bold text-slate-800">${inv.invoice_no}</div>
          <div class="text-[10px] text-slate-400">${inv.invoice_date || ''}</div>
        </td>
        <td class="py-3 px-4">
          <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
            isProforma ? 'bg-blue-100 text-blue-800 border border-blue-200' : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
          }">
            ${isProforma ? '📄 Proforma' : '🧾 Tax Invoice'}
          </span>
        </td>
        <td class="py-3 px-4">
          <div class="font-bold text-slate-800">${inv.customer_name}</div>
          <div class="text-[10px] text-slate-500">${inv.project_code} • ${inv.capacity_kw} kW</div>
        </td>
        <td class="py-3 px-4 font-semibold text-slate-700">${inv.milestone_name}</td>
        <td class="py-3 px-4 text-slate-700">₹${(inv.base_amount || 0).toLocaleString('en-IN')}</td>
        <td class="py-3 px-4 text-slate-600">₹${(inv.gst_amount || 0).toLocaleString('en-IN')} <span class="text-[9px] text-slate-400">(${inv.gst_rate || 5}%)</span></td>
        <td class="py-3 px-4 text-slate-600">₹${addCost.toLocaleString('en-IN')}</td>
        <td class="py-3 px-4 font-extrabold text-slate-900 text-sm">₹${(inv.total_amount || 0).toLocaleString('en-IN')}</td>
        <td class="py-3 px-4 font-bold text-emerald-700">₹${(inv.paid_amount || 0).toLocaleString('en-IN')}</td>
        <td class="py-3 px-4">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${
            inv.status === 'Paid' ? 'bg-emerald-100 text-emerald-800' :
            inv.status === 'Partially Paid' ? 'bg-amber-100 text-amber-800' :
            'bg-red-100 text-red-800'
          }">${inv.status}</span>
        </td>
        <td class="py-3 px-4 text-right space-x-1 whitespace-nowrap">
          <a href="/api/pdf/invoice/${inv.id}" target="_blank" title="Download Printable PDF" class="inline-flex items-center space-x-1 px-2.5 py-1 bg-solar-700 hover:bg-solar-800 text-white rounded text-[11px] font-semibold transition">
            <i data-lucide="printer" class="w-3.5 h-3.5"></i>
            <span>PDF</span>
          </a>
          ${isProforma ? `
            <button onclick="convertToTaxInvoice(${inv.id}, '${inv.invoice_no}')" title="Convert Proforma to Official Tax Invoice" class="inline-flex items-center space-x-1 px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded text-[11px] font-semibold transition">
              <i data-lucide="file-check" class="w-3.5 h-3.5"></i>
              <span>To Tax Inv</span>
            </button>
          ` : ''}
          <button onclick="deleteInvoice(${inv.id}, '${inv.invoice_no}')" title="Delete Invoice" class="inline-flex items-center p-1 text-red-500 hover:bg-red-50 rounded transition">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading invoices:", err);
  }
}

function filterInvoicesByCategory(cat) {
  loadInvoices(cat);
}

async function convertToTaxInvoice(id, invNo) {
  if (confirm(`Convert Proforma Invoice ${invNo} into an official GST Tax Invoice? This will generate a formal Tax Invoice number (INV-2026-XXXX).`)) {
    try {
      const res = await fetch(`/api/invoices/${id}/convert-to-tax-invoice`, { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        showToast(`Converted to Tax Invoice ${data.new_invoice_no} successfully!`);
        loadInvoices();
        loadDashboard();
      } else {
        showToast(data.detail || "Error converting invoice", "error");
      }
    } catch (err) {
      showToast("Error converting invoice", "error");
    }
  }
}

async function deleteInvoice(id, invNo) {
  if (confirm(`Are you sure you want to delete invoice ${invNo}? This action cannot be undone.`)) {
    try {
      const res = await fetch(`/api/invoices/${id}`, { method: "DELETE" });
      if (res.ok) {
        showToast(`Invoice ${invNo} deleted.`);
        loadInvoices();
        loadDashboard();
      } else {
        showToast("Error deleting invoice", "error");
      }
    } catch (err) {
      showToast("Error deleting invoice", "error");
    }
  }
}

async function openInvoiceModal() {
  if (!currentProjects.length) await loadProjects();
  const sel = document.getElementById("invProjectId");
  sel.innerHTML = "";

  currentProjects.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.innerText = `${p.project_code} - ${p.customer_name} (${p.capacity_kw} kW - ₹${(p.contract_value || 0).toLocaleString('en-IN')})`;
    sel.appendChild(opt);
  });

  const today = new Date().toISOString().slice(0, 10);
  document.getElementById("invDate").value = today;
  document.getElementById("invMilestone").value = "Material Dispatch Payment (70%)";
  document.getElementById("invBaseAmount").value = 75000;
  document.getElementById("invGstRate").value = 5.0;
  document.getElementById("invNetMeterCost").value = 0;
  document.getElementById("invTransportCost").value = 0;
  document.getElementById("invNotes").value = "Turnkey Solar Installation Invoice";
  recalcInvoiceModalTotals();

  openModal("invoiceModal");
}

function recalcInvoiceModalTotals() {
  const base = parseFloat(document.getElementById("invBaseAmount")?.value) || 0;
  const gstRate = parseFloat(document.getElementById("invGstRate")?.value) || 0;
  const netMeter = parseFloat(document.getElementById("invNetMeterCost")?.value) || 0;
  const transport = parseFloat(document.getElementById("invTransportCost")?.value) || 0;

  const gstAmt = Math.round(base * (gstRate / 100.0));
  const total = base + gstAmt + netMeter + transport;

  const el = document.getElementById("invModalTotalDisplay");
  if (el) el.innerText = total.toLocaleString('en-IN');
}

function onInvoiceProjectSelect(projId) {
  const proj = currentProjects.find(p => p.id === parseInt(projId));
  if (proj) {
    const defaultBase = Math.round((proj.contract_value || 100000) * 0.70);
    document.getElementById("invBaseAmount").value = defaultBase;
    recalcInvoiceModalTotals();
  }
}

async function handleInvoiceSubmit(e) {
  e.preventDefault();
  const projId = parseInt(document.getElementById("invProjectId").value);
  const proj = currentProjects.find(p => p.id === projId);

  const base = parseFloat(document.getElementById("invBaseAmount").value) || 0;
  const gstRate = parseFloat(document.getElementById("invGstRate").value) || 5.0;
  const netMeter = parseFloat(document.getElementById("invNetMeterCost").value) || 0;
  const transport = parseFloat(document.getElementById("invTransportCost").value) || 0;

  const gstAmt = Math.round(base * (gstRate / 100.0));
  const total = base + gstAmt + netMeter + transport;

  const payload = {
    project_id: projId,
    lead_id: proj ? proj.lead_id : null,
    invoice_type: document.getElementById("invTypeSelect").value,
    milestone_name: document.getElementById("invMilestone").value,
    base_amount: base,
    gst_rate: gstRate,
    gst_amount: gstAmt,
    net_meter_cost: netMeter,
    transportation_cost: transport,
    total_amount: total,
    invoice_date: document.getElementById("invDate").value,
    due_date: document.getElementById("invDueDate").value || null,
    status: "Unpaid",
    notes: document.getElementById("invNotes").value
  };

  try {
    const res = await fetch("/api/invoices", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (res.ok) {
      closeModal("invoiceModal");
      showToast(`${payload.invoice_type} ${result.invoice_no} created successfully!`);
      loadInvoices();
      loadDashboard();
    } else {
      showToast(result.detail || "Error generating invoice", "error");
    }
  } catch (err) {
    showToast("Error saving invoice", "error");
  }
}

// ================= PAYMENTS & FINANCIAL LEDGER =================
let currentPaymentFilter = "All";

async function loadPayments(typeFilter = currentPaymentFilter) {
  currentPaymentFilter = typeFilter;

  // Update category tab button UI
  document.querySelectorAll(".pay-filter-btn").forEach(btn => {
    btn.className = "pay-filter-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition border border-slate-200";
  });
  if (typeFilter === "All") {
    const el = document.getElementById("payTabAll");
    if (el) el.className = "pay-filter-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-solar-700 text-white shadow-sm transition";
  } else if (typeFilter === "Payment In") {
    const el = document.getElementById("payTabIn");
    if (el) el.className = "pay-filter-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-emerald-700 text-white shadow-sm transition";
  } else if (typeFilter === "Payment Out") {
    const el = document.getElementById("payTabOut");
    if (el) el.className = "pay-filter-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-amber-600 text-white shadow-sm transition";
  } else if (typeFilter === "Project Expense") {
    const el = document.getElementById("payTabExp");
    if (el) el.className = "pay-filter-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-purple-700 text-white shadow-sm transition";
  }

  try {
    // 1. Fetch Summary for 4 KPI Cards
    const summaryRes = await fetch("/api/payments/summary");
    const summary = await summaryRes.json();

    const elIn = document.getElementById("kpiPaymentIn");
    if (elIn) elIn.innerText = (summary.total_in || 0).toLocaleString('en-IN');

    const elOut = document.getElementById("kpiPaymentOut");
    if (elOut) elOut.innerText = (summary.total_out || 0).toLocaleString('en-IN');

    const elExp = document.getElementById("kpiPaymentExpenses");
    if (elExp) elExp.innerText = (summary.total_expenses || 0).toLocaleString('en-IN');

    const elNet = document.getElementById("kpiNetCashflow");
    if (elNet) elNet.innerText = (summary.net_cashflow || 0).toLocaleString('en-IN');

    // 2. Fetch all payments to update counts
    const allRes = await fetch("/api/payments?transaction_type=All");
    const allPayments = await allRes.json();

    const countAll = allPayments.length;
    const countIn = allPayments.filter(p => p.transaction_type === "Payment In").length;
    const countOut = allPayments.filter(p => p.transaction_type === "Payment Out").length;
    const countExp = allPayments.filter(p => p.transaction_type === "Project Expense").length;

    const elCountAll = document.getElementById("payCountAll");
    if (elCountAll) elCountAll.innerText = countAll;
    const elCountIn = document.getElementById("payCountIn");
    if (elCountIn) elCountIn.innerText = countIn;
    const elCountOut = document.getElementById("payCountOut");
    if (elCountOut) elCountOut.innerText = countOut;
    const elCountExp = document.getElementById("payCountExp");
    if (elCountExp) elCountExp.innerText = countExp;

    // 3. Fetch filtered list
    let url = `/api/payments?transaction_type=${encodeURIComponent(typeFilter)}`;
    const res = await fetch(url);
    const payments = await res.json();

    const elFilterCount = document.getElementById("payFilteredCountText");
    if (elFilterCount) elFilterCount.innerText = payments.length;

    const tbody = document.getElementById("paymentsTableBody");
    tbody.innerHTML = "";

    payments.forEach(p => {
      const isPaymentIn = p.transaction_type === "Payment In";
      const isPaymentOut = p.transaction_type === "Payment Out";
      const isExpense = p.transaction_type === "Project Expense";

      let typeBadge = `<span class="bg-emerald-100 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-full text-[10px] font-bold">📥 Payment In</span>`;
      let amountClass = "font-black text-emerald-700 text-sm";
      let amountSign = "+";

      if (isPaymentOut) {
        typeBadge = `<span class="bg-amber-100 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full text-[10px] font-bold">📤 Payment Out</span>`;
        amountClass = "font-bold text-amber-700 text-sm";
        amountSign = "-";
      } else if (isExpense) {
        typeBadge = `<span class="bg-purple-100 text-purple-800 border border-purple-200 px-2 py-0.5 rounded-full text-[10px] font-bold">🏗️ Site Expense</span>`;
        amountClass = "font-bold text-purple-700 text-sm";
        amountSign = "-";
      }

      const partyDisplay = p.display_party || p.party_name || p.customer_name || 'Direct';

      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      tr.innerHTML = `
        <td class="py-3 px-4 font-mono font-bold text-slate-800">${p.receipt_no}</td>
        <td class="py-3 px-4">${typeBadge}</td>
        <td class="py-3 px-4 font-bold text-slate-800">${partyDisplay}</td>
        <td class="py-3 px-4 text-slate-600 font-medium">${p.category || 'General'}</td>
        <td class="py-3 px-4 font-mono text-solar-700">${p.project_code || 'General'}</td>
        <td class="py-3 px-4 ${amountClass}">${amountSign}₹${(p.amount || 0).toLocaleString('en-IN')}</td>
        <td class="py-3 px-4 text-slate-600">${p.payment_date || ''}</td>
        <td class="py-3 px-4"><span class="bg-slate-100 px-2 py-0.5 rounded text-[10px] font-semibold">${p.payment_mode}</span></td>
        <td class="py-3 px-4 font-mono text-xs text-slate-500">${p.reference_no || '-'}</td>
        <td class="py-3 px-4 text-right">
          <button onclick="deletePayment(${p.id}, '${p.receipt_no}')" title="Delete Transaction" class="p-1 text-red-500 hover:bg-red-50 rounded transition">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading payments:", err);
  }
}

function filterPaymentsByType(type) {
  loadPayments(type);
}

async function deletePayment(id, receiptNo) {
  if (confirm(`Are you sure you want to delete transaction ${receiptNo}? This action cannot be undone.`)) {
    try {
      const res = await fetch(`/api/payments/${id}`, { method: "DELETE" });
      if (res.ok) {
        showToast(`Transaction ${receiptNo} deleted.`);
        loadPayments();
        loadDashboard();
      } else {
        showToast("Error deleting transaction", "error");
      }
    } catch (err) {
      showToast("Error deleting transaction", "error");
    }
  }
}

async function openPaymentModal() {
  if (!currentProjects.length) await loadProjects();
  const sel = document.getElementById("payProjectId");
  sel.innerHTML = `<option value="">-- General / Non-Project --</option>`;

  currentProjects.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.innerText = `${p.project_code} - ${p.customer_name} (₹${(p.contract_value || 0).toLocaleString('en-IN')})`;
    sel.appendChild(opt);
  });

  document.getElementById("payDate").value = new Date().toISOString().slice(0, 10);
  document.getElementById("payAmount").value = "";
  document.getElementById("payPartyName").value = "";
  document.getElementById("payRefNo").value = "";
  document.getElementById("payRemarks").value = "";
  togglePaymentTypeFields(document.getElementById("payTransType").value);

  openModal("paymentModal");
}

function togglePaymentTypeFields(type) {
  const lbl = document.getElementById("lblPartyName");
  const catSel = document.getElementById("payCategory");
  catSel.innerHTML = "";

  if (type === "Payment In") {
    if (lbl) lbl.innerText = "Customer / Client Name *";
    document.getElementById("payPartyName").placeholder = "e.g. Subrat Jena / Pradeep Mishra";
    catSel.innerHTML = `
      <option value="Customer Advance">Customer Advance Booking (15%)</option>
      <option value="Material Dispatch Stage">Material Dispatch Payment (70%)</option>
      <option value="Final Settlement">Final Commissioning Settlement (15%)</option>
      <option value="Govt Subsidy DBT">PM Surya Ghar Central / State Subsidy Credit</option>
      <option value="Other Collection">Other Customer Receipt</option>
    `;
  } else if (type === "Payment Out") {
    if (lbl) lbl.innerText = "Supplier / Vendor Party Name *";
    document.getElementById("payPartyName").placeholder = "e.g. Waaree Energies Ltd / Growatt India";
    catSel.innerHTML = `
      <option value="Solar Panels">Solar PV Modules (Waaree/Adani/Tata/Saatvik)</option>
      <option value="Solar Inverter">Solar On-Grid Inverter (Growatt/Sungrow/Havells)</option>
      <option value="Mounting Structure">HDG Structure & Civil Hardware</option>
      <option value="AC/DC Cables & BOS">DC Cables, MC4, SPD, Earthing Chemical</option>
      <option value="Supplier Advance">Vendor Advance Token</option>
      <option value="Supplier Settlement">Vendor Final Invoice Settlement</option>
    `;
  } else {
    if (lbl) lbl.innerText = "Service Provider / Site Hand *";
    document.getElementById("payPartyName").placeholder = "e.g. Sagar Logistics / TPCODL Inspection";
    catSel.innerHTML = `
      <option value="Net Meter Cost">Net Meter Supply & Testing Fee (DISCOM)</option>
      <option value="Transportation & Freight">Truck Freight & Site Logistics</option>
      <option value="Crane & Unloading">Hydra Crane & High-Rise Lifting</option>
      <option value="Installation Labor">Installation, Mechanical & Wiring Labor</option>
      <option value="Site Survey & Feasibility">Survey & Shadow Analysis Expense</option>
      <option value="Misc Site Expense">Miscellaneous Site Hardware & Consumables</option>
    `;
  }
}

async function handlePaymentSubmit(e) {
  e.preventDefault();
  const rawProjId = document.getElementById("payProjectId").value;
  const projectId = rawProjId ? parseInt(rawProjId) : null;
  const project = projectId ? currentProjects.find(p => p.id === projectId) : null;

  const transType = document.getElementById("payTransType").value;
  const partyName = document.getElementById("payPartyName").value;
  const category = document.getElementById("payCategory").value;
  const amount = parseFloat(document.getElementById("payAmount").value);
  const mode = document.getElementById("payMode").value;
  const payDate = document.getElementById("payDate").value;
  const refNo = document.getElementById("payRefNo").value;
  const remarks = document.getElementById("payRemarks").value;

  const payload = {
    project_id: projectId,
    lead_id: project ? project.lead_id : null,
    transaction_type: transType,
    party_name: partyName,
    category: category,
    amount: amount,
    payment_mode: mode,
    payment_date: payDate,
    reference_no: refNo,
    remarks: remarks || `${transType} - ${category}`
  };

  try {
    const res = await fetch("/api/payments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (res.ok) {
      closeModal("paymentModal");
      showToast(`${transType} ${result.receipt_no} recorded successfully!`);
      loadPayments();
      loadDashboard();
    } else {
      showToast(result.detail || "Error saving payment", "error");
    }
  } catch (err) {
    showToast("Error saving payment", "error");
  }
}

// ================= GLOBAL SEARCH =================
function setupGlobalSearch() {
  const input = document.getElementById("globalSearchInput");
  input.addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase().trim();
    if (!term) return;

    // Search across leads
    const matchLead = currentLeads.find(l => 
      l.name.toLowerCase().includes(term) ||
      l.phone.includes(term) ||
      (l.consumer_no && l.consumer_no.toLowerCase().includes(term))
    );

    if (matchLead) {
      switchTab("leads");
      document.getElementById("leadStatusFilter").value = "All";
      return;
    }

    // Search across projects
    const matchProject = currentProjects.find(p =>
      p.project_code.toLowerCase().includes(term) ||
      p.customer_name.toLowerCase().includes(term) ||
      (p.consumer_no && p.consumer_no.toLowerCase().includes(term))
    );

    if (matchProject) {
      switchTab("projects");
      return;
    }
  });
}

// ================= 12. SOFTWARE UPDATES & AUTO-DEPLOYMENT =================
let updateCheckResult = null;
let updatePollInterval = null;

function loadUpdatesTab() {
  if (!updateCheckResult) {
    checkUpdates(false);
  }
}

async function checkUpdates(manual = false) {
  const btn = document.getElementById("btnManualCheck");
  const icon = document.getElementById("checkSpinnerIcon");
  
  if (manual && icon) {
    icon.classList.add("animate-spin");
    if (btn) btn.disabled = true;
  }

  try {
    const res = await fetch("/api/update/check");
    const data = await res.json();
    updateCheckResult = data;

    // Update current version
    const curVerEl = document.getElementById("currentVerDisplay");
    if (curVerEl && data.current_version) {
      curVerEl.innerText = data.current_version;
    }

    // Update last checked time
    const lastCheckedEl = document.getElementById("lastCheckedTime");
    if (lastCheckedEl) {
      const now = new Date();
      lastCheckedEl.innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    const headerBtn = document.getElementById("headerUpdateBtn");
    const navBadge = document.getElementById("updateNavBadge");
    const upToDateCard = document.getElementById("upToDateCard");
    const updateAvailCard = document.getElementById("updateAvailableCard");

    if (data.update_available) {
      // Unhide update badge and notification button
      if (headerBtn) headerBtn.classList.remove("hidden");
      if (navBadge) navBadge.classList.remove("hidden");

      // Show update card, hide up to date card
      if (upToDateCard) upToDateCard.classList.add("hidden");
      if (updateAvailCard) updateAvailCard.classList.remove("hidden");

      // Populate details
      const latestVerEl = document.getElementById("latestVerDisplay");
      if (latestVerEl) latestVerEl.innerText = `v${data.latest_version}`;

      const relDateEl = document.getElementById("releaseDateDisplay");
      if (relDateEl && data.release_date) relDateEl.innerText = data.release_date;

      const notesList = document.getElementById("releaseNotesList");
      if (notesList && data.release_notes && Array.isArray(data.release_notes)) {
        notesList.innerHTML = data.release_notes.map(item => `<li>${item}</li>`).join("");
      }

      if (manual) {
        showToast(`🚀 New Version v${data.latest_version} Available!`, "info");
      }
    } else {
      // Up to date
      if (headerBtn) headerBtn.classList.add("hidden");
      if (navBadge) navBadge.classList.add("hidden");

      if (upToDateCard) upToDateCard.classList.remove("hidden");
      if (updateAvailCard) updateAvailCard.classList.add("hidden");

      if (manual) {
        showToast(`SolarPulse ERP is completely up to date (v${data.current_version})!`, "success");
      }
    }
  } catch (err) {
    console.error("Failed to check updates:", err);
    if (manual) {
      showToast("Cloud update check failed: Network timeout or offline.", "error");
    }
  } finally {
    if (manual && icon) {
      icon.classList.remove("animate-spin");
      if (btn) btn.disabled = false;
    }
    lucide.createIcons();
  }
}

async function startAutoUpdate() {
  if (!updateCheckResult || !updateCheckResult.download_url) {
    showToast("Update manifest not loaded. Please click Check for Updates first.", "error");
    return;
  }

  const btnStart = document.getElementById("btnStartUpdate");
  const progressBox = document.getElementById("downloadProgressBox");
  const readyBox = document.getElementById("readyToInstallBox");

  if (btnStart) btnStart.classList.add("hidden");
  if (readyBox) readyBox.classList.add("hidden");
  if (progressBox) progressBox.classList.remove("hidden");

  try {
    const res = await fetch("/api/update/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        download_url: updateCheckResult.download_url,
        version: updateCheckResult.latest_version
      })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Download failed to initiate");
    }

    showToast("Download started in background...", "info");

    // Start progress polling
    if (updatePollInterval) clearInterval(updatePollInterval);
    updatePollInterval = setInterval(pollDownloadProgress, 500);

  } catch (err) {
    console.error("Start update error:", err);
    showToast("Failed to start download: " + err.message, "error");
    if (btnStart) btnStart.classList.remove("hidden");
    if (progressBox) progressBox.classList.add("hidden");
  }
}

async function pollDownloadProgress() {
  try {
    const res = await fetch("/api/update/progress");
    const info = await res.json();

    const bar = document.getElementById("downloadProgressBar");
    const pct = document.getElementById("downloadPctText");
    const mbText = document.getElementById("downloadMbText");
    const totalMbText = document.getElementById("downloadTotalMbText");
    const speedText = document.getElementById("downloadSpeedText");
    const statusLabel = document.getElementById("downloadStatusLabel");

    const percent = Math.min(100, Math.max(0, Math.round(info.progress || 0)));

    if (bar) bar.style.width = `${percent}%`;
    if (pct) pct.innerText = `${percent}%`;

    const downloadedMb = (info.downloaded_bytes / (1024 * 1024)).toFixed(1);
    const totalMb = info.total_bytes > 0 ? (info.total_bytes / (1024 * 1024)).toFixed(1) : "--";

    if (mbText) mbText.innerText = `${downloadedMb} MB`;
    if (totalMbText) totalMbText.innerText = `${totalMb} MB`;
    if (speedText) speedText.innerText = `${(info.speed_mbps || 0).toFixed(2)} MB/s`;

    if (info.status === "completed") {
      clearInterval(updatePollInterval);
      updatePollInterval = null;

      if (statusLabel) statusLabel.innerText = "Package downloaded & verified!";
      const progressBox = document.getElementById("downloadProgressBox");
      const readyBox = document.getElementById("readyToInstallBox");

      if (progressBox) progressBox.classList.add("hidden");
      if (readyBox) readyBox.classList.remove("hidden");
      lucide.createIcons();

      showToast("✅ Update Package Download Complete! Ready to install.", "success");
    } else if (info.status === "failed") {
      clearInterval(updatePollInterval);
      updatePollInterval = null;

      showToast("Download failed: " + (info.error || "Connection terminated"), "error");
      const btnStart = document.getElementById("btnStartUpdate");
      const progressBox = document.getElementById("downloadProgressBox");
      if (btnStart) btnStart.classList.remove("hidden");
      if (progressBox) progressBox.classList.add("hidden");
    }
  } catch (err) {
    console.error("Progress poll error:", err);
  }
}

async function executeInstall(silent = true) {
  const confirmMsg = silent 
    ? "Are you ready to run 1-Click Express Update?\n\nThe software will automatically close, apply updates, and relaunch within seconds."
    : "Launch Standard Setup Wizard?\n\nThe setup installer will open on your desktop to guide you through updating.";
  
  if (!confirm(confirmMsg)) return;

  // Show installation full-screen overlay
  let overlay = document.getElementById("installOverlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "installOverlay";
    overlay.className = "fixed inset-0 bg-slate-950/95 backdrop-blur-md z-[9999] flex flex-col items-center justify-center p-6 text-center text-white space-y-4 animate-fade-in";
    document.body.appendChild(overlay);
  }

  overlay.innerHTML = `
    <div class="w-16 h-16 rounded-2xl bg-solar-600 flex items-center justify-center shadow-2xl animate-pulse">
      <svg class="w-8 h-8 text-white animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
      </svg>
    </div>
    <div class="space-y-1">
      <h2 class="text-2xl font-black tracking-tight text-white">${silent ? "Applying Express Update..." : "Opening Setup Wizard..."}</h2>
      <p class="text-sm text-slate-400" id="installStatusText">${silent ? "Executing silent update in background. Old version is closing..." : "Launching setup window on your desktop..."}</p>
      <p class="text-xs text-amber-400 font-semibold pt-2" id="reconnectTimerText">${silent ? "SolarPulse ERP will restart automatically in ~10 seconds." : "Please follow the setup steps in the installer window."}</p>
      ${!silent ? '<button onclick="document.getElementById(\'installOverlay\').remove()" class="mt-4 bg-slate-800 hover:bg-slate-700 text-xs text-white px-4 py-2 rounded-lg border border-slate-700">Dismiss Overlay</button>' : ''}
    </div>
  `;

  try {
    const res = await fetch("/api/update/install", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ silent: silent })
    });
    const data = await res.json();
    
    if (!res.ok || data.status === "error") {
      overlay.remove();
      showToast(data.message || "Failed to launch installer", "error");
      return;
    }

    if (silent) {
      // Countdown and auto-reconnect
      let countdown = 12;
      const timerEl = document.getElementById("reconnectTimerText");
      const interval = setInterval(() => {
        countdown--;
        if (timerEl) timerEl.innerText = `Reconnecting to updated SolarPulse ERP in ${countdown}s...`;
        if (countdown <= 0) {
          clearInterval(interval);
          window.location.reload();
        }
      }, 1000);
    } else {
      setTimeout(() => {
        if (overlay) overlay.remove();
      }, 4000);
    }

  } catch (err) {
    console.error("Install request sent/failed:", err);
    // If the server shut down to apply updates, connection drops as expected
    if (silent) {
      let countdown = 8;
      const timerEl = document.getElementById("reconnectTimerText");
      const interval = setInterval(() => {
        countdown--;
        if (timerEl) timerEl.innerText = `Applying updates. Reconnecting in ${countdown}s...`;
        if (countdown <= 0) {
          clearInterval(interval);
          window.location.reload();
        }
      }, 1000);
    } else {
      if (overlay) overlay.remove();
    }
  }
}

