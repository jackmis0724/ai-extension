const backendUrlInput = document.getElementById('backend-url');
const apiKeyInput = document.getElementById('api-key');
const aiModelInput = document.getElementById('ai-model');
const saveBtn = document.getElementById('save-btn');
const status = document.getElementById('status');

// 页面加载时恢复保存的配置
document.addEventListener('DOMContentLoaded', () => {
  chrome.storage.local.get(['backendUrl', 'apiKey', 'aiModel'], (res) => {
    // 设置默认值
    backendUrlInput.value = res.backendUrl || 'https://8.156.94.232.nip.io:8000';
    apiKeyInput.value = res.apiKey || '';
    aiModelInput.value = res.aiModel || 'openai';
  });
});

// 保存配置
saveBtn.addEventListener('click', () => {
  const backendUrl = backendUrlInput.value.trim();
  const apiKey = apiKeyInput.value.trim();
  const aiModel = aiModelInput.value;

  // 验证后端地址格式
  if (!backendUrl) {
    status.textContent = '请输入后端服务地址';
    status.style.color = '#dc3545';
    return;
  }

  // 验证API Key
  if (!apiKey) {
    status.textContent = '请输入API Key';
    status.style.color = '#dc3545';
    return;
  }

  // 移除末尾斜杠
  const normalizedUrl = backendUrl.endsWith('/') ? backendUrl.slice(0, -1) : backendUrl;

  chrome.storage.local.set({
    backendUrl: normalizedUrl,
    apiKey: apiKey,
    aiModel: aiModel
  }, () => {
    status.textContent = '配置已保存！你可以关闭此页面了。';
    status.style.color = '#28a745';
    setTimeout(() => { status.textContent = ''; }, 3000);
  });
});
