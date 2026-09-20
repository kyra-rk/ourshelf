import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // relative base so the built app works from a gh-pages project subpath
  // (e.g. username.github.io/ourshelf/) without hardcoding the repo name
  base: './',
})
