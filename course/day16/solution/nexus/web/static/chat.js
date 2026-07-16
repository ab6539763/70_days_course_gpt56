const messageList = document.getElementById("messageList");
const chatForm = document.getElementById("chatForm");
const promptInput = document.getElementById("promptInput");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");
const statusEl = document.getElementById("status");
const feedbackEl = document.getElementById("feedback");

function formatError(error) {
  if (!error) {
    return "未知错误";
  }
  if (typeof error === "string") {
    return error;
  }
  if (error.code) {
    return `[${error.code}] ${error.message}`;
  }
  return error.message || String(error);
}

  feedbackEl.textContent = text || "";
  feedbackEl.classList.toggle("error", Boolean(isError));
}

function renderMessages(messages) {
  messageList.innerHTML = "";
  if (!messages || messages.length === 0) {
    const empty = document.createElement("li");
    empty.textContent = "暂无消息，请在右侧输入问题。";
    empty.className = "message-item";
    messageList.appendChild(empty);
    return;
  }
  messages.forEach((item) => {
    const li = document.createElement("li");
    li.className = `message-item ${item.role}`;
    li.innerHTML = `<div class="role">${item.role}</div><div class="content"></div>`;
    li.querySelector(".content").textContent = item.content || item.preview || "";
    messageList.appendChild(li);
  });
  messageList.scrollTop = messageList.scrollHeight;
}

async function loadHealth() {
  const response = await fetch("/api/health");
  const data = await response.json();
  if (!data.ok) {
    statusEl.textContent = `服务异常：${formatError(data.error)}`;
    return;
  }
  statusEl.textContent = `revision=${data.revision}｜model=${data.model}｜trace=${data.trace_id || ""}`;
}

async function loadMessages() {
  const response = await fetch("/api/messages");
  const data = await response.json();
  if (!data.ok) {
    setFeedback(formatError(data.error) || "加载消息失败", true);
    return;
  }
  renderMessages(data.messages);
}

async function sendPrompt(prompt) {
  sendBtn.disabled = true;
  setFeedback("正在请求模型…");
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  const data = await response.json();
  sendBtn.disabled = false;
  if (!data.ok) {
    setFeedback(formatError(data.error) || "发送失败", true);
    return;
  }
  renderMessages(data.messages);
  setFeedback(`已保存 revision=${data.revision}`);
  await loadHealth();
}

async function clearHistory() {
  clearBtn.disabled = true;
  const response = await fetch("/api/clear", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ keep_system: true }),
  });
  const data = await response.json();
  clearBtn.disabled = false;
  if (!data.ok) {
    setFeedback(formatError(data.error) || "清空失败", true);
    return;
  }
  renderMessages(data.messages);
  setFeedback(data.message || "已清空");
  await loadHealth();
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) {
    setFeedback("请输入问题", true);
    return;
  }
  promptInput.value = "";
  await sendPrompt(prompt);
});

clearBtn.addEventListener("click", clearHistory);

promptInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

loadHealth().then(loadMessages).catch((error) => {
  setFeedback(String(error), true);
});
