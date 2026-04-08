// ====== 配置区 ======
let DIFY_API_URL = '';
let DIFY_UPLOAD_URL = '';
let DIFY_API_KEY = '';

// 获取最新配置
async function updateConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['difyApiUrl', 'difyUploadUrl', 'difyApiKey'], (res) => {
      DIFY_API_URL = res.difyApiUrl || 'http://127.0.0.1/v1/chat-messages';
      DIFY_UPLOAD_URL = res.difyUploadUrl || 'http://127.0.0.1/v1/files/upload';
      DIFY_API_KEY = res.difyApiKey || '';
      resolve();
    });
  });
}
// ====================================

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const cropBtn = document.getElementById('crop-btn');
const screenshotBtn = document.getElementById('screenshot-btn');
const imagePreviewContainer = document.getElementById('image-preview-container');
const imagePreview = document.getElementById('image-preview');
const clearImageBtn = document.getElementById('clear-image-btn');

let currentScreenshot = null; 

// --- 初始化与历史记录 ---
async function init() {
  await updateConfig(); 
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const title = tab?.title || "浏览器助手";

  chrome.storage.session.get(['chatHistory'], (result) => {
    if (result.chatHistory) {
      chatBox.innerHTML = result.chatHistory;
      // 重新绑定历史记录中思考框的点击事件
      bindThoughtEvents();
      scrollToBottom();
    } else {
      appendMessage("AI", `已进入：${title}\n有什么可以帮你的？`);
    }
  });
}

function bindThoughtEvents() {
  document.querySelectorAll('.thought-header').forEach(header => {
    header.onclick = () => header.parentElement.classList.toggle('collapsed');
  });
}

