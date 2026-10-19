/**
 * Helios PRD - Material Lines Dummy Application
 * Local prototype logic for Excel-driven line entry
 */

(function () {
  'use strict';

  // Sample catalog descriptions for visual fidelity with screenshot
  const PART_DESCRIPTIONS = {
    'CABL00058': 'TipTag Name Label 65x15mm - roll 100',
    'CABL00059': 'TipTag Name Label 30x11mm - roll 100',
    'DBDS00031': 'Number Label traffol/Acrylic 12x10x1.5mm',
    'DBDS00030': 'Name Label traffol/Acrylic 50x12x1.5mm',
    'DBDS00029': 'Name Label Traffoll/Acrylic 80x25x1.5mm',
    'DBDS00028': 'Name Label Traffoll/Acrylic 180x30x1.5mm',
    'FOKT00004': 'Fall Arrest System 50m'
  };

  // State
  let currentLineNumber = 10;
  let savedLines = [];

  // DOM Elements
  const partInput = document.getElementById('input-part');
  const qtyInput = document.getElementById('input-qty');
  const siteInput = document.getElementById('input-site');
  const costCodeInput = document.getElementById('input-cost-code');
  const wbsInput = document.getElementById('input-wbs');

  const currentLineNoInput = document.getElementById('input-current-line-no');
  const btnAddLine = document.getElementById('btn-add-line');
  const btnClearForm = document.getElementById('btn-clear-form');
  const btnResetTable = document.getElementById('btn-reset-table');

  const tableBody = document.getElementById('lines-table-body');
  const recordCountSpan = document.getElementById('record-count');
  const totalCountSpan = document.getElementById('total-count');
  const statusMessage = document.getElementById('status-message');

  function updateStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = 'status-banner';
    if (type === 'success') {
      statusMessage.classList.add('status-success');
    } else if (type === 'error') {
      statusMessage.classList.add('status-error');
    } else {
      statusMessage.classList.add('status-idle');
    }
  }

  function showErrorPopup(message) {
    const popup = document.getElementById('error-popup');
    const textEl = document.getElementById('modal-error-text');
    if (popup && textEl) {
      textEl.textContent = message;
      popup.style.display = 'flex';
    }
  }

  function clearFormInputs() {
    partInput.value = '';
    qtyInput.value = '';
    siteInput.value = '';
    costCodeInput.value = '';
    wbsInput.value = '';
    partInput.focus();
  }

  function renderTable() {
    tableBody.innerHTML = '';
    savedLines.forEach((item) => {
      const tr = document.createElement('tr');
      tr.setAttribute('data-testid', 'material-line-row');
      tr.setAttribute('data-line-id', item.line);

      tr.innerHTML = `
        <td data-field="line">${item.line}</td>
        <td data-field="part" style="font-weight: 600;">${item.part}</td>
        <td data-field="description">${item.description}</td>
        <td data-field="qty" style="text-align: right;">${item.qty}</td>
        <td data-field="site">${item.site}</td>
        <td data-field="cost-code">${item.costCode}</td>
        <td data-field="wbs">${item.wbs}</td>
        <td data-field="available-qty">36,916</td>
        <td data-field="qty-on-hand">37,343</td>
        <td data-field="bin">400206-PROJ</td>
        <td data-field="issued-qty">0</td>
        <td data-field="returns-qty">0</td>
        <td data-field="return-cond"></td>
        <td data-field="exp-return-qty"></td>
        <td data-field="material-list"></td>
        <td data-field="commodity"></td>
      `;
      tableBody.appendChild(tr);
    });

    recordCountSpan.textContent = savedLines.length;
    totalCountSpan.textContent = savedLines.length;
    currentLineNoInput.value = currentLineNumber;
  }

  function handleAddLine() {
    const part = partInput.value.trim();
    const qtyRaw = qtyInput.value.trim();
    const site = siteInput.value.trim();
    const costCode = costCodeInput.value.trim();
    const wbs = wbsInput.value.trim();

    // 1. Validation: check missing required fields
    const missing = [];
    if (!part) missing.push('Part');
    if (!qtyRaw) missing.push('Qty');
    if (!site) missing.push('Site');
    if (!costCode) missing.push('Cost Code - SAP Budget Line');
    if (!wbs) missing.push('WBS and Project Code');

    if (missing.length > 0) {
      const errMsg = `Validation Error: Missing required field(s): ${missing.join(', ')}`;
      updateStatus(errMsg, 'error');
      showErrorPopup(errMsg);
      return false;
    }

    // 2. Validation: check quantity is positive number
    const qtyNum = Number(qtyRaw);
    if (isNaN(qtyNum) || qtyNum <= 0) {
      const errMsg = 'Validation Error: Quantity must be a valid positive number.';
      updateStatus(errMsg, 'error');
      showErrorPopup(errMsg);
      return false;
    }

    // 3. Create entry
    const newLineRecord = {
      line: currentLineNumber,
      part: part,
      qty: qtyNum,
      site: site,
      costCode: costCode,
      wbs: wbs,
      description: PART_DESCRIPTIONS[part] || 'Material Item'
    };

    savedLines.push(newLineRecord);
    currentLineNumber += 10;

    renderTable();
    clearFormInputs();

    updateStatus(`Success: Line ${newLineRecord.line} saved successfully (Part: ${newLineRecord.part}, Qty: ${newLineRecord.qty})`, 'success');
    return true;
  }

  function handleResetTable() {
    savedLines = [];
    currentLineNumber = 10;
    renderTable();
    clearFormInputs();
    updateStatus('Table reset. Ready for entries.', 'idle');
  }

  // Enter key submission handler
  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      handleAddLine();
    }
  }

  // Event Listeners: Enter key on inputs
  [partInput, qtyInput, siteInput, costCodeInput, wbsInput].forEach((input) => {
    input.addEventListener('keydown', handleKeyDown);
  });

  if (btnAddLine) {
    btnAddLine.addEventListener('click', handleAddLine);
  }
  btnClearForm.addEventListener('click', () => {
    clearFormInputs();
    updateStatus('Form inputs cleared.', 'idle');
  });
  btnResetTable.addEventListener('click', handleResetTable);

  // Initialize
  renderTable();
  updateStatus('Ready. Waiting for input. (Press Enter to save line)', 'idle');

  // Expose test helper on window for programmatic inspection if needed
  window.__DEMO_APP__ = {
    getSavedLines: () => [...savedLines],
    reset: handleResetTable,
    addLine: handleAddLine
  };
})();
