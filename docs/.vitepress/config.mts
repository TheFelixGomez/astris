import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Astris',
  description: 'The modern full-stack web framework for Python.',
  head: [
    ['link', { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#0ea5e9' }],
  ],
  themeConfig: {
    logo: '/astris-logo.svg',
    nav: [
      { text: 'Documentation', link: '/getting-started/introduction' },
      { text: 'Orbit CLI', link: '/cli/orbit' },
      { text: 'PyPI', link: 'https://pypi.org/project/astris-python/' },
      {
        text: 'v0.1.1',
        items: [
          { text: 'Release Notes', link: 'https://github.com/TheFelixGomez/astris/releases' },
          { text: 'Roadmap & Issues', link: 'https://github.com/TheFelixGomez/astris/issues' },
        ],
      },
    ],

    sidebar: [
      {
        text: 'Getting Started',
        items: [
          { text: 'Introduction', link: '/getting-started/introduction' },
          { text: 'Installation', link: '/getting-started/installation' },
          { text: 'Directory Structure', link: '/getting-started/directory-structure' },
          { text: 'Configuration & .env', link: '/getting-started/configuration' },
        ],
      },
      {
        text: 'Architecture & Routing',
        items: [
          { text: 'Application Kernel', link: '/architecture/kernel' },
          { text: 'Controllers & Routes', link: '/architecture/controllers' },
          { text: 'HTTP Requests & Responses', link: '/architecture/http-requests' },
          { text: 'Module Auto-Discovery', link: '/architecture/module-discovery' },
        ],
      },
      {
        text: 'Frontend & Inertia.js',
        items: [
          { text: 'Inertia.js Overview', link: '/frontend/inertia' },
          { text: 'Rendering Responses', link: '/frontend/responses' },
          { text: 'Shared Props & Flash Data', link: '/frontend/shared-data' },
          { text: 'Forms & Validation', link: '/frontend/forms-validation' },
          { text: 'Vite & Tailwind CSS v4', link: '/frontend/vite-tailwind' },
        ],
      },
      {
        text: 'Database & Models',
        items: [
          { text: 'Configuration', link: '/database/configuration' },
          { text: 'SQLModel Models', link: '/database/models' },
          { text: 'Queries & CRUD', link: '/database/queries' },
          { text: 'Schema Migrations', link: '/database/migrations' },
        ],
      },
      {
        text: 'Security & Authentication',
        items: [
          { text: 'Authentication Kit', link: '/security/authentication' },
          { text: 'Auth Guards & Dependencies', link: '/security/guards' },
          { text: 'CSRF Protection', link: '/security/csrf' },
          { text: 'Signed Cookie Sessions', link: '/security/sessions' },
        ],
      },
      {
        text: 'CLI Reference',
        items: [
          { text: 'Orbit CLI', link: '/cli/orbit' },
          { text: 'Astris Project Generator', link: '/cli/astris' },
        ],
      },
      {
        text: 'Deployment',
        items: [
          { text: 'Production & Docker', link: '/deployment/production' },
        ],
      },
    ],

    search: {
      provider: 'local',
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/TheFelixGomez/astris' },
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2026 Felix Gomez',
    },
  },
})
