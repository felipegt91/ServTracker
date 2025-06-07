<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";

const props = defineProps({
  // Recebe o timestamp de início da sessão ATUAL
  startTime: {
    type: Number,
    required: true,
  },
  // NOVA PROP: Recebe a duração total já registrada para esta etapa
  initialDuration: {
    type: Number,
    default: 0,
  },
});

// O estado agora representa o tempo total (duração inicial + tempo da sessão atual)
const totalElapsedSeconds = ref(props.initialDuration);
let timerInterval = null;

const formattedTime = computed(() => {
  const seconds = Math.max(0, totalElapsedSeconds.value);
  const h = Math.floor(seconds / 3600)
    .toString()
    .padStart(2, "0");
  const m = Math.floor((seconds % 3600) / 60)
    .toString()
    .padStart(2, "0");
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${h}:${m}:${s}`;
});

onMounted(() => {
  const startTimestamp = props.startTime;

  if (!startTimestamp) {
    console.error(
      "Não foi encontrado um tempo de início local para o cronômetro."
    );
    return;
  }

  timerInterval = setInterval(() => {
    const nowTimestamp = Date.now();
    const currentSessionSeconds = Math.floor(
      (nowTimestamp - startTimestamp) / 1000
    );

    // AQUI ESTÁ A MUDANÇA: O tempo total é a soma da duração inicial + a da sessão atual
    totalElapsedSeconds.value = props.initialDuration + currentSessionSeconds;
  }, 1000);
});

onUnmounted(() => {
  clearInterval(timerInterval);
});
</script>

<template>
  <div class="active-timer">
    {{ formattedTime }}
  </div>
</template>

<style scoped>
.active-timer {
  font-family: "Courier New", Courier, monospace;
  font-size: 1.2rem;
  font-weight: bold;
  color: #1e88e5; /* Azul do status "em andamento" */
  background-color: #e3f2fd;
  padding: 0.5rem 1rem;
  border-radius: 4px;
}
</style>
