const backendUrlInput = document.getElementById('backend-url');
const aiModelInput = document.getElementById('ai-model');
const saveBtn = document.getElementById('save-btn');
const status = document.getElementById('status');

// 页面加载时恢复保存的配置
document.addEventListener('DOMContentLoaded', () => {
  chrome.storage.local.get(['backendUrl', 'aiModel'], (res) => {
    // 设置默认值
    backendUrlInput.value = res.backendUrl || 'http://localhost:8000';
    aiModelInput.value = res.aiModel || 'openai';
  });
});

// 保存配置
saveBtn.addEventListener('click', () => {
  const backendUrl = backendUrlInput.value.trim();
  const aiModel = aiModelInput.value;

  // 验证后端地址格式
  if (!backendUrl) {
    status.textContent = '请输入后端服务地址';
    status.style.color = '#dc3545';
    return;
  }

  // 移除末尾斜杠
  const normalizedUrl = backendUrl.endsWith('/') ? backendUrl.slice(0, -1) : backendUrl;

  chrome.storage.local.set({
    backendUrl: normalizedUrl,
    aiModel: aiModel
  }, () => {
    status.textContent = '配置已保存！你可以关闭此页面了。';
    status.style.color = '#28a745';
    setTimeout(() => { status.textContent = ''; }, 3000);
  });
});