export function initAnimations() {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const targets = new Set();
  const lines = [...document.querySelectorAll('[data-type-line]')];
  const sentences = lines.map(line => Array.from(line.textContent));
  const description = document.querySelector('.hero-description');
  const hero = document.querySelector('.hero');
  const heading = document.querySelector('#hero-heading');
  let observer;
  let heroAnimation;
  let heroRange = 1;
  let heroProgress = -1;
  let frame = 0;
  let timer;

  function observeReveals(nodes) {
    for (const target of targets) {
      if (!target.isConnected) {
        observer?.unobserve(target);
        targets.delete(target);
      }
    }
    if (reduced.matches || !observer) return;
    nodes.forEach(target => {
      target.classList.add('reveal-pending');
      targets.add(target);
      observer.observe(target);
    });
  }

  function updateHero() {
    frame = 0;
    const progress = Math.min(1, Math.max(0, window.scrollY / heroRange));
    if (heroAnimation && progress !== heroProgress) {
      heroAnimation.currentTime = progress * 1000;
      heroProgress = progress;
    }
  }
  function scheduleHero() {
    if (!frame) frame = window.requestAnimationFrame(updateHero);
  }
  function measureHero() {
    heroRange = Math.max(1, Math.min(hero.offsetHeight, window.innerHeight * 0.65));
    scheduleHero();
  }
  function startHero() {
    if (!heading?.animate || heroAnimation) return;
    heroAnimation = heading.animate([
      { transform: 'translateY(0)', opacity: 1 },
      { transform: 'translateY(-20px)', opacity: 0.6 },
    ], { duration: 1000, fill: 'both', easing: 'linear' });
    heroAnimation.pause();
    window.addEventListener('scroll', scheduleHero, { passive: true });
    window.addEventListener('resize', measureHero);
    measureHero();
  }
  function stop() {
    clearTimeout(timer);
    observer?.disconnect();
    targets.forEach(target => target.classList.remove('reveal-pending'));
    targets.clear();
    if (frame) window.cancelAnimationFrame(frame);
    frame = 0;
    window.removeEventListener('scroll', scheduleHero);
    window.removeEventListener('resize', measureHero);
    heroAnimation?.cancel();
    heroAnimation = undefined;
    heroProgress = -1;
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
            targets.delete(entry.target);
          }
        });
      }, { threshold: 0.2 });
      observeReveals([...document.querySelectorAll('[data-reveal]')]);
    }
    startHero();
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
  reduced.addEventListener('change', event => {
    if (event.matches) stop();
    else startHero();
  });
  return observeReveals;
}
