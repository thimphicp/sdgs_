const API_BASE_URL = window.SDGS_API_BASE_URL || "http://127.0.0.1:8090";
const ANALYZE_URL = `${API_BASE_URL}/analyze`;
const ASK_URL = `${API_BASE_URL}/ask`;
const USE_MOCK_WHEN_API_NOT_READY = false;

const uploadForm = document.querySelector("#uploadForm");
const imageInput = document.querySelector("#imageInput");
const dropZone = document.querySelector("#dropZone");
const previewWrap = document.querySelector("#previewWrap");
const previewImage = document.querySelector("#previewImage");
const removeImageButton = document.querySelector("#removeImage");
const submitButton = document.querySelector("#submitButton");
const followupPanel = document.querySelector("#followupPanel");
const followupInput = document.querySelector("#followupInput");
const followupButton = document.querySelector("#followupButton");

const emptyState = document.querySelector("#emptyState");
const loadingState = document.querySelector("#loadingState");
const errorState = document.querySelector("#errorState");
const resultState = document.querySelector("#resultState");
const errorMessage = document.querySelector("#errorMessage");
const foodName = document.querySelector("#foodName");
const confidenceValue = document.querySelector("#confidenceValue");
const sdgList = document.querySelector("#sdgList");
const questionCard = document.querySelector("#questionCard");
const userQuestion = document.querySelector("#userQuestion");
const followupAnswer = document.querySelector("#followupAnswer");
const sdgMessageTitle = document.querySelector("#sdgMessageTitle");
const sdgMessage = document.querySelector("#sdgMessage");

let selectedFile = null;
let previewUrl = null;
let latestAnalysis = null;
let followupUsed = false;

imageInput.addEventListener("change", () => {
  const [file] = imageInput.files;
  setSelectedFile(file);
});

removeImageButton.addEventListener("click", () => {
  imageInput.value = "";
  setSelectedFile(null);
});

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("is-dragging");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("is-dragging");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("is-dragging");

  const [file] = event.dataTransfer.files;
  if (!file) return;

  if (!file.type.startsWith("image/")) {
    showError("이미지 파일만 업로드할 수 있어요.");
    return;
  }

  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  imageInput.files = dataTransfer.files;
  setSelectedFile(file);
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!selectedFile) {
    showError("먼저 음식 사진을 선택해 주세요.");
    return;
  }

  showState("loading");
  submitButton.disabled = true;

  try {
    const result = await analyzeImage(selectedFile);
    renderResult(result);
  } catch (error) {
    showError(error.message || "분석 중 문제가 발생했어요.");
  } finally {
    submitButton.disabled = !selectedFile;
  }
});

followupButton.addEventListener("click", async () => {
  const question = followupInput.value.trim();

  if (!latestAnalysis) {
    showError("먼저 음식 사진을 분석해 주세요.");
    return;
  }

  if (!question) {
    showError("추가 질문을 입력해 주세요.");
    return;
  }

  if (followupUsed) {
    showError("추가 질문은 분석 1번당 한 번만 할 수 있어요.");
    return;
  }

  followupButton.disabled = true;
  followupButton.textContent = "질문 보내는 중...";

  try {
    const answer = await askFollowupQuestion(question, latestAnalysis);
    renderFollowupAnswer(question, answer);
  } catch (error) {
    showError(error.message || "추가 질문 처리 중 문제가 발생했어요.");
  } finally {
    if (!followupUsed) {
      followupButton.disabled = false;
      followupButton.textContent = "추가질문하기";
    }
  }
});

function setSelectedFile(file) {
  selectedFile = file || null;
  submitButton.disabled = !selectedFile;

  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = null;
  }

  if (!selectedFile) {
    previewWrap.classList.add("hidden");
    dropZone.classList.remove("hidden");
    latestAnalysis = null;
    followupUsed = false;
    unlockFollowupInput();
    followupPanel.classList.add("hidden");
    showState("empty");
    return;
  }

  latestAnalysis = null;
  followupUsed = false;
  unlockFollowupInput();
  followupInput.value = "";
  questionCard.classList.add("hidden");
  followupPanel.classList.add("hidden");
  previewUrl = URL.createObjectURL(selectedFile);
  previewImage.src = previewUrl;
  previewWrap.classList.remove("hidden");
  dropZone.classList.add("hidden");
  showState("empty");
}

