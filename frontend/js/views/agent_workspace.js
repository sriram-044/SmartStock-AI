// ==============================================================================
// StockMind AI: Goal-Driven Agentic AI Workspace
// Multi-Agent Orchestration, Live Activity Timeline, & Human Approval Center
// ==============================================================================

const AgentWorkspaceView = {
  currentTask: null,
  recentTasks: [],
  pollingInterval: null,

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem;">
        <div>
          <div style="font-size: 0.85rem; font-weight: 700; color: #4338CA; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem;">
            <span class="pulse-dot"></span> Goal-Driven Multi-Agent System &bull; Human-In-The-Loop Governance
          </div>
          <h2 style="font-size: 1.6rem; font-weight: 900; color: var(--text-primary); letter-spacing: -0.02em;">
            Agentic AI Command Center
          </h2>
          <p style="color: var(--text-secondary); font-size: 0.875rem;">
            Autonomous Goal Interpretation &rarr; Planning &rarr; Tool Execution &rarr; Supplier Evaluation &rarr; Human Approval Gate
          </p>
        </div>
        <div style="display: flex; gap: 0.75rem; align-items: center;">
          <button class="btn btn-secondary" id="btn-refresh-tasks">
            <span>🔄</span> Refresh Tasks
          </button>
        </div>
      </div>

      <!-- ACTIVE MULTI-AGENT SWARM BADGES -->
      <div class="glass-card" style="padding: 1rem 1.25rem; margin-bottom: 1.5rem; background: linear-gradient(135deg, #EEF2FF 0%, #FFFFFF 100%); border-left: 4px solid #4F46E5;">
        <div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #4F46E5; margin-bottom: 0.5rem;">
          Active Agent Swarm
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.6rem;">
          <span class="agent-badge active"><strong>SupervisorAgent</strong> (Coordinator)</span>
          <span class="agent-badge"><strong>InventoryAgent</strong> (Runout & Stockout)</span>
          <span class="agent-badge"><strong>ForecastingAgent</strong> (ML Multi-Model)</span>
          <span class="agent-badge"><strong>SupplierAgent</strong> (Lead Time & MOQ)</span>
          <span class="agent-badge"><strong>ExpiryAgent</strong> (FEFO Shelf-Life)</span>
          <span class="agent-badge"><strong>ProcurementAgent</strong> (Budget & Draft PO)</span>
          <span class="agent-badge"><strong>BusinessAnalyst</strong> (Margins & Health)</span>
        </div>
      </div>

      <!-- AGENT COMMAND CENTER: GOAL SUBMISSION -->
      <div class="glass-card" style="margin-bottom: 1.5rem;">
        <h3 style="font-size: 1.15rem; font-weight: 800; margin-bottom: 0.75rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
          <span>🎯</span> Define Business Objective
        </h3>
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem;">
          Describe your objective in natural language. The Supervisor Agent will interpret constraints, schedule specialized agents, execute verified tools, and propose an actionable procurement plan.
        </p>

        <!-- Quick Goal Presets Chips -->
        <div style="margin-bottom: 1rem; display: flex; flex-wrap: wrap; gap: 0.5rem;">
          <button type="button" class="btn btn-sm btn-outline goal-chip" data-goal="Prepare my shop for the next seven days. Prevent stockouts, avoid products expiring before sale, select reliable suppliers, and keep purchasing costs within ₹15,000.">
            🌾 7-Day Stockout & Budget Restock (₹15k)
          </button>
          <button type="button" class="btn btn-sm btn-outline goal-chip" data-goal="Find products likely to run out within three days and prepare an urgent replenishment plan.">
            🚨 3-Day Emergency Restock
          </button>
          <button type="button" class="btn btn-sm btn-outline goal-chip" data-goal="Restock the products that will run out before preferred suppliers can deliver, keeping budget under ₹10,000.">
            🚚 Supplier Lead-Time Constrained Plan
          </button>
          <button type="button" class="btn btn-sm btn-outline goal-chip" data-goal="Identify products likely to expire before they sell and suggest safe markdown and inventory rotation actions.">
            ⏳ Expiry Prevention & Markdown Audit
          </button>
          <button type="button" class="btn btn-sm btn-outline goal-chip" data-goal="Analyze slow-moving and dead stock, and calculate total blocked capital for recovery.">
            💰 Blocked Capital Recovery Audit
          </button>
        </div>

        <form id="agent-goal-form">
          <div style="margin-bottom: 1rem;">
            <textarea id="agent-objective-input" class="form-control" rows="3" placeholder="e.g. Prepare my shop for the next seven days. Prevent stockouts, avoid expiring items, and keep purchasing under ₹15,000..." style="font-size: 0.95rem; line-height: 1.5; resize: vertical;" required></textarea>
          </div>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.25rem;">
            <div>
              <label style="font-size: 0.8rem; font-weight: 700; color: var(--text-secondary); display: block; margin-bottom: 0.35rem;">
                Budget Ceiling (₹ Optional)
              </label>
              <input type="number" id="agent-budget-input" class="form-control" placeholder="e.g. 15000" min="0" step="100" />
            </div>
            <div>
              <label style="font-size: 0.8rem; font-weight: 700; color: var(--text-secondary); display: block; margin-bottom: 0.35rem;">
                Planning Horizon (Days)
              </label>
              <select id="agent-horizon-input" class="form-control">
                <option value="3">3 Days (Urgent)</option>
                <option value="7" selected>7 Days (Weekly Cycle)</option>
                <option value="14">14 Days (Bi-weekly)</option>
                <option value="30">30 Days (Monthly)</option>
              </select>
            </div>
          </div>
          <div style="display: flex; justify-content: flex-end;">
            <button type="submit" class="btn btn-ai" id="btn-submit-goal" style="padding: 0.75rem 1.75rem; font-size: 0.95rem;">
              <span>⚡</span> Dispatch Agent Swarm &rarr;
            </button>
          </div>
        </form>
      </div>

      <!-- CURRENT TASK EXECUTION DETAILS -->
      <div id="current-task-container" style="display: none; margin-bottom: 2rem;">
        <!-- Dynamically rendered when task is active or loaded -->
      </div>

      <!-- RECENT TASKS HISTORY TABLE -->
      <div class="glass-card">
        <h3 style="font-size: 1.15rem; font-weight: 800; margin-bottom: 1rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
          <span>📋</span> Agent Task Execution History
        </h3>
        <div id="tasks-history-table-container">
          <p style="color: var(--text-muted); font-size: 0.85rem;">Loading past agent tasks...</p>
        </div>
      </div>
    `;

    this.bindEvents();
    await this.loadRecentTasks();
  },

  bindEvents() {
    // Goal chips
    document.querySelectorAll('.goal-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        const goal = btn.getAttribute('data-goal');
        const input = document.getElementById('agent-objective-input');
        if (input) {
          input.value = goal;
          input.focus();
        }
      });
    });

    // Form submit
    const form = document.getElementById('agent-goal-form');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleGoalSubmit();
      });
    }

    // Refresh tasks
    const refreshBtn = document.getElementById('btn-refresh-tasks');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.loadRecentTasks());
    }
  },

  async handleGoalSubmit() {
    const objectiveInput = document.getElementById('agent-objective-input');
    const budgetInput = document.getElementById('agent-budget-input');
    const horizonInput = document.getElementById('agent-horizon-input');
    const submitBtn = document.getElementById('btn-submit-goal');

    const objective = objectiveInput.value.trim();
    if (!objective) return;

    const constraints = {};
    if (budgetInput && budgetInput.value) {
      constraints.budget_limit_inr = parseFloat(budgetInput.value);
    }
    if (horizonInput) {
      constraints.days_horizon = parseInt(horizonInput.value);
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>⏳</span> Planning & Executing Agents...';

    try {
      const task = await API.post('/api/agent/tasks', {
        objective,
        constraints
      });

      showToast(`Agent task ${task.id} started!`, 'success');
      this.currentTask = task;
      this.renderCurrentTask(task);
      await this.loadRecentTasks();

      // Scroll to current task
      const taskEl = document.getElementById('current-task-container');
      if (taskEl) taskEl.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      showToast(err.message || 'Failed to dispatch agent task', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<span>⚡</span> Dispatch Agent Swarm &rarr;';
    }
  },

  async loadRecentTasks() {
    const container = document.getElementById('tasks-history-table-container');
    if (!container) return;

    try {
      const tasks = await API.get('/api/agent/tasks');
      this.recentTasks = tasks;

      if (!tasks || tasks.length === 0) {
        container.innerHTML = `
          <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
            <p>No agent tasks executed yet. Submit an objective above to trigger the multi-agent system.</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div style="overflow-x: auto;">
          <table class="data-table" style="width: 100%;">
            <thead>
              <tr>
                <th>Task ID</th>
                <th>Objective</th>
                <th>Status</th>
                <th>Steps</th>
                <th>Approval</th>
                <th>Created At</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${tasks.map(t => `
                <tr>
                  <td><code>${t.id}</code></td>
                  <td style="max-width: 320px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${t.objective}">
                    <strong>${t.objective}</strong>
                  </td>
                  <td>${this.renderStatusBadge(t.status)}</td>
                  <td><span class="badge" style="background: #EEF2FF; color: #4338CA;">${t.current_step}/${t.total_steps || t.step_count || 6}</span></td>
                  <td>${this.renderApprovalBadge(t.approval_status)}</td>
                  <td style="font-size: 0.8rem; color: var(--text-muted);">${new Date(t.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                  <td>
                    <button class="btn btn-sm btn-outline" onclick="AgentWorkspaceView.inspectTask('${t.id}')">
                      Inspect &rarr;
                    </button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<p style="color: #EF4444;">Error loading tasks: ${err.message}</p>`;
    }
  },

  async inspectTask(taskId) {
    try {
      const task = await API.get(`/api/agent/tasks/${taskId}`);
      this.currentTask = task;
      this.renderCurrentTask(task);
      const taskEl = document.getElementById('current-task-container');
      if (taskEl) taskEl.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      showToast(`Failed to load task ${taskId}`, 'error');
    }
  },

  renderCurrentTask(task) {
    const container = document.getElementById('current-task-container');
    if (!container) return;
    container.style.display = 'block';

    const steps = task.steps || [];
    const approvals = task.approvals || [];
    const pendingApproval = approvals.find(a => a.status === 'PENDING');
    const finalOut = task.final_output || {};

    container.innerHTML = `
      <div class="glass-card" style="border-top: 4px solid #4F46E5; margin-bottom: 1.5rem;">
        <!-- TASK HEADER -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem;">
          <div>
            <div style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">TASK #${task.id}</div>
            <h3 style="font-size: 1.25rem; font-weight: 800; color: var(--text-primary); margin: 0.25rem 0;">
              ${task.objective}
            </h3>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">
              Initiated: ${new Date(task.created_at).toLocaleString()} &bull;
              Horizon: <strong>${task.constraints?.days_horizon || 7} days</strong> &bull;
              Budget Limit: <strong>${task.constraints?.budget_limit_inr ? '₹' + task.constraints.budget_limit_inr.toLocaleString('en-IN') : 'None'}</strong>
            </div>
          </div>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            ${this.renderStatusBadge(task.status)}
            ${task.status === 'RUNNING' || task.status === 'WAITING_FOR_APPROVAL' ? `
              <button class="btn btn-sm btn-secondary" onclick="AgentWorkspaceView.cancelTask('${task.id}')">Cancel Task</button>
            ` : ''}
          </div>
        </div>

        <!-- RESULT SUMMARY CALLOUT -->
        ${task.result_summary ? `
          <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 1.5rem; font-size: 0.875rem; color: #1E293B;">
            <strong>📌 Final Execution Summary:</strong> ${task.result_summary}
          </div>
        ` : ''}

        <!-- HUMAN APPROVAL CENTER (IF PENDING) -->
        ${pendingApproval ? `
          <div class="glass-card" style="background: #FFFBEB; border: 1.5px solid #F59E0B; margin-bottom: 1.5rem; padding: 1.25rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
              <div style="display: flex; align-items: center; gap: 0.5rem; color: #B45309; font-weight: 800; font-size: 1rem;">
                <span>🛡️ Human-In-The-Loop Approval Gateway</span>
              </div>
              <span class="badge" style="background: #FEF3C7; color: #B45309; font-weight: 800;">DECISION REQUIRED</span>
            </div>
            <p style="color: #92400E; font-size: 0.85rem; margin-bottom: 1rem;">
              The Procurement Agent prepared the following order. In accordance with safety policies, spending authorization requires Store Manager or Admin approval before submitting to wholesale suppliers.
            </p>

            <div style="background: #FFFFFF; border: 1px solid #FDE68A; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-weight: 700;">
                <span>Supplier: <strong>${pendingApproval.proposed_payload?.supplier_name || 'Wholesale Supplier'}</strong></span>
                <span style="color: #059669; font-size: 1.1rem;">Total Cost: ₹${(pendingApproval.estimated_cost || 0).toLocaleString('en-IN')}</span>
              </div>
              <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.75rem;">
                Justification: <em>${pendingApproval.justification}</em>
              </div>

              <!-- Line items table -->
              ${pendingApproval.proposed_payload?.items ? `
                <table class="data-table" style="width: 100%; font-size: 0.8rem;">
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Quantity</th>
                      <th>Unit Cost</th>
                      <th>GST</th>
                      <th>Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${pendingApproval.proposed_payload.items.map(it => `
                      <tr>
                        <td><strong>${it.product_name || 'Product ' + it.product_id}</strong></td>
                        <td>${it.quantity} ${it.unit || 'units'}</td>
                        <td>₹${it.unit_cost}</td>
                        <td>${it.gst_rate || 5}%</td>
                        <td><strong>₹${it.line_cost ? it.line_cost.toLocaleString('en-IN') : (it.quantity * it.unit_cost).toLocaleString('en-IN')}</strong></td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              ` : ''}
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
              <button class="btn btn-secondary" onclick="AgentWorkspaceView.handleApprovalDecision('${task.id}', ${pendingApproval.id}, false)">
                ❌ Reject Order
              </button>
              <button class="btn btn-primary" style="background: #059669; border-color: #059669;" onclick="AgentWorkspaceView.handleApprovalDecision('${task.id}', ${pendingApproval.id}, true)">
                ✅ Authorize & Dispatch Purchase Order
              </button>
            </div>
          </div>
        ` : ''}

        <!-- MULTI-AGENT ACTIVITY TIMELINE -->
        <h4 style="font-size: 1rem; font-weight: 800; color: var(--text-primary); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.4rem;">
          <span>⏱️</span> Execution Timeline & Agent Activity Traces
        </h4>

        <div class="agent-activity-timeline" style="margin-bottom: 1.5rem;">
          ${steps.map(s => `
            <div class="timeline-step-item">
              <div class="timeline-step-icon ${s.step_status.toLowerCase()}">
                ${s.step_status === 'COMPLETED' ? '✓' : s.step_status === 'RUNNING' ? '⚡' : '•'}
              </div>
              <div class="timeline-step-body">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                  <span style="font-weight: 800; color: var(--text-primary); font-size: 0.9rem;">
                    Step ${s.step_number}: ${s.action_type} &bull; <span style="color: #4F46E5;">${s.agent_name}</span>
                  </span>
                  <span style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">
                    ${s.duration_ms ? s.duration_ms + 'ms' : ''}
                  </span>
                </div>
                ${s.tool_name ? `
                  <div style="margin: 0.25rem 0; font-size: 0.775rem;">
                    <span style="color: #059669; font-weight: 700;">Tool:</span> <code>${s.tool_name}</code>
                  </div>
                ` : ''}
                ${s.reflection ? `
                  <div style="font-size: 0.825rem; color: var(--text-secondary); margin-top: 0.35rem; line-height: 1.4;">
                    ${s.reflection}
                  </div>
                ` : ''}
              </div>
            </div>
          `).join('')}
        </div>

        <!-- STRUCTURED OUTPUTS ACCORDION -->
        ${finalOut.procurement_plan ? `
          <div style="margin-top: 1.5rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
            <h4 style="font-size: 1rem; font-weight: 800; color: var(--text-primary); margin-bottom: 0.75rem;">
              📊 Restocking Plan Details
            </h4>
            <div class="kpi-grid" style="margin-bottom: 1rem;">
              <div class="glass-card-subtle">
                <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700;">PROPOSED ORDERS</div>
                <div style="font-size: 1.3rem; font-weight: 900; color: #4F46E5;">${finalOut.procurement_plan.draft_orders?.length || 0}</div>
              </div>
              <div class="glass-card-subtle">
                <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700;">TOTAL ESTIMATED SPEND</div>
                <div style="font-size: 1.3rem; font-weight: 900; color: #059669;">
                  ₹${(finalOut.procurement_plan.budget_analysis?.adjusted_total_spend_inr || finalOut.procurement_plan.budget_analysis?.total_spend_inr || 0).toLocaleString('en-IN')}
                </div>
              </div>
              <div class="glass-card-subtle">
                <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700;">BUDGET COMPLIANCE</div>
                <div style="font-size: 1.3rem; font-weight: 900; color: ${finalOut.procurement_plan.budget_analysis?.is_within_budget ? '#059669' : '#DC2626'};">
                  ${finalOut.procurement_plan.budget_analysis?.is_within_budget ? '100% Valid' : 'Exceeded'}
                </div>
              </div>
            </div>
          </div>
        ` : ''}
      </div>
    `;
  },

  async handleApprovalDecision(taskId, approvalId, approved) {
    let reason = null;
    if (!approved) {
      reason = prompt("Please provide a reason for rejecting this purchase order:") || "Manager rejected";
    }

    try {
      const endpoint = approved ? `/api/agent/tasks/${taskId}/approve` : `/api/agent/tasks/${taskId}/reject`;
      const res = await API.post(endpoint, {
        approval_id: approvalId,
        reason
      });

      showToast(approved ? "Purchase order approved and submitted!" : "Order proposal rejected.", approved ? "success" : "info");
      await this.inspectTask(taskId);
      await this.loadRecentTasks();
    } catch (err) {
      showToast(err.message || "Failed to submit approval decision", "error");
    }
  },

  async cancelTask(taskId) {
    if (!confirm("Are you sure you want to cancel this agent task?")) return;
    try {
      await API.post(`/api/agent/tasks/${taskId}/cancel`);
      showToast("Task cancelled", "info");
      await this.inspectTask(taskId);
      await this.loadRecentTasks();
    } catch (err) {
      showToast(err.message || "Failed to cancel task", "error");
    }
  },

  renderStatusBadge(status) {
    const map = {
      PENDING: '<span class="badge" style="background: #F3F4F6; color: #4B5563;">PENDING</span>',
      PLANNING: '<span class="badge" style="background: #E0E7FF; color: #4338CA;">PLANNING</span>',
      RUNNING: '<span class="badge" style="background: #DBEAFE; color: #1D4ED8;"><span class="pulse-dot"></span> RUNNING</span>',
      WAITING_FOR_APPROVAL: '<span class="badge" style="background: #FEF3C7; color: #B45309; font-weight: 800;">WAITING APPROVAL</span>',
      COMPLETED: '<span class="badge badge-safe">✓ COMPLETED</span>',
      FAILED: '<span class="badge badge-critical">FAILED</span>',
      CANCELLED: '<span class="badge" style="background: #FEE2E2; color: #991B1B;">CANCELLED</span>'
    };
    return map[status] || `<span class="badge">${status}</span>`;
  },

  renderApprovalBadge(appr) {
    const map = {
      NOT_REQUIRED: '<span style="color: var(--text-muted); font-size: 0.8rem;">Auto</span>',
      PENDING: '<span class="badge" style="background: #FEF3C7; color: #B45309; font-weight: 700;">Needs Approval</span>',
      APPROVED: '<span class="badge badge-safe">Approved</span>',
      REJECTED: '<span class="badge badge-critical">Rejected</span>'
    };
    return map[appr] || appr || '—';
  }
};
