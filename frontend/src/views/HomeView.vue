<script setup>
import { ref, onMounted, computed, reactive } from "vue";
import axios from "axios";
import ProjectTimeline from "@/components/ProjectTimeline.vue";
import { formatDuration } from "@/utils/formatters.js";

// --- ESTADO DA PÁGINA ---
const clients = ref([]);
const clientProjects = ref([]);
const stages = ref([]);
const selectedClient = ref(null);
const selectedProject = ref(null);
const isLoading = ref({ clients: false, projects: false, stages: false });
const error = ref(null);

// --- ESTADO DOS MODAIS ---
const isAddClientModalOpen = ref(false);
const newClient = ref({ name: "", contact_person: "" });
const isAddProjectModalOpen = ref(false);
const newProject = ref({ name: "" });
const isEditClientModalOpen = ref(false);
const editingClient = ref(null);

// --- PROPRIEDADE COMPUTADA ---
const totalProjectTimeSeconds = computed(() => {
  if (!stages.value || stages.value.length === 0) return 0;
  return stages.value.reduce(
    (total, stage) => total + stage.total_duration_seconds,
    0
  );
});

// --- FUNÇÕES DE LÓGICA PRINCIPAL ---
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
  const index = stages.value.findIndex((stage) => stage.id === updatedStage.id);
  if (index !== -1) {
    stages.value.splice(index, 1, reactive(updatedStage));
  }
}

// --- FUNÇÕES DO MODAL DE CLIENTE ---
function openAddClientModal() {
  isAddClientModalOpen.value = true;
}

function closeAddClientModal() {
  isAddClientModalOpen.value = false;
  newClient.value = { name: "", contact_person: "" };
}

async function saveNewClient() {
  if (!newClient.value.name.trim()) {
    handleError("O nome do cliente não pode estar em branco.");
    return;
  }
  try {
    await axios.post("http://127.0.0.1:5000/api/clients", newClient.value);
    closeAddClientModal();
    await fetchClients();
  } catch (err) {
    handleError(err.response?.data?.error || "Erro ao salvar novo cliente.");
  }
}

// --- FUNÇÕES DO MODAL DE EDIÇÃO DE CLIENTE ---
function openEditClientModal() {
  if (!selectedClient.value) return;
  editingClient.value = { ...selectedClient.value };
  isEditClientModalOpen.value = true;
}

function closeEditClientModal() {
  isEditClientModalOpen.value = false;
  editingClient.value = null;
}

async function updateClient() {
  if (!editingClient.value || !editingClient.value.name.trim()) {
    handleError("O nome do cliente não pode estar em branco.");
    return;
  }
  try {
    const previouslySelectedClientId = selectedClient.value.id;
    const previouslySelectedProjectId = selectedProject.value
      ? selectedProject.value.id
      : null;

    await axios.put(
      `http://127.0.0.1:5000/api/clients/${editingClient.value.id}`,
      editingClient.value
    );

    closeEditClientModal();
    await fetchClients();

    selectedClient.value =
      clients.value.find((c) => c.id === previouslySelectedClientId) || null;
    if (selectedClient.value) {
      await onClientChange();
      if (previouslySelectedProjectId) {
        selectedProject.value =
          clientProjects.value.find(
            (p) => p.id === previouslySelectedProjectId
          ) || null;
      }
    }
  } catch (err) {
    handleError(err.response?.data?.error || "Erro ao atualizar o cliente.");
  }
}

// --- FUNÇÕES DO MODAL DE PROJETO ---
function openAddProjectModal() {
  isAddProjectModalOpen.value = true;
}

function closeAddProjectModal() {
  isAddProjectModalOpen.value = false;
  newProject.value = { name: "" };
}

async function saveNewProject() {
  if (!newProject.value.name.trim() || !selectedClient.value) {
    handleError("Nome do projeto e cliente são necessários.");
    return;
  }
  try {
    const payload = {
      name: newProject.value.name,
      client_id: selectedClient.value.id,
    };
    await axios.post("http://127.0.0.1:5000/api/projects", payload);

    closeAddProjectModal();
    await onClientChange();
  } catch (err) {
    handleError(err.response?.data?.error || "Erro ao salvar novo projeto.");
  }
}

// --- HOOK DE CICLO DE VIDA ---
onMounted(() => {
  fetchClients();
});
</script>

