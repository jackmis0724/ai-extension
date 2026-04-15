// ====== 配置区 ======
let BACKEND_URL = '';
let AI_MODEL = '';

// 获取最新配置
async function updateConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['backendUrl', 'aiModel'], (res) => {
      BACKEND_URL = res.backendUrl || 'http://localhost:8000';
      AI_MODEL = res.aiModel || 'openai';
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

// --- 检查模型是否支持视觉 ---
function isVisionModel(model) {
  // OpenAI GPT-4o-mini 和 Claude 支持视觉，DeepSeek 不支持
  return model === 'openai' || model === 'claude';
}

// --- 截图逻辑 ---
screenshotBtn.addEventListener('click', async () => {
  // 检查当前模型是否支持视觉
  if (!isVisionModel(AI_MODEL)) {
    appendMessage('System', `⚠️ 当前使用的模型（${AI_MODEL}）不支持图片识别功能。\n\n建议：\n• 切换到 OpenAI 或 Claude 模型以使用图片分析\n• 当前模型仅支持文本对话\n\n你可以在设置中切换模型。`);
    return;
  }

  try {
    const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: 'jpeg', quality: 80 });
    setPreview(dataUrl);
  } catch (error) {
    appendMessage("System", "截图失败。");
  }
});

cropBtn.addEventListener('click', async () => {
  // 检查当前模型是否支持视觉
  if (!isVisionModel(AI_MODEL)) {
    appendMessage('System', `⚠️ 当前使用的模型（${AI_MODEL}）不支持图片识别功能。\n\n建议：\n• 切换到 OpenAI 或 Claude 模型以使用图片分析\n• 当前模型仅支持文本对话\n\n你可以在设置中切换模型。`);
    return;
  }

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
async function uploadImage(dataUrl) {
  // 将 dataURL 转换为 Blob
  let arr = dataUrl.split(','), mime = arr[0].match(/:(.*?);/)[1], bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
  while(n--) { u8arr[n] = bstr.charCodeAt(n); }
  const blob = new Blob([u8arr], {type:mime});

  // 创建 FormData
  const formData = new FormData();
  formData.append('file', new File([blob], 'screenshot.jpg', {type:mime}));

  // 上传到后端
  const response = await fetch(`${BACKEND_URL}/api/upload`, {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    throw new Error('图片上传失败');
  }

  const data = await response.json();
  return data.file_id;
}

async function sendMessage() {
  await updateConfig();
  if (!BACKEND_URL) {
    appendMessage('System', '⚠️ 请先配置后端服务地址。');
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

    // 上传图片（如果有）
    let fileId = null;
    if (imageToUpload) {
      fileId = await uploadImage(imageToUpload);
    }

    // 构建请求
    const payload = {
      query: text || "请查看图片",
      page_content: activeContent,
      url: tab.url,
      title: tab.title,
      model: AI_MODEL,
      conversation_id: conversationId || ""
    };

    if (fileId) {
      payload.image_file_id = fileId;
    }

const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`服务器错误: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let fullAnswer = "";

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

          // 处理消息内容
          if (data.event === 'message' && data.content) {
            fullAnswer += data.content;
            aiTextNode.innerHTML = marked.parse(fullAnswer);
            scrollToBottom();
          }

          // 处理思考过程（如果后端支持）
          if (data.event === 'thought') {
            thoughtWrapper.style.display = 'block';
            thoughtWrapper.querySelector('.thought-content').innerHTML = marked.parse(data.content || '');
            scrollToBottom();
          }

          // 处理错误
          if (data.event === 'error') {
            throw new Error(data.error || '未知错误');
          }

          // 消息结束
          if (data.event === 'message_end') {
            chrome.storage.session.set({ conversationId: data.conversation_id, savedUrl: tab.url });
          }
        } catch (e) {
          console.error('解析 SSE 数据出错:', e, line);
        }
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