<script setup>
import axios from "axios";
defineProps({ stages: { type: Array, required: true } });
const emit = defineEmits(["stage-updated", "error"]);

function formatDuration(s) {
  return s ? `${Math.floor(s / 60)}m ${s % 60}s` : "0s";
}

async function toggleStage(stage) {
  const isRunning = stage.status === "em_andamento";
  const url = `http://127.0.0.1:5000/api/stages/${stage.id}/${
    isRunning ? "stop" : "start"
  }`;
  try {
    const response = await axios.post(url);
    emit("stage-updated", response.data);
  } catch (error) {
    emit("error", error.response?.data?.error || "Ação falhou.");
  }
}

async function stopStage(stageId) {
  try {
    const response = await axios.post(
      `http://127.0.0.1:5000/api/stages/${stageId}/stop`
    );

    // LOG DE DEPURAÇÃO 1: Ver o que estamos enviando para o pai.
    console.log(
      "[ProjectTimeline] Etapa atualizada recebida da API. Emitindo evento com:",
      response.data
    );

    emit("stage-updated", response.data);
  } catch (error) {
    const errorMessage =
      error.response?.data?.error || "Não foi possível parar a etapa.";
    emit("error", errorMessage);
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
        :class="`status-${stage.status}`"
      >
        <div class="status-icon">
          <span>{{ stage.status === "em_andamento" ? "▶️" : "⚪️" }}</span>
        </div>
        <div class="stage-details">
          <strong>{{ stage.name }}</strong>
          <small
            >Duração: {{ formatDuration(stage.total_duration_seconds) }}</small
          >
        </div>
        <div class="stage-actions">
          <button
            @click="toggleStage(stage)"
            :class="stage.status === 'em_andamento' ? 'stop-button' : ''"
          >
            {{ stage.status === "em_andamento" ? "Parar" : "Iniciar" }}
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
/* Estilos podem ser simplificados ou mantidos */
.stage-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
}
.stage-item.status-em_andamento {
  border-left: 5px solid #1e88e5;
}
.status-icon {
  font-size: 1.5rem;
  margin-right: 1rem;
}
.stage-details {
  flex-grow: 1;
}
.stage-details strong {
  font-size: 1.1rem;
}
.stage-details small {
  color: #666;
}
.stage-actions button {
  padding: 0.5rem 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
}
.stage-actions .stop-button {
  background-color: #e53935;
  color: white;
  border-color: #e53935;
}
/* Demais estilos omitidos para simplicidade */
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
</style>
