export function initAnimations() {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const targets = [...document.querySelectorAll('[data-reveal]')];
  const lines = [...document.querySelectorAll('[data-type-line]')];
  const sentences = lines.map(line => Array.from(line.textContent));
  const description = document.querySelector('.hero-description');
  let observer;
  let timer;
  function stop() {
    clearTimeout(timer);
    observer?.disconnect();
    targets.forEach(target => target.classList.remove('reveal-pending'));
    lines.forEach((line, index) => {
      line.textContent = sentences[index].join('');
      line.classList.remove('typing');
    });
    description.classList.remove('hero-description-pending');
  }
  if (!reduced.matches) {
    if ('IntersectionObserver' in window) {
      observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.remove('reveal-pending');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.2 });
      targets.forEach(target => { target.classList.add('reveal-pending'); observer.observe(target); });
    }
    lines.forEach(line => { line.textContent = ''; });
    description.classList.add('hero-description-pending');
    let lineIndex = 0;
    let position = 0;
    function type() {
      const line = lines[lineIndex];
      line.classList.add('typing');
      position += 1;
      line.textContent = sentences[lineIndex].slice(0, position).join('');
      if (position < sentences[lineIndex].length) {
        timer = setTimeout(type, 65);
      } else {
        line.classList.remove('typing');
        lineIndex += 1;
        position = 0;
        timer = lineIndex < lines.length
          ? setTimeout(type, 140)
          : setTimeout(() => description.classList.remove('hero-description-pending'), 180);
      }
    }
    timer = setTimeout(type, 300);
  }
  reduced.addEventListener('change', stop);
}
