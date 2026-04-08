const apiUrlInput = document.getElementById('api-url');
const uploadUrlInput = document.getElementById('upload-url');
const apiKeyInput = document.getElementById('api-key');
const saveBtn = document.getElementById('save-btn');
const status = document.getElementById('status');

// 页面加载时恢复保存的配置
document.addEventListener('DOMContentLoaded', () => {
  chrome.storage.local.get(['difyApiUrl', 'difyUploadUrl', 'difyApiKey'], (res) => {
    // 设置默认值
    apiUrlInput.value = res.difyApiUrl || 'http://127.0.0.1/v1/chat-messages';
    uploadUrlInput.value = res.difyUploadUrl || 'http://127.0.0.1/v1/files/upload';
    apiKeyInput.value = res.difyApiKey || '';
  });
});

// 保存配置
saveBtn.addEventListener('click', () => {
  const apiUrl = apiUrlInput.value.trim();
  const uploadUrl = uploadUrlInput.value.trim();
  const apiKey = apiKeyInput.value.trim();

  chrome.storage.local.set({
    difyApiUrl: apiUrl,
    difyUploadUrl: uploadUrl,
    difyApiKey: apiKey
  }, () => {
    status.textContent = '配置已保存！你可以关闭此页面了。';
    setTimeout(() => { status.textContent = ''; }, 3000);
  });
});