async function analyzeImage(file) {
  if (USE_MOCK_WHEN_API_NOT_READY) {
    await wait(900);
    return createMockResult(file.name);
  }

  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch(ANALYZE_URL, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "서버가 분석 요청을 처리하지 못했어요."));
  }

  return response.json();
}

async function askFollowupQuestion(question, analysis) {
  if (USE_MOCK_WHEN_API_NOT_READY) {
    await wait(700);
    return createMockFollowupAnswer(question, analysis);
  }

  const response = await fetch(ASK_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
    }),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "LLM이 추가 질문을 처리하지 못했어요."));
  }

  const result = await response.json();
  return result.answer || result.message || "추가 답변을 받았지만 표시할 문장이 없어요.";
}

function renderResult(result) {
  const confidence = Number(result.confidence ?? 0);
  const sdgs = Array.isArray(result.sdgs) ? result.sdgs : [];

  latestAnalysis = result;
  followupUsed = false;
  unlockFollowupInput();
  foodName.textContent = result.food || "알 수 없는 음식";
  confidenceValue.textContent = `${Math.round(confidence * 100)}%`;
  sdgMessage.textContent =
    result.message ||
    "이 음식은 건강한 식생활과 지속가능한 소비 관점에서 SDGs와 연결해 설명할 수 있어요.";

  sdgList.innerHTML = "";
  sdgs.forEach((sdg) => {
    const item = document.createElement("span");
    item.className = "sdg-pill";
    item.textContent = sdg;
    sdgList.append(item);
  });

  if (sdgs.length === 0) {
    const item = document.createElement("span");
    item.className = "sdg-pill";
    item.textContent = "SDG 12";
    sdgList.append(item);
  }

  followupPanel.classList.remove("hidden");
  questionCard.classList.add("hidden");
  sdgMessageTitle.textContent = "SDGs 설명";
  showState("result");
}

function renderFollowupAnswer(question, answer) {
  followupUsed = true;
  userQuestion.textContent = question;
  followupAnswer.textContent = answer;
  sdgMessageTitle.textContent = "처음 분석한 SDGs 설명";
  lockFollowupInput();
  questionCard.classList.remove("hidden");
  showState("result");
}

function lockFollowupInput() {
  followupInput.disabled = true;
  followupButton.disabled = true;
  followupButton.textContent = "추가질문 완료";
}

function unlockFollowupInput() {
  followupInput.disabled = false;
  followupButton.disabled = false;
  followupButton.textContent = "추가질문하기";
}

function showError(message) {
  errorMessage.textContent = message;
  showState("error");
}

function showState(state) {
  emptyState.classList.toggle("hidden", state !== "empty");
  loadingState.classList.toggle("hidden", state !== "loading");
  errorState.classList.toggle("hidden", state !== "error");
  resultState.classList.toggle("hidden", state !== "result");
}

async function getErrorMessage(response, fallbackMessage) {
  try {
    const result = await response.json();
    return result.detail || result.message || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

function createMockResult(fileName) {
  const lowerName = fileName.toLowerCase();
  const isRice = lowerName.includes("rice") || lowerName.includes("bap");
  const food = isRice ? "볶음밥" : "김치볶음밥";

  return {
    food,
    confidence: 0.91,
    sdgs: ["SDG 3", "SDG 12", "SDG 13"],
    message:
      `${food}은 한 끼 식사로 활용하기 좋고, 남은 채소나 밥을 사용하면 음식물 쓰레기를 줄이는 SDG 12와 연결됩니다. ` +
      "나트륨과 기름 사용량을 조절하면 건강한 식생활을 다루는 SDG 3에도 맞출 수 있고, 식재료 낭비를 줄이는 선택은 기후 행동인 SDG 13과도 이어집니다.",
  };
}

function createMockFollowupAnswer(question, analysis) {
  return `"${question}"에 대한 답변입니다. ${analysis.food}은 현재 분석 결과에서 ${analysis.sdgs.join(", ")}와 연결되어 있습니다. 특히 음식물 낭비를 줄이는 방식으로 먹거나 남은 재료를 활용하면 SDG 12와 연결되고, 영양 균형을 고려하면 SDG 3 관점에서도 설명할 수 있습니다.`;
}

function wait(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}
