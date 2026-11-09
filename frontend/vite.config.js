import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite compila el código de React (JSX) a un único archivo JavaScript.
// Lo dejo DENTRO de la carpeta static de la app "tablero" de Django, así
// Django lo entrega como cualquier otro archivo estático y no hace falta
// un segundo servidor: todo vive en un solo sitio y en un solo repositorio.
export default defineConfig({
  plugins: [react()],
  build: {
    // Carpeta de salida (relativa a frontend/)
    outDir: '../tablero/static/tablero/react',
    // Borra lo anterior en cada compilación, para no acumular archivos viejos
    emptyOutDir: true,
    rollupOptions: {
      // El punto de entrada es el JavaScript, no un index.html
      input: 'src/main.jsx',
      output: {
        // Nombre fijo, sin código al final, para que la plantilla de
        // Django pueda escribir siempre la misma dirección
        entryFileNames: 'tablero.js',
        chunkFileNames: '[name].js',
        assetFileNames: 'tablero.[ext]',
      },
    },
  },
})
