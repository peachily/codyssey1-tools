// Shared brand mapping. Unknown or non-brand technologies remain readable text.
const iconFiles = Object.freeze({
  HTML5: 'html5', CSS3: 'css3', JavaScript: 'javascript', TypeScript: 'typescript',
  React: 'react', Vite: 'vitejs', 'Tailwind CSS': 'tailwindcss',
  Python: 'python', 'Node.js': 'nodejs', FastAPI: 'fastapi', SQLite: 'sqlite',
  PostgreSQL: 'postgresql', Supabase: 'supabase', PocketBase: 'pocketbase', 'OpenAI API': 'openai',
  Git: 'git', GitHub: 'github', Linux: 'linux', 'Amazon Web Services': 'amazonwebservices',
  Flask: 'flask', SQLAlchemy: 'sqlalchemy',
  Docker: 'docker', Railway: 'railway', Cloudflare: 'cloudflare', Netlify: 'netlify', Figma: 'figma',
});
const aliases = Object.freeze({ HTML: 'HTML5', CSS: 'CSS3' });
export function createTechnologyBadge(name, { compact = false } = {}) {
  const label = aliases[name] || name;
  const badge = document.createElement('span');
  badge.className = `badge technology-badge${compact ? ' technology-badge--compact' : ''}`;
  badge.dataset.technology = label;
  if (iconFiles[label]) {
    const image = document.createElement('img');
    image.className = `technology-logo${label === 'Railway' ? ' technology-logo--railway' : ''}`;
    image.src = `assets/icons/technologies/${iconFiles[label]}.svg`;
    image.alt = '';
    image.width = compact ? 14 : 18; image.height = compact ? 14 : 18;
    image.loading = 'lazy'; image.decoding = 'async';
    badge.append(image);
  }
  const text = document.createElement('span');
  text.textContent = label;
  badge.append(text);
  return badge;
}
export function initSkills() {
  document.querySelectorAll('#skills [data-technology]').forEach(node => {
    node.replaceWith(createTechnologyBadge(node.dataset.technology));
  });
}
