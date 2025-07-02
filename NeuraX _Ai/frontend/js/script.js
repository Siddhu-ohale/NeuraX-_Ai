document.addEventListener("DOMContentLoaded", () => {
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // DOM Elements
  const body = document.body;
  const darkToggle = document.getElementById("darkModeToggle");
  const darkIcon = darkToggle.querySelector('i');
  const sendBtn = document.getElementById("sendBtn");
  const chatInput = document.getElementById("chatInput");
  const chatBox = document.getElementById("chatBox");
  const voiceBtn = document.getElementById("voiceBtn");
  const voiceBtnInput = document.getElementById("voiceBtnInput");
  const newChatBtn = document.getElementById("newChatBtn");
  const historyList = document.getElementById("historyList");
  const menuToggle = document.getElementById("menuToggle");
  const sidebar = document.querySelector(".sidebar");
  const sidebarOverlay = document.getElementById("sidebarOverlay");

  // PDF Converter Modal
  const pdfConverterModal = new bootstrap.Modal(document.getElementById('pdfConverterModal'));
  const showPdfConverterBtn = document.getElementById('showPdfConverter');
  const pdfConverterForm = document.getElementById('pdfConverterForm');

  // PDF Converter functionality
  const dropZone = document.getElementById('dropZone');
  const imagePreview = document.getElementById('imagePreview');
  const imageFilesInput = document.getElementById('imageFiles');
  const textConverterForm = document.getElementById('textConverterForm');
  const conversionOptions = document.querySelectorAll('.conversion-option');
  const conversionForms = document.querySelectorAll('.conversion-form');
  const textStyleBtns = document.querySelectorAll('.text-style-btn');
  const fontSizeSelect = document.getElementById('fontSize');

  // Handle drag and drop events
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
  });

  function highlight(e) {
    dropZone.classList.add('dragover');
  }

  function unhighlight(e) {
    dropZone.classList.remove('dragover');
  }

  // Handle dropped files
  dropZone.addEventListener('drop', handleDrop, false);

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
  }

  // Handle click to upload
  dropZone.addEventListener('click', () => {
    imageFilesInput.click();
  });

  imageFilesInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
  });

  function handleFiles(files) {
    imagePreview.innerHTML = ''; // Clear existing previews
    const validImageTypes = ['image/jpeg', 'image/png', 'image/gif'];

    Array.from(files).forEach((file, index) => {
      if (!validImageTypes.includes(file.type)) {
        addMessage('System', `File "${file.name}" is not a supported image type.`);
        return;
      }

      const reader = new FileReader();
      reader.onload = function(e) {
        const previewItem = document.createElement('div');
        previewItem.className = 'preview-item';
        previewItem.innerHTML = `
          <img src="${e.target.result}" alt="Preview">
          <button type="button" class="remove-image" data-index="${index}">
            <i class="bi bi-x"></i>
          </button>
        `;
        imagePreview.appendChild(previewItem);

        // Add remove button functionality
        const removeBtn = previewItem.querySelector('.remove-image');
        removeBtn.addEventListener('click', function() {
          previewItem.remove();
          // Create a new FileList without the removed file
          const dt = new DataTransfer();
          const input = document.getElementById('imageFiles');
          const { files } = input;

          for(let i = 0; i < files.length; i++) {
            if(i !== parseInt(this.dataset.index)) {
              dt.items.add(files[i]);
            }
          }

          input.files = dt.files;
        });
      };
      reader.readAsDataURL(file);
    });

    // Update the file input
    const dt = new DataTransfer();
    Array.from(files).forEach(file => dt.items.add(file));
    imageFilesInput.files = dt.files;
  }

  // Add loading state to convert button during conversion
  pdfConverterForm.addEventListener('submit', function(e) {
    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Converting...`;
    submitBtn.disabled = true;

    // Re-enable button and restore text after conversion (success or error)
    const resetButton = () => {
      submitBtn.innerHTML = originalText;
      submitBtn.disabled = false;
    };

    // Add success/error handlers to the existing form submit logic
    const originalSubmitHandler = e => {
      e.preventDefault();
      const formData = new FormData(pdfConverterForm);

      fetch('/convert-to-pdf', {
        method: 'POST',
        body: formData
      }).then(response => {
        if (response.ok) {
          return response.blob();
        }
        return response.json().then(err => {
          throw new Error(err.error || 'Failed to convert images to PDF');
        });
      }).then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${formData.get('pdf_name')}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        pdfConverterModal.hide();
        addMessage('System', 'PDF has been successfully created and downloaded!');

        // Reset form
        pdfConverterForm.reset();
        imagePreview.innerHTML = '';
      }).catch(error => {
        console.error('Error:', error);
        addMessage('System', `Error: ${error.message}`);
      }).finally(() => {
        resetButton();
      });
    };

    // Call the original submit handler
    originalSubmitHandler(e);
  });

  // Handle conversion type switching
  conversionOptions.forEach(option => {
    option.addEventListener('click', () => {
        // Update active state of options
        conversionOptions.forEach(opt => opt.classList.remove('active'));
        option.classList.add('active');
        
        // Show corresponding form
        const type = option.dataset.type;
        conversionForms.forEach(form => {
            if (form.dataset.type === type) {
                form.classList.add('active');
                form.style.display = 'block';
            } else {
                form.classList.remove('active');
                form.style.display = 'none';
            }
        });
    });
  });

  // Handle text styling buttons
  textStyleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        btn.classList.toggle('active');
    });
  });

  // Handle text to PDF conversion
  textConverterForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const submitBtn = textConverterForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Converting...`;
    submitBtn.disabled = true;

    try {
        const formData = new FormData(textConverterForm);
        
        // Add text styling options
        formData.append('font_size', fontSizeSelect.value);
        textStyleBtns.forEach(btn => {
            const style = btn.dataset.style;
            formData.append(`is_${style}`, btn.classList.contains('active'));
        });

        const response = await fetch('/convert-text-to-pdf', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${formData.get('pdf_name')}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            pdfConverterModal.hide();
            addMessage('System', 'Text has been successfully converted to PDF!');

            // Reset form
            textConverterForm.reset();
            textStyleBtns.forEach(btn => btn.classList.remove('active'));
            fontSizeSelect.value = '14';
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to convert text to PDF');
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('System', `Error: ${error.message}`);
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
  });

  // State Variables
  let recognition;
  let isListening = false;
  let chatHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
  let currentChatId = null;
  let ytPlayers = {};
  let playerCounter = 0;
  let isSidebarOpen = false;

  // Initialize
  initDarkMode();
  renderHistoryList();
  initNewChat();
  setupEventListeners();

  // Functions
  function initDarkMode() {
    if (localStorage.getItem("darkMode") === "true") {
      body.classList.add("dark-mode");
      darkIcon.classList.replace("bi-moon-fill", "bi-sun-fill");
    }
  }

  function renderHistoryList() {
    historyList.innerHTML = '';
    chatHistory.forEach(chat => {
      const li = document.createElement('li');
      li.innerHTML = `
        <span class="history-item">${chat.title}</span>
        <i class="bi bi-trash delete-history" data-id="${chat.id}"></i>
      `;
      
      li.addEventListener('click', (e) => {
        if (!e.target.classList.contains('bi-trash')) {
          loadChat(chat.id);
        }
      });

      historyList.appendChild(li);
    });

    // Add delete event listeners
    document.querySelectorAll('.delete-history').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteChat(e.target.dataset.id);
      });
    });
  }

  function initNewChat() {
    if (chatHistory.length > 0) {
      loadChat(chatHistory[0].id);
    } else {
      newChat();
    }
  }

  function setupEventListeners() {
    // Dark Mode Toggle
    darkToggle.addEventListener("click", toggleDarkMode);
    
    // New Chat Button
    newChatBtn.addEventListener('click', newChat);
    
    // Send Message
    sendBtn.addEventListener("click", () => sendMessage(chatInput.value));
    chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") sendMessage(chatInput.value);
    });
    
    // Voice Recognition
    voiceBtn.addEventListener("click", toggleVoiceRecognition);
    voiceBtnInput.addEventListener("click", toggleVoiceRecognition);
    
    // Menu Items
    document.querySelectorAll('.clickable-menu-item').forEach(item => {
      item.addEventListener('click', function() {
        const command = this.dataset.command;
        sendMessage(command);
      });
    });

    // Mobile Menu Toggle
    menuToggle.addEventListener("click", toggleSidebar);
    sidebarOverlay.addEventListener("click", toggleSidebar);

    // Close sidebar when clicking history item on mobile
    historyList.addEventListener("click", () => {
      if (window.innerWidth <= 768) {
        toggleSidebar();
      }
    });

    // Handle window resize
    window.addEventListener("resize", () => {
      if (window.innerWidth > 768 && isSidebarOpen) {
        toggleSidebar();
      }
    });

    // Close sidebar when clicking outside
    document.addEventListener("click", (e) => {
      if (isSidebarOpen && 
          !sidebar.contains(e.target) && 
          !menuToggle.contains(e.target)) {
        isSidebarOpen = false;
        sidebar.classList.remove("active");
        sidebarOverlay.classList.remove("active");
        document.body.style.overflow = "";
      }
    });

    // Show PDF converter modal
    showPdfConverterBtn.addEventListener('click', () => {
      pdfConverterModal.show();
    });

    // Handle PDF conversion
    pdfConverterForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = new FormData(pdfConverterForm);
      
      try {
          const response = await fetch('/convert-to-pdf', {
              method: 'POST',
              body: formData
          });
          
          if (response.ok) {
              const blob = await response.blob();
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `${formData.get('pdf_name')}.pdf`;
              document.body.appendChild(a);
              a.click();
              window.URL.revokeObjectURL(url);
              document.body.removeChild(a);
              
              // Close modal and show success message
              pdfConverterModal.hide();
              addMessage('System', 'PDF has been successfully created and downloaded!');
          } else {
              const error = await response.json();
              throw new Error(error.error || 'Failed to convert images to PDF');
          }
      } catch (error) {
          console.error('Error:', error);
          addMessage('System', `Error: ${error.message}`);
      }
    });
  }

  function toggleDarkMode() {
    body.classList.toggle("dark-mode");
    if (body.classList.contains("dark-mode")) {
      darkIcon.classList.replace("bi-moon-fill", "bi-sun-fill");
    } else {
      darkIcon.classList.replace("bi-sun-fill", "bi-moon-fill");
    }
    localStorage.setItem("darkMode", body.classList.contains("dark-mode"));
  }

  function toggleSidebar() {
    isSidebarOpen = !isSidebarOpen;
    sidebar.classList.toggle("active");
    sidebarOverlay.classList.toggle("active");
    menuToggle.classList.toggle("active");
    document.body.style.overflow = isSidebarOpen ? "hidden" : "";
  }

  function newChat() {
    currentChatId = null;
    chatBox.innerHTML = `
      <div class="chat-greeting text-center">
        <div class="neurax-logo mb-4">
          <img src="Tatchi ai icon.jpg" alt="NeuraX Bot" class="bot-avatar">
        </div>
        <p class="subtitle-text text-muted">Let's get started. Ask me anything.</p>
      </div>
    `;
    // Stop all YouTube players if any exist
    Object.values(ytPlayers).forEach(player => {
      if (player && typeof player.stopVideo === 'function') {
        player.stopVideo();
      }
    });
    ytPlayers = {};
    playerCounter = 0;
  }

  function loadChat(chatId) {
    const chat = chatHistory.find(c => c.id === chatId);
    if (!chat) return;

    currentChatId = chatId;
    chatBox.innerHTML = '';
    // Stop all YouTube players if any exist
    Object.values(ytPlayers).forEach(player => {
      if (player && typeof player.stopVideo === 'function') {
        player.stopVideo();
      }
    });
    ytPlayers = {};
    playerCounter = 0;
    
    // Recreate chat from history
    const messages = chat.content.split('\n\n');
    messages.forEach(msg => {
      if (msg.includes('User:')) {
        addMessageToChat('User', msg.replace('User:', '').trim(), false);
      } else if (msg.includes('Assistant:')) {
        addMessageToChat('Assistant', msg.replace('Assistant:', '').trim(), false);
      } else if (msg.includes('YouTube:')) {
        const videoId = msg.match(/v=([a-zA-Z0-9_-]+)/)?.[1];
        if (videoId) showYouTubePlayer(videoId, msg.replace('YouTube:', '').trim(), false);
      }
    });
  }

  function deleteChat(chatId) {
    chatHistory = chatHistory.filter(chat => chat.id !== chatId);
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    
    if (currentChatId === chatId) {
      newChat();
    }
    
    renderHistoryList();
  }

  function saveChatToHistory() {
    const chatContent = Array.from(chatBox.children).map(el => {
      if (el.classList.contains('user-message')) {
        return `User: ${el.textContent}`;
      } else if (el.classList.contains('bot-message')) {
        return `Assistant: ${el.textContent}`;
      } else if (el.classList.contains('youtube-message')) {
        const title = el.querySelector('.youtube-title')?.textContent || '';
        const videoId = el.querySelector('.youtube-player-wrapper iframe')?.src.match(/embed\/([a-zA-Z0-9_-]+)/)?.[1];
        return `YouTube: ${title} (v=${videoId})`;
      }
      return '';
    }).filter(Boolean).join('\n\n');

    if (!chatContent.trim()) return;

    const firstMessage = chatBox.querySelector('.user-message, .bot-message');
    const chatTitle = firstMessage ? firstMessage.textContent.slice(0, 50) : 'New Chat';
    const timestamp = new Date().toISOString();

    if (currentChatId) {
      // Update existing chat
      const index = chatHistory.findIndex(chat => chat.id === currentChatId);
      if (index !== -1) {
        chatHistory[index] = {
          id: currentChatId,
          title: chatTitle,
          content: chatContent,
          timestamp
        };
      }
    } else {
      // Create new chat
      currentChatId = Date.now().toString();
      chatHistory.unshift({
        id: currentChatId,
        title: chatTitle,
        content: chatContent,
        timestamp
      });
    }

    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    renderHistoryList();
  }

  function sendMessage(text) {
    if (!text.trim()) return;
    addMessageToChat('User', text);
    chatInput.value = "";
    handleUserMessage(text);
  }

  function addMessageToChat(sender, text, save = true) {
    // Hide greeting if it exists
    const greeting = chatBox.querySelector('.chat-greeting');
    if (greeting) {
        greeting.style.display = 'none';
    }
    
    if (sender === 'Assistant') {
        // First add typing indicator
        const typingIndicator = document.createElement("div");
        typingIndicator.classList.add("typing-indicator");
        typingIndicator.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;
        chatBox.appendChild(typingIndicator);
        chatBox.scrollTop = chatBox.scrollHeight;

        // Create the message div but don't add it yet
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("bot-message");
        
        // Start typing animation after a short delay
        setTimeout(() => {
            // Remove typing indicator
            typingIndicator.remove();
            
            // Add message div to chat
            chatBox.appendChild(msgDiv);
            
            // Convert markdown and start typing animation
            const words = marked.parse(text).split(' ');
            let currentText = '';
            let wordIndex = 0;
            
            function typeNextWord() {
                if (wordIndex < words.length) {
                    currentText += words[wordIndex] + ' ';
                    msgDiv.innerHTML = currentText;
                    msgDiv.classList.add('visible');
                    chatBox.scrollTop = chatBox.scrollHeight;
                    wordIndex++;
                    
                    // Random delay between words (30-50ms)
                    setTimeout(typeNextWord, Math.random() * 20 + 30);
                } else if (save) {
                    saveChatToHistory();
                }
            }
            
            typeNextWord();
        }, 1000);
    } else {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("user-message");
        msgDiv.textContent = text;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        if (save) saveChatToHistory();
    }
  }

  function showYouTubePlayer(videoId, query, save = true) {
    const playerId = `youtube-player-${playerCounter++}`;
    
    // Create container for all YouTube elements
    const youtubeContainer = document.createElement('div');
    youtubeContainer.classList.add('youtube-message');
    
    // Create title element
    const titleDiv = document.createElement('div');
    titleDiv.classList.add('youtube-title');
    titleDiv.textContent = query;
    
    // Create player wrapper
    const playerWrapper = document.createElement('div');
    playerWrapper.classList.add('youtube-player-wrapper');
    
    // Create player element
    const playerElement = document.createElement('div');
    playerElement.id = playerId;
    
    // Create controls
    const controlsDiv = document.createElement('div');
    controlsDiv.classList.add('youtube-controls');
    
    const playBtn = document.createElement('button');
    playBtn.textContent = 'Play';
    playBtn.onclick = () => {
      if (ytPlayers[playerId]) {
        ytPlayers[playerId].playVideo();
      }
    };
    
    const pauseBtn = document.createElement('button');
    pauseBtn.textContent = 'Pause';
    pauseBtn.onclick = () => {
      if (ytPlayers[playerId]) {
        ytPlayers[playerId].pauseVideo();
      }
    };
    
    controlsDiv.appendChild(playBtn);
    controlsDiv.appendChild(pauseBtn);
    
    // Append elements
    playerWrapper.appendChild(playerElement);
    youtubeContainer.appendChild(titleDiv);
    youtubeContainer.appendChild(playerWrapper);
    youtubeContainer.appendChild(controlsDiv);
    chatBox.appendChild(youtubeContainer);
    
    // Initialize YouTube player
    ytPlayers[playerId] = new YT.Player(playerId, {
      height: '100%',
      width: '100%',
      videoId: videoId,
      playerVars: { 
        autoplay: 1,
        modestbranding: 1,
        rel: 0,
        controls: 1
      }
    });
    
    chatBox.scrollTop = chatBox.scrollHeight;
    
    if (save) {
      addMessageToChat('Assistant', `YouTube: ${query} (v=${videoId})`, save);
      const hiddenMsg = document.querySelector('.bot-message:last-child');
      if (hiddenMsg) hiddenMsg.style.display = 'none';
    }
  }

  function toggleVoiceRecognition() {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }

  function startListening() {
    // Check for various Speech Recognition APIs
    window.SpeechRecognition = window.SpeechRecognition || 
                              window.webkitSpeechRecognition ||
                              window.mozSpeechRecognition ||
                              window.msSpeechRecognition;

    function updateMicStatus(status, error = null) {
      const micStatusElements = document.querySelectorAll('.mic-status');
      const micErrorHints = document.querySelectorAll('.mic-error-hint');
      const voiceButtons = [voiceBtn, voiceBtnInput];
      micStatusElements.forEach(el => {
        el.textContent = status;
        el.style.opacity = '1';
      });
      if (error) {
        micErrorHints.forEach(el => {
          el.textContent = error + ' You can type your question below.';
          el.style.opacity = '1';
        });
        voiceButtons.forEach(btn => {
          btn.classList.remove('listening');
          btn.classList.add('error');
        });
        setTimeout(() => {
          voiceButtons.forEach(btn => btn.classList.remove('error'));
          micErrorHints.forEach(el => el.style.opacity = '0');
        }, 4000);
      } else {
        micErrorHints.forEach(el => el.style.opacity = '0');
      }
    }

    // Check for basic browser support
    if (!window.SpeechRecognition) {
      updateMicStatus('Not Available', 'Microphone access is not available.');
      // Always allow user to type their question
      chatInput.focus();
      return;
    }

    // Check for microphone access
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      updateMicStatus('Not Available', 'Microphone access is not available on your device.');
      return;
    }

    // Request microphone permission with optimized audio settings
    navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: 1,
        sampleRate: 44100, // Optimized sample rate
        latency: 0, // Minimize latency
        sampleSize: 16
      } 
    })
      .then(function(stream) {
        // Stop the stream immediately - we just needed permission
        stream.getTracks().forEach(track => track.stop());
        
        try {
          recognition = new window.SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.maxAlternatives = 1; // Reduced for faster processing
          recognition.lang = 'en-US';

          recognition.onstart = () => {
            isListening = true;
            voiceBtn.innerHTML = '<i class="bi bi-mic-mute-fill"></i>';
            voiceBtnInput.innerHTML = '<i class="bi bi-mic-mute-fill"></i>';
            voiceBtn.classList.add('listening');
            voiceBtnInput.classList.add('listening');
            updateMicStatus('Listening...');
            
            // Reduced timeout for faster response
            setTimeout(() => {
              if (isListening) {
                recognition.stop();
                updateMicStatus('No Speech Detected', 'Please try speaking again');
              }
            }, 5000); // Reduced to 5 seconds
          };

          recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            
            // Optimized result processing
            for (let i = event.resultIndex; i < event.results.length; i++) {
              const transcript = event.results[i][0].transcript;
              if (event.results[i].isFinal) {
                finalTranscript = transcript; // Take only the latest final result
                break; // Exit loop early when we have a final result
              } else {
                interimTranscript = transcript; // Take only the latest interim result
              }
            }
            
            // Update input field immediately with interim results
            if (interimTranscript) {
              chatInput.value = interimTranscript;
              chatBox.scrollTop = chatBox.scrollHeight;
            }
            
            // Send message as soon as we have a final result
            if (finalTranscript) {
              chatInput.value = finalTranscript;
              sendMessage(finalTranscript);
              recognition.stop(); // Stop listening after getting final result
            }
          };

          recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            let errorMessage = '';
            
            switch(event.error) {
              case 'network':
                errorMessage = 'Please check your internet connection';
                break;
              case 'not-allowed':
              case 'permission-denied':
                errorMessage = 'Please allow microphone access in your browser settings';
                break;
              case 'no-speech':
                errorMessage = 'No speech was detected. Please try again';
                break;
              case 'audio-capture':
                errorMessage = 'No microphone was found on your device';
                break;
              case 'aborted':
                errorMessage = 'Voice input was cancelled';
                break;
              default:
                errorMessage = 'An error occurred with voice input';
            }
            
            updateMicStatus('Error', errorMessage);
            stopListening();
          };

          recognition.onend = () => {
            if (isListening) {
              // Restart recognition immediately if we were still supposed to be listening
              try {
                recognition.start();
              } catch (e) {
                console.error('Failed to restart recognition:', e);
                stopListening();
              }
            } else {
              voiceBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
              voiceBtnInput.innerHTML = '<i class="bi bi-mic-fill"></i>';
              voiceBtn.classList.remove('listening');
              voiceBtnInput.classList.remove('listening');
              
              // Hide status faster
              document.querySelectorAll('.mic-status').forEach(el => {
                el.style.opacity = '0';
              });
            }
          };

          // Start recognition immediately
          recognition.start();
          updateMicStatus('Listening...');
        } catch (e) {
          console.error('Recognition initialization error:', e);
          updateMicStatus('Init Failed', 'Voice recognition is not available');
        }
      })
      .catch(function(err) {
        console.error('Microphone access error:', err);
        let errorMessage = '';
        
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          errorMessage = 'Please allow microphone access in your browser settings';
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          errorMessage = 'No microphone found on your device';
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
          errorMessage = 'Your microphone may be in use by another app';
        } else {
          errorMessage = 'Could not access microphone';
        }
        
        updateMicStatus('Access Error', errorMessage);
      });
  }

  function stopListening() {
    if (recognition) recognition.stop();
    isListening = false;
    voiceBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
    voiceBtnInput.innerHTML = '<i class="bi bi-mic-fill"></i>';
  }

  async function handleUserMessage(message) {
    try {
      const response = await fetch("/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message })
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      
      // Handle redirect type
      if (data.type === 'redirect') {
        window.open(data.content, '_blank');
        addMessageToChat('Assistant', data.message);
        return;
      }
      
      if (data.type === 'youtube') {
        showYouTubePlayer(data.videoId, data.query);
      } else {
        addMessageToChat('Assistant', data.content);
      }
    } catch (error) {
      console.error("Error:", error);
      let errorMsg = "Sorry, I encountered an error.";
      if (error.message.includes("Failed to fetch")) {
        errorMsg = "Cannot connect to the server. Please check if the backend is running.";
      }
      addMessageToChat('Assistant', errorMsg);
    }
  }
});