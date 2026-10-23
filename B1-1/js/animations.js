export function initAnimations() {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const targets = [...document.querySelectorAll('[data-reveal]')];
  let observer;
  let timer;
  const typing = document.querySelector('#typing-text');
  const sentence = typing.textContent;
  function stop() {
    clearTimeout(timer);
    observer?.disconnect();
    targets.forEach(target => target.classList.remove('reveal-pending'));
    typing.textContent = sentence;
    typing.classList.remove('typing');
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
    let position = 0;
    typing.textContent = '';
    typing.classList.add('typing');
    function type() {
      position += 1;
      typing.textContent = sentence.slice(0, position);
      if (position < sentence.length) timer = setTimeout(type, 30);
      else typing.classList.remove('typing');
    }
    timer = setTimeout(type, 350);
  }
  reduced.addEventListener('change', stop);
}