function appendMessage(sender, text, imageDataUrl = null) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${sender === 'User' ? 'user-msg' : 'ai-msg'}`;
  
  if (imageDataUrl) {
    const img = document.createElement('img');
    img.src = imageDataUrl;
    img.style.cssText = "max-width:100%; border-radius:4px; margin-bottom:5px; display:block; cursor:zoom-in;";
    img.onclick = () => window.open(imageDataUrl, '_blank');
    msgDiv.appendChild(img);
  }

  const textNode = document.createElement('div');
  textNode.className = 'markdown-body'; 
  
  if (text) {
    textNode.innerHTML = marked.parse(text);
  }
  msgDiv.appendChild(textNode);
  
  chatBox.appendChild(msgDiv);
  scrollToBottom();
  saveHistory();
  return msgDiv;
}

function scrollToBottom() { chatBox.scrollTop = chatBox.scrollHeight; }
function saveHistory() { chrome.storage.session.set({ chatHistory: chatBox.innerHTML }); }

// --- 截图逻辑 ---
screenshotBtn.addEventListener('click', async () => {
  try {
    const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: 'jpeg', quality: 80 });
    setPreview(dataUrl);
  } catch (error) { appendMessage("System", "截图失败。"); }
});

cropBtn.addEventListener('click', async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['inject_crop.js'] });
  } catch (err) { appendMessage("System", "无法启动局部截图。"); }
});

chrome.runtime.onMessage.addListener(async (message) => {
  if (message.type === 'CROP_AREA_SELECTED') {
    const fullDataUrl = await chrome.tabs.captureVisibleTab(null, { format: 'jpeg', quality: 100 });
    const croppedUrl = await cropImageData(fullDataUrl, message.rect);
    setPreview(croppedUrl);
  }
});

function setPreview(dataUrl) {
  currentScreenshot = dataUrl;
  imagePreview.src = dataUrl;
  imagePreviewContainer.style.display = 'block';
  userInput.focus();
}

clearImageBtn.addEventListener('click', () => {
  currentScreenshot = null;
  imagePreviewContainer.style.display = 'none';
  imagePreview.src = '';
});

async function cropImageData(fullDataUrl, rect) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ratio = window.devicePixelRatio || 1;
      canvas.width = rect.w; canvas.height = rect.h;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, rect.x*ratio, rect.y*ratio, rect.w*ratio, rect.h*ratio, 0, 0, rect.w, rect.h);
      resolve(canvas.toDataURL('image/jpeg', 0.9));
    };
    img.src = fullDataUrl;
  });
}

// --- 发送逻辑 ---
async function uploadImageToDify(dataUrl) {
  let arr = dataUrl.split(','), mime = arr[0].match(/:(.*?);/)[1], bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
  while(n--) { u8arr[n] = bstr.charCodeAt(n); }
  const file = new File([u8arr], 'screenshot.jpg', {type:mime});
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user', 'arch-extension-user');

  const response = await fetch(DIFY_UPLOAD_URL, {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + DIFY_API_KEY },
    body: formData
  });
  const data = await response.json();
  return data.id;
}

async function sendMessage() {
  await updateConfig();
  if (!DIFY_API_KEY) {
    appendMessage('System', '⚠️ 请先配置 API Key。');
    chrome.runtime.openOptionsPage();
    return;
  }

  const text = userInput.value.trim();
  if (!text && !currentScreenshot) return;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  appendMessage('User', text, currentScreenshot);
  const imageToUpload = currentScreenshot;
  
  userInput.value = '';
  sendBtn.disabled = true;
  currentScreenshot = null;
  imagePreviewContainer.style.display = 'none';

  const aiMsgDiv = document.createElement('div');
  aiMsgDiv.className = 'message ai-msg';
  
  const thoughtWrapper = document.createElement('div');
  thoughtWrapper.className = 'thought-wrapper';
  thoughtWrapper.style.display = 'none'; 
  thoughtWrapper.innerHTML = `<div class="thought-header">思考过程</div><div class="thought-content markdown-body"></div>`;
  
  const aiTextNode = document.createElement('div');
  aiTextNode.className = 'markdown-body';
  aiTextNode.innerText = '正在思考...';

  aiMsgDiv.appendChild(thoughtWrapper);
  aiMsgDiv.appendChild(aiTextNode);
  chatBox.appendChild(aiMsgDiv);
  scrollToBottom();

  thoughtWrapper.querySelector('.thought-header').onclick = () => thoughtWrapper.classList.toggle('collapsed');

  try {
    let activeContent = "";
    try {
      const injection = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: () => document.body.innerText });
      activeContent = injection[0].result || "";
    } catch (e) {}

    let { conversationId, savedUrl } = await chrome.storage.session.get(['conversationId', 'savedUrl']);
    if (savedUrl !== tab.url) { conversationId = ""; }

    const payload = {
      inputs: { page_content: activeContent, url: tab.url, title: tab.title },
      query: text || "请查看图片",
      response_mode: "streaming",
      conversation_id: conversationId || "",
      user: "arch-extension-user",
      files: []
    };

    if (imageToUpload) {
      const fileId = await uploadImageToDify(imageToUpload);
      payload.files.push({ type: "image", transfer_method: "local_file", upload_file_id: fileId });
    }

    const response = await fetch(DIFY_API_URL, {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + DIFY_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = ""; 
    let fullRawAnswer = ""; // 核心：用于解析标签的累计文本
    
    aiTextNode.innerText = ""; 

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); 

      for (const line of lines) {
        if (!line.trim() || !line.startsWith('data:')) continue;
        try {
          const data = JSON.parse(line.substring(5));
          
          // 1. 处理显式的 thought 事件 (Dify 标准)
          if (data.event === 'thought') {
            thoughtWrapper.style.display = 'block';
            const currentThought = thoughtWrapper.querySelector('.thought-content').innerHTML;
            thoughtWrapper.querySelector('.thought-content').innerHTML = marked.parse((data.thought_accumulated || data.thought));
            scrollToBottom();
          } 
          
          // 2. 处理包含在 answer 里的 <think> 标签 (你的情况)
          else if (data.event === 'message') {
            fullRawAnswer += (data.answer || "");

            if (fullRawAnswer.includes('<think>')) {
              thoughtWrapper.style.display = 'block';
              
              const parts = fullRawAnswer.split('</think>');
              if (parts.length > 1) {
                // 思考已结束
                const thoughtText = parts[0].replace('<think>', '');
                const finalAnswer = parts[1];
                
                thoughtWrapper.querySelector('.thought-content').innerHTML = marked.parse(thoughtText);
                aiTextNode.innerHTML = marked.parse(finalAnswer);
                
                // 首次检测到结束时自动折叠
                if (!thoughtWrapper.classList.contains('collapsed') && finalAnswer.length > 0) {
                   thoughtWrapper.classList.add('collapsed');
                }
              } else {
                // 正在思考中
                const thoughtInProgress = fullRawAnswer.replace('<think>', '');
                thoughtWrapper.querySelector('.thought-content').innerHTML = marked.parse(thoughtInProgress);
              }
            } else {
              // 普通消息
              aiTextNode.innerHTML = marked.parse(fullRawAnswer);
            }
            scrollToBottom();
          } 
          else if (data.event === 'message_end') {
            chrome.storage.session.set({ conversationId: data.conversation_id, savedUrl: tab.url });
          }
        } catch (e) {}
      }
    }
  } catch (error) {
    aiTextNode.innerText = `错误: ${error.message}`;
  } finally {
    sendBtn.disabled = false;
    userInput.focus();
    saveHistory();
  }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
window.addEventListener('load', () => setTimeout(() => userInput.focus(), 100));
init();