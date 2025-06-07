import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
    },
    {
      path: "/about",
      name: "about",
      // Este é um exemplo de "lazy-loading" de rota, uma boa prática.
      // O componente só é carregado quando a rota é visitada.
      component: () => import("../views/AboutView.vue"),
    },
  ],
});

export default router;