<template>
  <div class="container">
    <header>
      <h1>ServTracker</h1>
    </header>

    <main>
      <section class="selection-area">
        <div class="form-group">
          <div class="label-with-button">
            <label for="client-select">1. Selecione o Cliente:</label>
            <div>
              <button
                v-if="selectedClient"
                @click="openEditClientModal"
                class="add-new-button edit-button"
              >
                Editar
              </button>
              <button @click="openAddClientModal" class="add-new-button">
                + Novo Cliente
              </button>
            </div>
          </div>
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
          <div class="label-with-button">
            <label for="project-select">2. Selecione o Projeto:</label>
            <button @click="openAddProjectModal" class="add-new-button">
              + Novo Projeto
            </button>
          </div>
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

      <section v-if="stages.length > 0" class="project-header">
        <h3>Tempo Total no Projeto</h3>
        <div class="total-time-display">
          {{ formatDuration(totalProjectTimeSeconds) }}
        </div>
      </section>

      <ProjectTimeline
        v-if="stages.length > 0"
        :stages="stages"
        @stage-updated="updateStageInList"
        @error="handleError"
      />

      <div v-if="error" class="error-message">
        <p>{{ error }}</p>
      </div>
    </main>

    <div
      v-if="isAddClientModalOpen"
      class="modal-overlay"
      @click.self="closeAddClientModal"
    >
      <div class="modal-content">
        <h2>Adicionar Novo Cliente</h2>
        <form @submit.prevent="saveNewClient">
          <div class="form-group">
            <label for="new-client-name">Nome do Cliente</label>
            <input
              type="text"
              id="new-client-name"
              v-model="newClient.name"
              required
            />
          </div>
          <div class="form-group">
            <label for="new-client-contact">Pessoa de Contato (Opcional)</label>
            <input
              type="text"
              id="new-client-contact"
              v-model="newClient.contact_person"
            />
          </div>
          <div class="modal-actions">
            <button
              type="button"
              class="button-secondary"
              @click="closeAddClientModal"
            >
              Cancelar
            </button>
            <button type="submit" class="button-primary">Salvar Cliente</button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="isEditClientModalOpen"
      class="modal-overlay"
      @click.self="closeEditClientModal"
    >
      <div class="modal-content">
        <h2>Editar Cliente</h2>
        <form v-if="editingClient" @submit.prevent="updateClient">
          <div class="form-group">
            <label for="edit-client-name">Nome do Cliente</label>
            <input
              type="text"
              id="edit-client-name"
              v-model="editingClient.name"
              required
            />
          </div>
          <div class="form-group">
            <label for="edit-client-contact"
              >Pessoa de Contato (Opcional)</label
            >
            <input
              type="text"
              id="edit-client-contact"
              v-model="editingClient.contact_person"
            />
          </div>
          <div class="modal-actions">
            <button
              type="button"
              class="button-secondary"
              @click="closeEditClientModal"
            >
              Cancelar
            </button>
            <button type="submit" class="button-primary">
              Salvar Alterações
            </button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="isAddProjectModalOpen"
      class="modal-overlay"
      @click.self="closeAddProjectModal"
    >
      <div class="modal-content">
        <h2 v-if="selectedClient">
          Adicionar Novo Projeto para {{ selectedClient.name }}
        </h2>
        <form @submit.prevent="saveNewProject">
          <div class="form-group">
            <label for="new-project-name">Nome do Projeto</label>
            <input
              type="text"
              id="new-project-name"
              v-model="newProject.name"
              required
            />
          </div>
          <div class="modal-actions">
            <button
              type="button"
              class="button-secondary"
              @click="closeAddProjectModal"
            >
              Cancelar
            </button>
            <button type="submit" class="button-primary">Salvar Projeto</button>
          </div>
        </form>
      </div>
    </div>
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
  gap: 0.5rem;
}
.form-group label {
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
.label-with-button {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.add-new-button {
  border: none;
  background-color: transparent;
  color: var(--cor-primaria-acao);
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 700;
  padding: 0.25rem;
}
.edit-button {
  color: #ffa726;
  margin-right: 0.5rem;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background-color: #fff;
  padding: 2rem;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}
.modal-content h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
}
.modal-actions {
  margin-top: 1.5rem;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}
.modal-actions button {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  border: none;
  font-weight: 700;
  cursor: pointer;
}
.button-primary {
  background-color: var(--cor-primaria-acao);
  color: #fff;
}
.button-secondary {
  background-color: #eee;
  color: #333;
}
#new-client-name,
#new-client-contact,
#new-project-name,
#edit-client-name,
#edit-client-contact {
  width: 100%;
  box-sizing: border-box;
  padding: 0.75rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.project-header {
  margin-bottom: 1rem;
  padding: 1.5rem;
  background-color: var(--cor-principal);
  color: #fff;
  border-radius: 8px;
  text-align: center;
}
.project-header h3 {
  margin-bottom: 0.5rem;
  font-weight: 400;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.total-time-display {
  font-size: 2.5rem;
  font-weight: 700;
  font-family: "Courier New", Courier, monospace;
}
</style>
