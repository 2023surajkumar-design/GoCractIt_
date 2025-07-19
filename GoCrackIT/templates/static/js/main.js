// --- GoCrackIT Modern UI/UX Interactivity ---

document.addEventListener('DOMContentLoaded', function () {
    // --- Input Bar Elements ---
    const fileInput = document.getElementById('file-upload');
    const textInput = document.getElementById('text-input');
    const audioBtn = document.getElementById('record-audio-btn');
    const audioInput = document.getElementById('audio-upload');
    const extractBtn = document.getElementById('extract-btn');
    const inputBarForm = document.getElementById('input-bar-form');
    const inputFeedback = document.getElementById('input-feedback');

    // --- File Upload ---
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                textInput.value = '';
                inputFeedback.textContent = fileInput.files[0].name;
            } else {
                inputFeedback.textContent = '';
            }
        });
    }

    // --- Text Input ---
    if (textInput) {
        textInput.addEventListener('input', () => {
            if (textInput.value.trim()) {
                if (fileInput) fileInput.value = '';
                inputFeedback.textContent = '';
            }
        });
    }

    // --- Audio Record/Upload ---
    let recording = false;
    let mediaRecorder, audioChunks = [];
    if (audioBtn && audioInput) {
        audioBtn.addEventListener('click', () => {
            if (!recording) {
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    navigator.mediaDevices.getUserMedia({ audio: true })
                        .then(stream => {
                            mediaRecorder = new MediaRecorder(stream);
                            audioChunks = [];
                            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                            mediaRecorder.onstop = () => {
                                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                                audioInput.file = audioBlob;
                                inputFeedback.textContent = 'Audio recorded.';
                                if (fileInput) fileInput.value = '';
                                textInput.value = '';
                            };
                            mediaRecorder.start();
                            recording = true;
                            audioBtn.classList.add('recording');
                            inputFeedback.textContent = 'Recording...';
                        })
                        .catch(() => {
                            inputFeedback.textContent = 'Microphone access denied.';
                        });
                } else {
                    inputFeedback.textContent = 'Audio recording not supported.';
                }
            } else {
                if (mediaRecorder && recording) {
                    mediaRecorder.stop();
                    recording = false;
                    audioBtn.classList.remove('recording');
                }
            }
        });
        audioInput.addEventListener('change', () => {
            if (audioInput.files && audioInput.files.length) {
                inputFeedback.textContent = audioInput.files[0].name;
                if (fileInput) fileInput.value = '';
                textInput.value = '';
            }
        });
    }

    // --- Extract Data (Send) ---
    if (inputBarForm) {
        inputBarForm.addEventListener('submit', function (e) {
            e.preventDefault();
            inputFeedback.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Extracting...';
            
            const text = textInput.value.trim();
            const file = fileInput && fileInput.files.length ? fileInput.files[0] : null;
            let audioBlob = null;
            
            if (audioInput && audioInput.files && audioInput.files.length) {
                audioBlob = audioInput.files[0];
            } else if (audioInput && audioInput.file) {
                audioBlob = audioInput.file;
            }
            
            const formData = new FormData();
            
            if (audioBlob) {
                formData.append('audio', audioBlob, 'audio.wav');
            } else if (file) {
                formData.append('file', file);
            } else if (text) {
                formData.append('text', text);
            } else {
                inputFeedback.innerHTML = '<span class="text-danger">Please provide a file, text, or audio input.</span>';
                return;
            }
            
            fetch('/extract', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.result) {
                    inputFeedback.innerHTML = '<span class="text-success">Data extracted!</span>';
                    displayExtractedData(data.result);
                } else {
                    inputFeedback.innerHTML = '<span class="text-danger">Extraction failed: ' + (data.error || 'Unknown error') + '</span>';
                }
            })
            .catch(err => {
                console.error('Extraction error:', err);
                inputFeedback.innerHTML = '<span class="text-danger">Extraction failed. Please try again.</span>';
            });
        });
    }

    // --- Display Extracted Data in Review Area (Unified approach) ---
    function safeParseJsonBlock(block, key) {
        if (!block) return null;
        try {
            return JSON.stringify(JSON.parse(block), null, 2);
        } catch (e) {
            // Try to extract just the JSON object from inside the block
            const objMatch = block.match(new RegExp(`\\{\\s*"${key}"[\\s\\S]*?\\}`));
            if (objMatch) {
                try {
                    return JSON.stringify(JSON.parse(objMatch[0]), null, 2);
                } catch (e2) {
                    return null;
                }
            }
            return null;
        }
    }

    function displayExtractedData(resultText) {
        const personalInfoPlain = document.getElementById('personal-info-plain');
        const workJsonDiv = document.getElementById('work-experience-json');
        const eduJsonDiv = document.getElementById('education-json');
        
        if (!personalInfoPlain || !workJsonDiv || !eduJsonDiv) return;

        // Show the review area
        const reviewArea = document.getElementById('review-area');
        if (reviewArea) {
            reviewArea.style.display = 'block';
        }

        console.log("Raw Gemini response:", resultText);

        // First, try to find JSON blocks with code markers
        const codeBlockRegex = /```(?:json)?[\r\n]+([\s\S]*?)\s*```/gi;
        const codeBlocks = [...resultText.matchAll(codeBlockRegex)];
        
        let workJson = '';
        let eduJson = '';
        let personalInfoText = resultText;

        // Process code blocks first
        for (const match of codeBlocks) {
            const blockContent = match[1].trim();
            try {
                const parsed = JSON.parse(blockContent);
                if (parsed.experience) {
                    workJson = JSON.stringify(parsed.experience, null, 2);
                    personalInfoText = personalInfoText.replace(match[0], '');
                }
                if (parsed.education) {
                    eduJson = JSON.stringify(parsed.education, null, 2);
                    personalInfoText = personalInfoText.replace(match[0], '');
                }
            } catch (e) {
                // Not valid JSON, continue
            }
        }

        // If no JSON found in code blocks, try to find inline JSON
        if (!workJson) {
            const expMatch = resultText.match(/\{\s*"experience"\s*:\s*\[[\s\S]*?\]\s*\}/);
            if (expMatch) {
                try {
                    const parsed = JSON.parse(expMatch[0]);
                    workJson = JSON.stringify(parsed.experience, null, 2);
                    personalInfoText = personalInfoText.replace(expMatch[0], '');
                } catch (e) {
                    console.error("Failed to parse experience JSON:", e);
                }
            }
        }

        if (!eduJson) {
            const eduMatch = resultText.match(/\{\s*"education"\s*:\s*\[[\s\S]*?\]\s*\}/);
            if (eduMatch) {
                try {
                    const parsed = JSON.parse(eduMatch[0]);
                    eduJson = JSON.stringify(parsed.education, null, 2);
                    personalInfoText = personalInfoText.replace(eduMatch[0], '');
                } catch (e) {
                    console.error("Failed to parse education JSON:", e);
                }
            }
        }

        // Clean up personal info text
        personalInfoText = personalInfoText
            .replace(/```[\s\S]*?```/g, '') // Remove any remaining code blocks
            .replace(/\{\s*"experience"\s*:\s*\[[\s\S]*?\]\s*\}/g, '') // Remove experience JSON
            .replace(/\{\s*"education"\s*:\s*\[[\s\S]*?\]\s*\}/g, '') // Remove education JSON
            .trim();

        // Format personal info as labeled fields
        const infoLabels = [
            'Name:',
            'Phone number:',
            'Email:',
            'LinkedIn URL:',
            'Total years of experience:',
            'About me / Bio / Summary:'
        ];
        let formattedPersonalInfo = '';
        for (const label of infoLabels) {
            // Find the line starting with the label
            const regex = new RegExp(label + '\\s*(.*)', 'i');
            const match = personalInfoText.match(regex);
            if (match) {
                formattedPersonalInfo += `${label} ${match[1].trim()}\n`;
            }
        }
        if (!formattedPersonalInfo) {
            formattedPersonalInfo = personalInfoText || 'No personal information found.';
        }
        // Display each field on a new line
        personalInfoPlain.innerHTML = formattedPersonalInfo.replace(/\n/g, '<br>');
        workJsonDiv.textContent = workJson || 'No work experience found or could not parse JSON.';
        eduJsonDiv.textContent = eduJson || 'No education found or could not parse JSON.';

        console.log("Parsed results:", {
            personalInfo: formattedPersonalInfo,
            workExperience: workJson,
            education: eduJson
        });
    }

    // --- Enable Collapse for Cards ---
    function enableCollapse(selector) {
        document.querySelectorAll(selector).forEach(header => {
            header.addEventListener('click', function () {
                const target = document.querySelector(this.getAttribute('data-bs-target'));
                if (target) {
                    const isOpen = target.classList.contains('show');
                    document.querySelectorAll(this.getAttribute('data-bs-target')).forEach(el => el.classList.remove('show'));
                    if (!isOpen) target.classList.add('show');
                }
            });
        });
    }

    // --- Enable Inline Editing ---
    function enableInlineEditing(container) {
        container.querySelectorAll('.editable-field').forEach(field => {
            field.addEventListener('click', function () {
                if (this.classList.contains('editing')) return;
                this.classList.add('editing');
                const oldValue = this.textContent;
                const input = document.createElement('input');
                input.type = 'text';
                input.value = oldValue;
                input.className = 'form-control form-control-sm';
                input.addEventListener('blur', () => {
                    this.textContent = input.value;
                    this.classList.remove('editing');
                });
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') input.blur();
                });
                this.textContent = '';
                this.appendChild(input);
                input.focus();
            });
        });
    }

    // --- Escape HTML Utility ---
    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // --- Accessibility: Focus visible for keyboard navigation ---
    document.body.addEventListener('keyup', function (e) {
        if (e.key === 'Tab') {
            document.body.classList.add('user-is-tabbing');
        }
    });
    document.body.addEventListener('mousedown', function () {
        document.body.classList.remove('user-is-tabbing');
    });
}); 