import "./assets/main.css";

import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import router from "./router";

// Cria a instância principal da aplicação Vue, usando o App.vue como componente raiz.
const app = createApp(App);

// Diz à aplicação para usar os plugins que instalamos.
app.use(createPinia()); // Para gerenciamento de estado
app.use(router); // Para gerenciamento de rotas/páginas

// Monta a aplicação inteira na div com o id="app" no seu arquivo index.html.
app.mount("#app");
