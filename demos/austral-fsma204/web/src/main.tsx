import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, HashRouter } from "react-router-dom";
import "@fontsource/inter/400.css";
import "@fontsource/inter/600.css";
import "./index.css";
import { App } from "./App";
import { installStaticFetch } from "./staticDemo";

if (import.meta.env.VITE_STATIC === "1") installStaticFetch();

const Router = import.meta.env.VITE_STATIC === "1" ? HashRouter : BrowserRouter;

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Router>
      <App />
    </Router>
  </React.StrictMode>,
);
