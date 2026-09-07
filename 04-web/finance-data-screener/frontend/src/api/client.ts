import axios from "axios";

export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";

const client = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

export default client;
