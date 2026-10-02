/**
 * ComicCraft - Frontend Application Logic
 * Handles real-time stage progress polling, single-panel live regeneration, and sample presets.
 */

document.addEventListener("DOMContentLoaded", () => {
  initStoryInputCharCounter();
  initPresetButtons();
  initProgressTracker();
  initRegenerationModal();
});

// 1. Live Character Counter for Story Idea
function initStoryInputCharCounter() {
  const storyInput = document.getElementById("story_idea");
  const counter = document.getElementById("story_char_counter");
  if (!storyInput || !counter) return;

  const updateCount = () => {
    const len = storyInput.value.trim().length;
    counter.textContent = `${len} / 2000`;
    if (len < 5) {
      counter.classList.add("text-amber-500");
    } else {
      counter.classList.remove("text-amber-500");
    }
  };

  storyInput.addEventListener("input", updateCount);
  updateCount();
}

// 2. Preset Story Loader for Demonstrations
function initPresetButtons() {
  const presets = {
    superhero: {
      story: "A rookie solar engineer in Neo-Metropolis discovers her body can absorb and discharge kinetic energy from falling meteors during an unexpected planetary alignment.",
      genre: "Superhero",
      tone: "Epic / Action-Packed",
      style: "Classic Comic Book (90s Marvel/DC)",
      character: "Aria Thorne",
      setting: "Neo-Metropolis Skylines & Power Grid",
      panels: 4
    },
    scifi: {
      story: "A deep-space scrap collector accidentally salvages a deactivated sentient android that holds the coordinate star-charts to humanity's lost home galaxy.",
      genre: "Sci-Fi",
      tone: "Mysterious",
      style: "Vibrant Modern Webtoon",
      character: "Jax & Unit 73",
      setting: "Orbital Junkyard over Saturn",
      panels: 4
    },
    noir: {
      story: "A weary private investigator in a perpetual rain-drenched megacity takes a case from an anonymous voice on an encrypted rotary telephone.",
      genre: "Noir / Detective",
      tone: "Dark & Gritty",
      style: "Noir Graphic Novel (High Contrast Shadows)",
      character: "Vincent Cross",
      setting: "Rain-soaked Chinatown Alleys",
      panels: 4
    }
  };

  document.querySelectorAll("[data-preset]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const presetKey = btn.getAttribute("data-preset");
      const data = presets[presetKey];
      if (!data) return;

      const storyInput = document.getElementById("story_idea");
      const genreSelect = document.getElementById("genre");
      const toneSelect = document.getElementById("tone");
      const styleSelect = document.getElementById("art_style");
      const charInput = document.getElementById("main_character");
      const settingInput = document.getElementById("setting");
      const panelCountSelect = document.getElementById("panel_count");

      if (storyInput) storyInput.value = data.story;
      if (genreSelect) genreSelect.value = data.genre;
      if (toneSelect) toneSelect.value = data.tone;
      if (styleSelect) styleSelect.value = data.style;
      if (charInput) charInput.value = data.character;
      if (settingInput) settingInput.value = data.setting;
      if (panelCountSelect) panelCountSelect.value = data.panels;

      // Trigger counter update
      if (storyInput) storyInput.dispatchEvent(new Event("input"));
    });
  });
}

// 3. Stage-Based Real-Time Progress Tracker
function initProgressTracker() {
  const trackingContainer = document.getElementById("comic-generation-tracker");
  if (!trackingContainer) return;

  const comicId = trackingContainer.getAttribute("data-comic-id");
  if (!comicId) return;

  const stageOrder = [
    "QUEUED",
    "OUTLINE_GENERATING",
    "STORY_GENERATING",
    "IMAGES_GENERATING",
    "LAYOUT_BUILDING",
    "PDF_GENERATING",
    "COMPLETED"
  ];

  const statusLabel = document.getElementById("current-stage-label");
  const progressBar = document.getElementById("progress-bar-fill");
  const errorAlert = document.getElementById("generation-error-alert");
  const errorMessage = document.getElementById("generation-error-message");

  let pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/comic/${comicId}/status`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (statusLabel) statusLabel.textContent = data.stage_description || "Processing...";
      if (progressBar) progressBar.style.width = `${data.progress_percent}%`;

      // Update stepper icons
      const currentIndex = stageOrder.indexOf(data.status);
      stageOrder.forEach((stageKey, idx) => {
        const stepEl = document.querySelector(`[data-stage="${stageKey}"]`);
        if (!stepEl) return;

        if (idx < currentIndex) {
          stepEl.classList.remove("active");
          stepEl.classList.add("completed");
          const icon = stepEl.querySelector(".step-icon");
          if (icon) icon.innerHTML = "✓";
        } else if (idx === currentIndex) {
          stepEl.classList.add("active");
          stepEl.classList.remove("completed");
          const icon = stepEl.querySelector(".step-icon");
          if (icon) icon.innerHTML = "●";
        } else {
          stepEl.classList.remove("active", "completed");
          const icon = stepEl.querySelector(".step-icon");
          if (icon) icon.innerHTML = (idx + 1).toString();
        }
      });

      if (data.status === "COMPLETED") {
        clearInterval(pollInterval);
        setTimeout(() => {
          window.location.href = `/comic/${comicId}`;
        }, 800);
      } else if (data.status === "FAILED") {
        clearInterval(pollInterval);
        if (errorAlert && errorMessage) {
          errorMessage.textContent = data.error_message || "Generation failed. Please try again.";
          errorAlert.style.display = "block";
        }
      }
    } catch (err) {
      console.warn("Polling error:", err);
    }
  }, 1500);
}

// 4. Panel Regeneration Modal & AJAX Execution
function initRegenerationModal() {
  const modal = document.getElementById("regenerate-modal");
  const openButtons = document.querySelectorAll(".btn-open-regen");
  const closeButtons = document.querySelectorAll(".btn-close-modal");
  const form = document.getElementById("regen-form");

  if (!modal) return;

  openButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const panelNum = btn.getAttribute("data-panel-number");
      const panelSelect = document.getElementById("regen-panel-number");
      if (panelSelect && panelNum) {
        panelSelect.value = panelNum;
      }
      modal.classList.add("open");
    });
  });

  closeButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      modal.classList.remove("open");
    });
  });

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const comicId = form.getAttribute("data-comic-id");
      const panelNumber = parseInt(document.getElementById("regen-panel-number").value, 10);
      const hint = document.getElementById("regen-prompt-hint").value.trim();
      const submitBtn = form.querySelector("button[type='submit']");

      const originalBtnText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = "Rendering Panel...";

      try {
        const response = await fetch(`/comic/${comicId}/regenerate-panel`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            panel_number: panelNumber,
            custom_prompt_hint: hint,
            regenerate_image_only: true
          })
        });

        if (!response.ok) throw new Error("Regeneration failed");
        const data = await response.json();

        // Update panel image dynamically without reloading
        const targetImg = document.querySelector(`[data-panel-img="${panelNumber}"]`);
        if (targetImg && data.image_url) {
          // Add timestamp to defeat browser image cache
          targetImg.src = `${data.image_url}?t=${Date.now()}`;
        }

        modal.classList.remove("open");
        alert(`Panel #${panelNumber} updated successfully!`);
      } catch (err) {
        alert("Failed to regenerate panel. Please try again.");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
      }
    });
  }
}
