// MediMate Client App Controller

document.addEventListener('DOMContentLoaded', () => {
  // Config
  const API_BASE = ''; // Same host

  // DOM Elements
  const toggleVoice = document.getElementById('toggle-voice');
  const toggleText = document.getElementById('toggle-text');
  const voiceInputSection = document.getElementById('voice-input-section');
  const textInputSection = document.getElementById('text-input-section');
  
  const recordButton = document.getElementById('record-button');
  const recordIcon = document.getElementById('record-icon');
  const recordRing = document.getElementById('record-ring');
  const recordStatus = document.getElementById('record-status');
  const recordTimer = document.getElementById('record-timer');
  
  const transcriptTextarea = document.getElementById('transcript-textarea');
  const patientNameInput = document.getElementById('patient-name');
  const generateBtn = document.getElementById('generate-btn');
  
  const safetyAlert = document.getElementById('safety-alert');
  const safetyTitle = document.getElementById('safety-title');
  const safetyDesc = document.getElementById('safety-desc');
  const acuityBadge = document.getElementById('acuity-badge');
  
  const soapTabs = document.querySelectorAll('.soap-tab');
  const soapTextareas = {
    subjective: document.getElementById('soap-subjective'),
    objective: document.getElementById('soap-objective'),
    assessment: document.getElementById('soap-assessment'),
    plan: document.getElementById('soap-plan')
  };
  
  const toolTabs = document.querySelectorAll('.tool-tab');
  const toolPanes = {
    icd10: document.getElementById('pane-icd10'),
    tests: document.getElementById('pane-tests'),
    drugs: document.getElementById('pane-drugs'),
    rag: document.getElementById('pane-rag')
  };
  
  const icdContainer = document.getElementById('icd-container');
  const testsContainer = document.getElementById('tests-container');
  const drugsContainer = document.getElementById('drugs-container');
  const ragContainer = document.getElementById('rag-container');
  const btnAddIcd = document.getElementById('btn-add-icd');
  const approveBtn = document.getElementById('approve-btn');
  
  const dashTabs = document.querySelectorAll('.dash-tab');
  const dashPanes = {
    records: document.getElementById('dash-records'),
    eval: document.getElementById('dash-eval')
  };
  
  const recordsContainer = document.getElementById('records-container');
  const runEvalBtn = document.getElementById('run-eval-btn');
  const metricSoap = document.getElementById('metric-soap');
  const metricIcd = document.getElementById('metric-icd');
  const metricSafety = document.getElementById('metric-safety');
  const metricHallucination = document.getElementById('metric-hallucination');
  const evalTableBody = document.getElementById('eval-table-body');
  const evalSearch = document.getElementById('eval-search');

  // State Variables
  let mediaRecorder = null;
  let audioChunks = [];
  let recordingInterval = null;
  let recordingSeconds = 0;
  let isRecording = false;
  let activeInputType = 'voice'; // 'voice' or 'text'
  
  let currentSoapDraft = null;
  let recognition = null; // HTML5 speech recognition instance
  let evaluationCachedResults = [];

  // Init
  loadSavedNotes();
  loadEvaluationCache();

  // === INPUT SWITCHER ===
  toggleVoice.addEventListener('click', () => {
    activeInputType = 'voice';
    toggleVoice.classList.add('active');
    toggleText.classList.remove('active');
    voiceInputSection.classList.remove('hidden');
    textInputSection.classList.add('hidden');
  });

  toggleText.addEventListener('click', () => {
    activeInputType = 'text';
    toggleText.classList.add('active');
    toggleVoice.classList.remove('active');
    textInputSection.classList.remove('hidden');
    voiceInputSection.classList.add('hidden');
  });

  // === SPEECH RECORDING & DICTATION API ===
  // Initialize native browser Web Speech API if supported
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      // If recording, update the textarea so the user has immediate visualization
      if (finalTranscript) {
        transcriptTextarea.value += (transcriptTextarea.value ? ' ' : '') + finalTranscript;
      }
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition warning:', event.error);
    };
  }

  recordButton.addEventListener('click', () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  async function startRecording() {
    audioChunks = [];
    recordingSeconds = 0;
    isRecording = true;
    
    recordRing.classList.add('recording');
    recordIcon.className = 'fa-solid fa-square';
    recordStatus.textContent = 'Dictating... Speak now. (Real-time transcription active)';
    
    // Start Web Audio recording for Whisper upload
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      mediaRecorder.onstop = uploadAudioForWhisper;
      mediaRecorder.start();
    } catch (err) {
      console.warn('Microphone stream error, utilizing native speech transcription only:', err);
    }

    // Start native browser visual typing
    if (recognition) {
      try {
        recognition.start();
      } catch (e) {}
    }

    // Timer
    recordTimer.textContent = '00:00';
    recordingInterval = setInterval(() => {
      recordingSeconds++;
      const mins = String(Math.floor(recordingSeconds / 60)).padStart(2, '0');
      const secs = String(recordingSeconds % 60).padStart(2, '0');
      recordTimer.textContent = `${mins}:${secs}`;
    }, 1000);
  }

  function stopRecording() {
    isRecording = false;
    recordRing.classList.remove('recording');
    recordIcon.className = 'fa-solid fa-microphone-lines';
    recordStatus.textContent = 'Processing dictation transcription...';
    
    clearInterval(recordingInterval);
    
    // Stop Media Recorder
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }

    // Stop Native Speech Recognition
    if (recognition) {
      try {
        recognition.stop();
      } catch (e) {}
    }
  }

  async function uploadAudioForWhisper() {
    if (audioChunks.length === 0) return;
    
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'dictation.wav');

    try {
      const res = await fetch(`${API_BASE}/api/transcribe`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      
      if (data.text) {
        // Populate the textarea with the transcription
        transcriptTextarea.value = data.text;
        recordStatus.textContent = data.fallbackUsed 
          ? `Transcribed (Local Simulation): Completed`
          : `Transcribed (Whisper-1): Completed`;
        
        // Auto-switch to text input mode to allow edits
        activeInputType = 'text';
        toggleText.click();
      } else {
        recordStatus.textContent = 'Transcription returned empty response.';
      }
    } catch (err) {
      console.error('Transcription error:', err);
      recordStatus.textContent = 'Transcription failed. Please type summary instead.';
    }
  }

  // === PRESET ENCOUNTERS ===
  const CLINICAL_PRESETS = {
    htn: {
      name: "Hypertension Check-up",
      text: "The patient is a 55-year-old male with a history of Stage 2 Hypertension. He's been checking his blood pressure at home and it's running around 145 over 92. He complains of mild headaches but denies any chest pain, shortness of breath, or palpitations. He is currently on no medications. We will start him on Lisinopril 10 mg daily and check a BMP in two weeks."
    },
    asthma: {
      name: "Asthma Flare-up",
      text: "A 34-year-old female presents with acute shortness of breath and expiratory wheezing that started last night. She has a history of childhood asthma and has been using an albuterol inhaler three times a day for the past week. She denies fever, chills, or productive cough. On exam, diffuse expiratory wheezes are present. We will start a daily low-dose ICS-formoterol inhaler and follow up in two weeks."
    },
    contrast: {
      name: "Contrast Study Safety Screening",
      text: "The patient is a 62-year-old female coming in for a follow-up on her Type 2 Diabetes. Her latest home glucose readings have been averaging 160. She is currently taking Metformin 500 mg twice a day. She denies any polyuria, polydipsia, or blurred vision, but she is scheduled for an outpatient CT scan with iodinated contrast dye next Tuesday. We discussed withholding Metformin for 48 hours post-contrast and checking a basic metabolic panel to monitor renal function."
    },
    chestpain: {
      name: "High Acuity: Acute Chest Pain",
      text: "A 58-year-old male presents with acute onset substernal chest pressure radiating to the left arm and jaw. The pain started 30 minutes ago, is rated 9 out of 10 in severity, and is accompanied by profuse diaphoresis, shortness of breath, and mild nausea. He has a history of dyslipidemia and active smoking. Immediate transfer to emergency department is required. Patient advised to chew aspirin 325 mg immediately."
    }
  };

  document.querySelectorAll('.preset-item').forEach(item => {
    item.addEventListener('click', () => {
      const presetKey = item.getAttribute('data-preset');
      const preset = CLINICAL_PRESETS[presetKey];
      if (preset) {
        patientNameInput.value = preset.name;
        transcriptTextarea.value = preset.text;
        activeInputType = 'text';
        toggleText.click();
        
        // Auto generate note for fast demonstrations
        generateSOAPNote();
      }
    });
  });

  // === SOAP NOTE GENERATION ===
  generateBtn.addEventListener('click', generateSOAPNote);

  async function generateSOAPNote() {
    const transcript = transcriptTextarea.value.trim();
    if (!transcript) {
      alert('Please speak or type a patient summary first.');
      return;
    }

    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating Note...';
    
    // Clear previous view state
    safetyAlert.classList.add('hidden');
    acuityBadge.className = 'badge';
    acuityBadge.textContent = 'Acuity: Processing...';

    try {
      const res = await fetch(`${API_BASE}/api/generate-soap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript, forceOffline: false })
      });
      
      if (!res.ok) throw new Error('API server returned error.');
      
      const data = await res.json();
      currentSoapDraft = data;
      
      // Render SOAP sections
      soapTextareas.subjective.value = data.soapNote.subjective || '';
      soapTextareas.objective.value = data.soapNote.objective || '';
      soapTextareas.assessment.value = data.soapNote.assessment || '';
      soapTextareas.plan.value = data.soapNote.plan || '';
      
      // Select first tab (Subjective)
      document.querySelector('.soap-tab[data-sec="subjective"]').click();
      
      // Render Acuity Badge
      acuityBadge.textContent = `Acuity: ${data.acuityLevel}`;
      if (data.acuityLevel === 'High') {
        acuityBadge.classList.add('acuity-high');
      } else if (data.acuityLevel === 'Moderate') {
        acuityBadge.classList.add('acuity-mod');
      } else {
        acuityBadge.classList.add('acuity-low');
      }

      // Render Safety alert if high acuity or out of scope
      if (data.isOutsideScope) {
        safetyAlert.classList.remove('hidden');
        safetyTitle.textContent = "High Acuity / Out-of-Scope Warning";
        safetyDesc.textContent = data.safetyRefusals.join(' | ') || "Patient displays emergency red-flags. Directing immediately to Emergency Services.";
      }

      // Render Tools widgets
      renderICD10(data.icd10);
      renderTests(data.tests);
      renderDrugs(data.drugInteractions);
      renderRAG(data.relevantGuidelines);

    } catch (err) {
      console.error(err);
      alert('Failed to generate SOAP note. Is the server running?');
    } finally {
      generateBtn.disabled = false;
      generateBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate SOAP Note';
    }
  }

  // === RENDER CLINICAL TOOLS ===
  
  function renderICD10(icdList) {
    icdContainer.innerHTML = '';
    if (!icdList || icdList.length === 0) {
      icdContainer.innerHTML = '<p class="empty-state">No codes suggested.</p>';
      return;
    }
    
    icdList.forEach((item, index) => {
      const div = document.createElement('div');
      div.className = 'icd-badge';
      div.innerHTML = `
        <span class="icd-code-name">${item.code}</span>
        <span class="icd-code-desc">${item.description}</span>
        <button class="remove-tag" data-index="${index}"><i class="fa-solid fa-xmark"></i></button>
      `;
      div.querySelector('.remove-tag').addEventListener('click', () => {
        icdList.splice(index, 1);
        renderICD10(icdList);
      });
      icdContainer.appendChild(div);
    });
  }

  btnAddIcd.addEventListener('click', () => {
    if (!currentSoapDraft) return;
    const code = prompt("Enter ICD-10 Code (e.g. E11.9):");
    const desc = prompt("Enter Code Description:");
    if (code && desc) {
      if (!currentSoapDraft.icd10) currentSoapDraft.icd10 = [];
      currentSoapDraft.icd10.push({ code, description: desc, confidence: 1.0, rationale: "Manually added by clinician." });
      renderICD10(currentSoapDraft.icd10);
    }
  });

  function renderTests(testsList) {
    testsContainer.innerHTML = '';
    if (!testsList || testsList.length === 0) {
      testsContainer.innerHTML = '<p class="empty-state">No tests recommended.</p>';
      return;
    }
    
    testsList.forEach((test) => {
      const div = document.createElement('div');
      div.className = 'test-item';
      div.innerHTML = `
        <input type="checkbox" checked>
        <label>${test}</label>
      `;
      testsContainer.appendChild(div);
    });
  }

  function renderDrugs(interactions) {
    drugsContainer.innerHTML = '';
    if (!interactions || interactions.length === 0) {
      drugsContainer.innerHTML = `
        <div class="drug-alert safe">
          <i class="fa-solid fa-circle-check"></i> No severe drug-drug interactions detected.
        </div>
      `;
      return;
    }

    interactions.forEach(warn => {
      const isCritical = warn.includes('CRITICAL');
      const div = document.createElement('div');
      div.className = `drug-alert ${isCritical ? 'danger' : 'warn'}`;
      div.innerHTML = `
        <i class="fa-solid ${isCritical ? 'fa-skull-crossbones' : 'fa-triangle-exclamation'}"></i>
        <span>${warn}</span>
      `;
      drugsContainer.appendChild(div);
    });
  }

  function renderRAG(guidelines) {
    ragContainer.innerHTML = '';
    if (!guidelines || guidelines.length === 0) {
      ragContainer.innerHTML = '<p class="empty-state">No guidelines matched (direct clinical context query empty).</p>';
      return;
    }
    
    guidelines.forEach(g => {
      const div = document.createElement('div');
      div.className = 'rag-item';
      div.innerHTML = `
        <div class="rag-item-header">
          <span>${g.condition} - ${g.title}</span>
          <span class="rag-score">ID: ${g.id}</span>
        </div>
        <p>Guidelines chunk loaded into agent context for formatting instructions.</p>
      `;
      ragContainer.appendChild(div);
    });
  }

  // === HUMAN-IN-THE-LOOP APPROVAL ===
  approveBtn.addEventListener('click', async () => {
    if (!currentSoapDraft) {
      alert('No note draft available to approve.');
      return;
    }

    approveBtn.disabled = true;
    approveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving approved note...';

    // Collect edited fields from UI textareas (HITL override)
    const approvedSoap = {
      subjective: soapTextareas.subjective.value,
      objective: soapTextareas.objective.value,
      assessment: soapTextareas.assessment.value,
      plan: soapTextareas.plan.value
    };

    const payload = {
      patientName: patientNameInput.value || 'Anonymous Patient',
      transcript: transcriptTextarea.value,
      soapNote: approvedSoap,
      icd10: currentSoapDraft.icd10 || [],
      tests: Array.from(testsContainer.querySelectorAll('input:checked')).map(cb => cb.nextElementSibling.textContent),
      drugInteractions: currentSoapDraft.drugInteractions || [],
      acuityLevel: currentSoapDraft.acuityLevel || 'Low',
      isOutsideScope: currentSoapDraft.isOutsideScope || false,
      safetyRefusals: currentSoapDraft.safetyRefusals || []
    };

    try {
      const res = await fetch(`${API_BASE}/api/save-note`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      
      if (data.success) {
        alert('SOAP Note successfully approved, signed, and saved to the patient files.');
        loadSavedNotes();
        // Clear workspace
        currentSoapDraft = null;
        soapTextareas.subjective.value = '';
        soapTextareas.objective.value = '';
        soapTextareas.assessment.value = '';
        soapTextareas.plan.value = '';
        icdContainer.innerHTML = '<p class="empty-state">No codes suggested.</p>';
        testsContainer.innerHTML = '<p class="empty-state">No recommended tests yet.</p>';
        drugsContainer.innerHTML = '<div class="drug-alert safe"><i class="fa-solid fa-circle-check"></i> No interactions detected.</div>';
        ragContainer.innerHTML = '<p class="empty-state">No context retrieved yet.</p>';
        safetyAlert.classList.add('hidden');
        acuityBadge.className = 'badge';
        acuityBadge.textContent = 'Acuity: Normal';
      }
    } catch (err) {
      console.error(err);
      alert('Failed to save approved note.');
    } finally {
      approveBtn.disabled = false;
      approveBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Approve & Save Note';
    }
  });

  async function loadSavedNotes() {
    try {
      const res = await fetch(`${API_BASE}/api/notes`);
      const notes = await res.json();
      
      recordsContainer.innerHTML = '';
      if (!notes || notes.length === 0) {
        recordsContainer.innerHTML = '<p class="empty-state">No notes approved yet. Click "Approve & Save" to add records here.</p>';
        return;
      }
      
      notes.reverse().forEach(note => {
        const div = document.createElement('div');
        div.className = 'record-box';
        
        let acuityClass = 'acuity-low';
        if (note.acuityLevel === 'High') acuityClass = 'acuity-high';
        else if (note.acuityLevel === 'Moderate') acuityClass = 'acuity-mod';
        
        div.innerHTML = `
          <div class="rec-meta">
            <h4>${note.patientName}</h4>
            <span>Saved on ${new Date(note.updatedAt).toLocaleString()}</span>
          </div>
          <div class="rec-badges">
            <span class="badge ${acuityClass}">${note.acuityLevel} Acuity</span>
            <span class="badge">${note.icd10.map(x => x.code).join(', ') || 'Z00.00'}</span>
            <button class="rec-btn-view">Load note</button>
          </div>
        `;
        
        div.querySelector('.rec-btn-view').addEventListener('click', () => {
          // Load this historical note back into the editor
          currentSoapDraft = note;
          patientNameInput.value = note.patientName;
          transcriptTextarea.value = note.transcript;
          
          soapTextareas.subjective.value = note.soapNote.subjective;
          soapTextareas.objective.value = note.soapNote.objective;
          soapTextareas.assessment.value = note.soapNote.assessment;
          soapTextareas.plan.value = note.soapNote.plan;
          
          acuityBadge.textContent = `Acuity: ${note.acuityLevel}`;
          acuityBadge.className = `badge ${acuityClass}`;
          
          if (note.isOutsideScope) {
            safetyAlert.classList.remove('hidden');
            safetyTitle.textContent = "High Acuity / Out-of-Scope Record";
            safetyDesc.textContent = note.safetyRefusals.join(' | ');
          } else {
            safetyAlert.classList.add('hidden');
          }
          
          renderICD10(note.icd10);
          renderTests(note.tests);
          renderDrugs(note.drugInteractions);
          renderRAG([]);
          
          // Switch to Subjective tab
          document.querySelector('.soap-tab[data-sec="subjective"]').click();
          // Scroll up
          window.scrollTo({ top: 200, behavior: 'smooth' });
        });
        
        recordsContainer.appendChild(div);
      });
    } catch (err) {
      console.error('Error loading notes:', err);
    }
  }

  // === AUTOMATED EVALUATION PIPELINE ===
  runEvalBtn.addEventListener('click', async () => {
    runEvalBtn.disabled = true;
    runEvalBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Testing 50 case samples...';
    
    try {
      const res = await fetch(`${API_BASE}/api/run-eval`, { method: 'POST' });
      const data = await res.json();
      
      renderEvaluationMetrics(data);
      alert('50-Sample Evaluation Suite completed successfully! Visual metrics are loaded.');
    } catch (err) {
      console.error(err);
      alert('Evaluation pipeline failed. Verify python evaluate.py setup.');
    } finally {
      runEvalBtn.disabled = false;
      runEvalBtn.innerHTML = '<i class="fa-solid fa-play"></i> Run 50-Sample Evaluation Pipeline';
    }
  });

  async function loadEvaluationCache() {
    try {
      const res = await fetch(`${API_BASE}/api/eval-results`);
      const data = await res.json();
      if (!data.error) {
        renderEvaluationMetrics(data);
      }
    } catch (e) {}
  }

  function renderEvaluationMetrics(data) {
    if (!data.summary) return;
    
    // Set summary metric cards
    metricSoap.textContent = `${data.summary.soap_completeness_rate.toFixed(1)}%`;
    metricIcd.textContent = `${data.summary.icd10_accuracy_rate.toFixed(1)}%`;
    metricSafety.textContent = `${data.summary.safety_compliance_rate.toFixed(1)}%`;
    metricHallucination.textContent = `${data.summary.hallucination_rate.toFixed(1)}%`;
    
    evaluationCachedResults = data.details || [];
    renderEvaluationTable(evaluationCachedResults);
  }

  function renderEvaluationTable(details) {
    evalTableBody.innerHTML = '';
    
    if (details.length === 0) {
      evalTableBody.innerHTML = '<tr><td colspan="7" class="text-center">No cases found.</td></tr>';
      return;
    }
    
    details.forEach(item => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${item.id}</strong></td>
        <td>${item.domain}</td>
        <td><span class="badge ${item.acuity === 'High' ? 'acuity-high' : item.acuity === 'Moderate' ? 'acuity-mod' : 'acuity-low'}">${item.acuity}</span></td>
        <td class="text-center">${item.soap_complete ? '<i class="fa-solid fa-circle-check text-green"></i>' : '<i class="fa-solid fa-circle-xmark" style="color: var(--color-danger)"></i>'}</td>
        <td><code>${item.suggested_icd10.join(', ') || 'None'}</code></td>
        <td class="text-center">${item.safety_compliant ? '<i class="fa-solid fa-circle-check text-green"></i>' : '<i class="fa-solid fa-circle-xmark" style="color: var(--color-danger)"></i>'}</td>
        <td><span style="color: ${item.status === 'Passed' ? 'var(--color-success)' : 'var(--color-danger)'}; font-weight:600">${item.status}</span></td>
      `;
      evalTableBody.appendChild(tr);
    });
  }

  evalSearch.addEventListener('input', () => {
    const q = evalSearch.value.toLowerCase().trim();
    if (!q) {
      renderEvaluationTable(evaluationCachedResults);
      return;
    }
    
    const filtered = evaluationCachedResults.filter(item => 
      item.id.toLowerCase().includes(q) ||
      item.domain.toLowerCase().includes(q) ||
      item.suggested_icd10.some(code => code.toLowerCase().includes(q))
    );
    renderEvaluationTable(filtered);
  });

  // === TABS NAVIGATION CONTROLLERS ===
  
  // SOAP Tab Switcher
  soapTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      soapTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      const targetSec = tab.getAttribute('data-sec');
      Object.keys(soapTextareas).forEach(key => {
        if (key === targetSec) {
          soapTextareas[key].parentElement.classList.remove('hidden');
        } else {
          soapTextareas[key].parentElement.classList.add('hidden');
        }
      });
    });
  });

  // Tools Tab Switcher
  toolTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      toolTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      const targetTool = tab.getAttribute('data-tool');
      Object.keys(toolPanes).forEach(key => {
        if (key === targetTool) {
          toolPanes[key].classList.remove('hidden');
        } else {
          toolPanes[key].classList.add('hidden');
        }
      });
    });
  });

  // Dashboard Tab Switcher
  dashTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      dashTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      const targetPane = tab.getAttribute('data-tab');
      Object.keys(dashPanes).forEach(key => {
        if (key === targetPane) {
          dashPanes[key].classList.remove('hidden');
        } else {
          dashPanes[key].classList.add('hidden');
        }
      });
    });
  });

});
