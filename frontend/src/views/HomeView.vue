<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import ProjectTimeline from "@/components/ProjectTimeline.vue";

const clients = ref([]);
const clientProjects = ref([]);
const stages = ref([]);
const selectedClient = ref(null);
const selectedProject = ref(null);
const isLoading = ref({ clients: false, projects: false, stages: false });
const error = ref(null);

async function fetchClients() {
  isLoading.value.clients = true;
  try {
    const response = await axios.get("http://127.0.0.1:5000/api/clients");
    clients.value = response.data;
  } catch (err) {
    handleError("Não foi possível carregar os clientes.");
  } finally {
    isLoading.value.clients = false;
  }
}

async function onClientChange() {
  if (!selectedClient.value) return;
  clientProjects.value = [];
  stages.value = [];
  selectedProject.value = null;
  isLoading.value.projects = true;
  try {
    const response = await axios.get(
      `http://127.0.0.1:5000/api/clients/${selectedClient.value.id}/projects`
    );
    clientProjects.value = response.data;
  } catch (err) {
    handleError("Não foi possível carregar os projetos deste cliente.");
  } finally {
    isLoading.value.projects = false;
  }
}

async function onProjectChange() {
  if (!selectedProject.value) return;
  stages.value = [];
  isLoading.value.stages = true;
  try {
    const response = await axios.get(
      `http://127.0.0.1:5000/api/projects/${selectedProject.value.id}/stages`
    );
    stages.value = response.data;
  } catch (err) {
    handleError("Não foi possível carregar as etapas deste projeto.");
  } finally {
    isLoading.value.stages = false;
  }
}

function handleError(message) {
  error.value = message;
  setTimeout(() => {
    error.value = null;
  }, 5000);
}

function updateStageInList(updatedStage) {
  // Encontra o índice do item a ser atualizado.
  const index = stages.value.findIndex((stage) => stage.id === updatedStage.id);

  // Se o item for encontrado...
  if (index !== -1) {
    // Usa .splice() para remover o item antigo e inserir o novo no mesmo lugar.
    // Esta é uma mutação direta que o Vue detecta de forma muito eficaz.
    stages.value.splice(index, 1, updatedStage);
  }
}

onMounted(fetchClients);
</script>

<template>
  <div class="container">
    <header><h1>ServTracker</h1></header>
    <main>
      <section class="selection-area">
        <div class="form-group">
          <label for="client-select">1. Selecione o Cliente:</label>
          <select
            id="client-select"
            v-model="selectedClient"
            @change="onClientChange"
            :disabled="isLoading.clients"
          >
            <option :value="null" disabled>
              {{
                isLoading.clients ? "Carregando..." : "-- Escolha um cliente --"
              }}
            </option>
            <option v-for="client in clients" :key="client.id" :value="client">
              {{ client.name }}
            </option>
          </select>
        </div>
        <div v-if="selectedClient" class="form-group">
          <label for="project-select">2. Selecione o Projeto:</label>
          <select
            id="project-select"
            v-model="selectedProject"
            @change="onProjectChange"
            :disabled="isLoading.projects"
          >
            <option :value="null" disabled>
              {{
                isLoading.projects
                  ? "Carregando..."
                  : clientProjects.length === 0
                  ? "Nenhum projeto encontrado"
                  : "-- Escolha um projeto --"
              }}
            </option>
            <option
              v-for="project in clientProjects"
              :key="project.id"
              :value="project"
            >
              {{ project.name }}
            </option>
          </select>
        </div>
      </section>

      <div v-if="isLoading.stages" style="text-align: center">
        Carregando andamento...
      </div>
      <ProjectTimeline
        v-else-if="stages.length > 0"
        :stages="stages"
        @stage-updated="updateStageInList"
        @error="handleError"
      />
      <div v-if="error" class="error-message">
        <p>{{ error }}</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.container {
  max-width: 800px;
  margin: 40px auto;
  padding: 2rem;
  font-family: sans-serif;
  color: #2c3e50;
}
header {
  text-align: center;
  margin-bottom: 2rem;
}
.selection-area {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
.form-group {
  display: flex;
  flex-direction: column;
}
.form-group label {
  margin-bottom: 0.5rem;
  font-weight: 700;
  color: #34495e;
}
.form-group select {
  padding: 0.75rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: #fff;
}
.error-message {
  margin-top: 1.5rem;
  text-align: center;
  padding: 1rem;
  background-color: #ffcdd2;
  border-left: 5px solid #f44336;
  color: #c62828;
  border-radius: 4px;
}
</style>
