<script setup>
import { formatDuration } from "@/utils/formatters.js";
import { ref, onMounted } from "vue"; // O 'computed' não é mais necessário aqui
import axios from "axios";
import ActiveTimer from "./ActiveTimer.vue";

defineProps({
  stages: { type: Array, required: true },
});

const emit = defineEmits(["stage-updated", "error"]);

// ESTA É A MUDANÇA PRINCIPAL:
// Criamos uma variável de estado local para o tempo de início do timer.
// Ela é inicializada com o valor do localStorage, caso o usuário atualize a página.
const activeTimerStartTime = ref(
  Number(localStorage.getItem("activeTimerStart")) || null
);

async function startStage(stageId) {
  try {
    const response = await axios.post(
      `http://127.0.0.1:5000/api/stages/${stageId}/start`
    );

    // Atualizamos nosso estado local e o localStorage ao mesmo tempo.
    const now = Date.now();
    localStorage.setItem("activeTimerStart", now);
    activeTimerStartTime.value = now;

    emit("stage-updated", response.data);
  } catch (error) {
    emit(
      "error",
      error.response?.data?.error || "Não foi possível iniciar/retomar a etapa."
    );
  }
}

async function stopStage(stageId) {
  try {
    const response = await axios.post(
      `http://127.0.0.1:5000/api/stages/${stageId}/stop`
    );

    // Limpamos nosso estado local e o localStorage.
    localStorage.removeItem("activeTimerStart");
    activeTimerStartTime.value = null;

    emit("stage-updated", response.data);
  } catch (error) {
    emit(
      "error",
      error.response?.data?.error || "Não foi possível parar a etapa."
    );
  }
}

async function completeStage(stageId) {
  if (
    !confirm(
      "Você tem certeza que deseja finalizar esta etapa? Esta ação não pode ser desfeita."
    )
  )
    return;
  try {
    const response = await axios.post(
      `http://127.0.0.1:5000/api/stages/${stageId}/complete`
    );

    // Limpamos nosso estado local e o localStorage por segurança.
    localStorage.removeItem("activeTimerStart");
    activeTimerStartTime.value = null;

    emit("stage-updated", response.data);
  } catch (error) {
    emit(
      "error",
      error.response?.data?.error || "Não foi possível finalizar a etapa."
    );
  }
}
</script>

<template>
  <div class="timeline-container">
    <h2>Andamento do Projeto</h2>
    <ul class="stages-list">
      <li
        v-for="stage in stages"
        :key="stage.id"
        class="stage-item"
        :class="`status-${stage.status}`"
      >
        <div class="status-icon">
          <span v-if="stage.status === 'nao_iniciada'">⚪️</span>
          <span v-if="stage.status === 'em_andamento'">▶️</span>
          <span v-if="stage.status === 'pausada'">⏸️</span>
          <span v-if="stage.status === 'finalizada'">✅</span>
        </div>
        <div class="stage-details">
          <strong>{{ stage.name }}</strong>
          <small
            >Duração: {{ formatDuration(stage.total_duration_seconds) }}</small
          >
          <div class="timer-wrapper" v-if="stage.status === 'em_andamento'">
            <ActiveTimer
              v-if="activeTimerStartTime"
              :start-time="activeTimerStartTime"
              :initial-duration="stage.total_duration_seconds"
            />
          </div>
        </div>
        <div class="stage-actions">
          <button
            v-if="stage.status === 'nao_iniciada'"
            @click="startStage(stage.id)"
          >
            Iniciar
          </button>
          <button
            v-if="stage.status === 'pausada'"
            class="resume-button"
            @click="startStage(stage.id)"
          >
            Retomar
          </button>
          <button
            v-if="stage.status === 'em_andamento'"
            class="stop-button"
            @click="stopStage(stage.id)"
          >
            Parar
          </button>
          <button
            v-if="stage.status === 'em_andamento' || stage.status === 'pausada'"
            class="complete-button"
            @click="completeStage(stage.id)"
          >
            Finalizar Etapa
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
/* Estilos permanecem os mesmos */
.stage-item.status-pausada {
  border-left: 5px solid #fdd835;
}
.stage-actions .resume-button {
  background-color: #1e88e5;
}
.timeline-container {
  margin-top: 2rem;
  padding: 1.5rem;
  background-color: #fff;
  border-radius: 8px;
}
h2 {
  margin-bottom: 1.5rem;
  text-align: center;
}
.stages-list {
  list-style-type: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.stage-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border: 1px solid var(--cor-borda);
  border-radius: 6px;
  transition: background-color 0.3s;
}
.stage-item.status-finalizada {
  background-color: #f0f4f0;
  color: #888;
  border-left: 5px solid #4caf50;
}
.status-icon {
  font-size: 1.5rem;
  margin-right: 1rem;
}
.stage-details {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}
.stage-details strong {
  font-size: 1.1rem;
  margin-bottom: 0.25rem;
}
.stage-details small {
  color: #666;
}
.stage-actions {
  display: flex;
  gap: 0.5rem;
}
.stage-actions button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 700;
  background-color: var(--cor-primaria-acao);
  color: #fff;
}
.stage-actions .stop-button {
  background-color: #e53935;
}
.stage-actions .complete-button {
  background-color: #757575;
}
.timer-wrapper {
  margin-top: 0.5rem;
}
</style>
