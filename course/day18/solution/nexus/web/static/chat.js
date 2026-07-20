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

function setFeedback(text, isError = false) {
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

function ensureStreamingAssistantBubble() {
  let node = document.getElementById("streamingAssistant");
  if (node) {
    return node.querySelector(".content");
  }
  const li = document.createElement("li");
  li.id = "streamingAssistant";
  li.className = "message-item assistant streaming";
  li.innerHTML = `<div class="role">assistant</div><div class="content"></div>`;
  messageList.appendChild(li);
  messageList.scrollTop = messageList.scrollHeight;
  return li.querySelector(".content");
}

function removeStreamingAssistantBubble() {
  const node = document.getElementById("streamingAssistant");
  if (node) {
    node.remove();
  }
}

function parseSseBlock(block) {
  const lines = block.split("\n");
  let eventName = "message";
  let dataLine = "";
  lines.forEach((line) => {
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLine = line.slice(5).trim();
    }
  });
  if (!dataLine) {
    return null;
  }
  return { event: eventName, data: JSON.parse(dataLine) };
}

function consumeSseBuffer(buffer) {
  const parts = buffer.split("\n\n");
  const remaining = parts.pop() || "";
  const events = [];
  parts.forEach((block) => {
    if (!block.trim()) {
      return;
    }
    try {
      const parsed = parseSseBlock(block);
      if (parsed) {
        events.push(parsed);
      }
    } catch (error) {
      throw new Error(`SSE 解析失败：${error.message}`);
    }
  });
  return { events, remaining };
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
  setFeedback("正在流式请求模型…");
  removeStreamingAssistantBubble();
  const contentEl = ensureStreamingAssistantBubble();
  let assistantText = "";
  let donePayload = null;

  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });

  const contentType = response.headers.get("Content-Type") || "";
  if (!response.ok || !contentType.includes("text/event-stream")) {
    sendBtn.disabled = false;
    removeStreamingAssistantBubble();
    let message = "发送失败";
    try {
      const data = await response.json();
      message = formatError(data.error) || message;
    } catch (error) {
      message = `HTTP ${response.status}`;
    }
    setFeedback(message, true);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const parsed = consumeSseBuffer(buffer);
    buffer = parsed.remaining;
    parsed.events.forEach((item) => {
      if (item.event === "chunk" && item.data.delta) {
        assistantText += item.data.delta;
        contentEl.textContent = assistantText;
        messageList.scrollTop = messageList.scrollHeight;
      } else if (item.event === "done") {
        donePayload = item.data;
      } else if (item.event === "error") {
        throw new Error(formatError(item.data.error) || "流式错误");
      }
    });
  }

  sendBtn.disabled = false;
  removeStreamingAssistantBubble();

  if (!donePayload || !donePayload.ok) {
    setFeedback("流式响应未完成", true);
    await loadMessages();
    return;
  }

  renderMessages(donePayload.messages);
  const windowHint = donePayload.window && donePayload.window.window_applied
    ? `｜窗口 ${donePayload.window.non_system_sent}/${donePayload.window.non_system_total} 条`
    : "";
  setFeedback(`流式完成 revision=${donePayload.revision}${windowHint}`);
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
  try {
    await sendPrompt(prompt);
  } catch (error) {
    sendBtn.disabled = false;
    removeStreamingAssistantBubble();
    setFeedback(String(error), true);
    await loadMessages();
  }
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
