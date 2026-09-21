import { ru } from "vuetify/locale";
import "@mdi/font/css/materialdesignicons.css";
import "vuetify/styles";
import { createVuetify } from "vuetify";
import * as components from "vuetify/components";
import * as directives from "vuetify/directives";

export default createVuetify({
  locale: { locale: "ru", messages: { ru } },
  components,
  directives,
  theme: {
    defaultTheme: "light",
    themes: {
      light: {
        dark: false,
        colors: {
          primary: "#7770ca",
          secondary: "#89a998",
          background: "#f7f8fc",
          surface: "#ffffff",
        },
      },
    },
  },
});
