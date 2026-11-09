/** Rerunnable CUA browser check. Pass a connected tab and src/foundations.json.
 * Start at /smalldocs/ or /quarto/. A parent can call this same function on a
 * narrow iframe via manual AX interactions. CUA does not support iframe DOM
 * evaluation; this helper verifies root documents only. Viewport/screenshots
 * remain the browser reviewer's job.
 */
export async function verifyReading(tab, foundation) {
  const failures = [];
  let context = foundation.theme;
  const assert = (condition, message) => { if (!condition) failures.push(context + ': ' + message); };
  const observed = [];
  await tab.playwright.domSnapshot();
  for (let index = 0; index < 2; index += 1) {
    // TOC active-state colors animate in the native shells. Wait for the
    // declared transition duration rather than sampling an interpolated color.
    const transitions = await tab.playwright.evaluate(() => Array.from(document.querySelectorAll('#TOC .nav-link')).map(el => ({duration:getComputedStyle(el).transitionDuration,delay:getComputedStyle(el).transitionDelay})));
    const milliseconds = value => value.trim().endsWith('ms') ? Number.parseFloat(value) : Number.parseFloat(value) * 1000;
    const settle = Math.max(0, ...transitions.map(item => Math.max(...item.duration.split(',').map(milliseconds)) + Math.max(...item.delay.split(',').map(milliseconds))));
    if (settle > 0) await tab.playwright.waitForTimeout(Math.ceil(settle) + 20);
    const metrics = await tab.playwright.evaluate(() => {
      const style = selector => {
        const el = document.querySelector(selector);
        if (!el) throw new Error('Missing fixture component: ' + selector);
        const s = getComputedStyle(el);
        return {size: +(s.fontSize.replace('px','')), ink: s.color, fill: s.backgroundColor,
          line: +(s.lineHeight.replace('px','')), padding: +(s.paddingTop.replace('px','')), paddingRight: +(s.paddingRight.replace('px','')), opacity: s.opacity, width: el.getBoundingClientRect().width};
      };
      const root = getComputedStyle(document.documentElement);
      const hamburger = document.querySelector('.navbar-toggler-icon');
      return {root: +(root.fontSize.replace('px','')), viewport:document.documentElement.clientWidth, body: style('body'), prose: style('main.content p'), title: style('.quarto-title h1.title'), hamburger: hamburger ? getComputedStyle(hamburger).backgroundImage : null,
        primary: style('#primary'), secondary: style('#secondary'),
        callout: style('.callout-body'), calloutParagraph: style('.callout-body p'), calloutHeader: style('.callout-header'), code: style('p > code'),
        codeOuter: style('div.sourceCode'), codePre: style('pre.sourceCode'), codeInner: style('pre.sourceCode code'), codeSpan: style('pre.sourceCode code > span'), error: style('#invalid-message'), table: style('table'), cell: style('td'), tableHeading: style('th'), caption: style('figcaption'),
        nav: style('.navbar .nav-link'), toc: Array.from(document.querySelectorAll('#TOC .nav-link')).map(el => ({active:el.classList.contains('active'),ink:getComputedStyle(el).color,size:+getComputedStyle(el).fontSize.replace('px','')})), disabled: document.querySelector('#disabled').disabled,
        invalid: document.querySelector('#invalid').getAttribute('aria-describedby'),
        semanticActions: Array.from(document.querySelectorAll('button[data-action-state]')).map(el => ({id:el.id,state:el.getAttribute('data-action-state'),variant:el.getAttribute('data-action-variant'),phase:el.getAttribute('data-action-phase'),ink:getComputedStyle(el).color,fill:getComputedStyle(el).backgroundColor,boundary:getComputedStyle(el).borderColor,opacity:getComputedStyle(el).opacity,image:getComputedStyle(el).backgroundImage,decoration:getComputedStyle(el).textDecorationLine,disabled:el.disabled})),
        calloutStates: ['note','tip','warning','important','caution'].map(kind => { const el = document.querySelector('.callout-' + kind); const header = el.querySelector('.callout-header'); const icon = el.querySelector('.callout-icon'); return {kind, ink:getComputedStyle(header).color, fill:getComputedStyle(header).backgroundColor, boundary:getComputedStyle(el).borderLeftColor, icon:icon ? getComputedStyle(icon).color : null}; }),
        overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth};
    });
    const rgb = hex => 'rgb(' + [1,3,5].map(i => parseInt(hex.slice(i,i+2),16)).join(', ') + ')';
    const mode = Object.entries(foundation.modes).find(([,data]) => rgb(data.swatches[data.roles.paper]) === metrics.body.fill)?.[0];
    if (!mode) throw new Error('Body uses neither authored paper');
    context = foundation.theme + ' ' + mode;
    const data = foundation.modes[mode];
    const role = name => rgb(data.swatches[data.roles[name]]);
    const reading = foundation.typography.profiles.reading;
    assert(metrics.root === 16, 'Default root must honor the 16px browser preference: ' + metrics.root);
    assert(metrics.body.size === reading.body, 'Body profile mismatch');
    assert(metrics.title.size === reading.title, 'Title profile mismatch');
    assert(Math.abs(metrics.body.line - reading.body * foundation.typography.lineHeights.reading) < .02, 'Body line-height mismatch');
    assert(Math.abs(metrics.callout.line - reading.body * foundation.typography.lineHeights.reading) < .02, 'Callout line-height mismatch');
    assert(metrics.callout.padding === foundation.spacing.profiles.reading.panel && metrics.callout.paddingRight === foundation.spacing.profiles.reading.panel, 'Callout panel padding mismatch');
    assert(metrics.calloutParagraph.size === reading.body && metrics.calloutParagraph.padding === 0, 'Callout paragraph remains shrunk or double-padded');
    assert(metrics.calloutHeader.size === reading.ui && metrics.calloutHeader.opacity === '1', 'Callout header UI role mismatch');
    if (metrics.viewport >= 800) assert(metrics.prose.width <= 640.1, 'Desktop prose exceeds 640px: ' + metrics.prose.width);
    assert([role('ink'),role('muted'),role('accent-text')].includes(metrics.nav.ink), 'Effective navbar ink loses foundation cascade');
    if (metrics.hamburger && metrics.hamburger !== 'none') {
      const image = decodeURIComponent(metrics.hamburger);
      const paint = image.match(/(?:stroke|fill)=["'](#[0-9a-f]{6}|rgba?\([^"']+\))["']/i)?.[1];
      if (paint) {
        const channels = paint.startsWith('#') ? [1,3,5].map(i => parseInt(paint.slice(i,i+2),16)) : paint.match(/[\d.]+/g).map(Number);
        const bg = role('paper').match(/\d+/g).map(Number);
        const alpha = channels[3] ?? 1;
        assert(alpha === 1 && 'rgb(' + channels.slice(0,3).join(', ') + ')' === role('ink'), 'Hamburger must use opaque foundation ink');
        const lum = c => c.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
        const blended = channels.slice(0,3).map((v,i)=>v*alpha+bg[i]*(1-alpha));
        const pair = [lum(blended),lum(bg)].sort((a,b)=>a-b);
        assert((pair[1]+.05)/(pair[0]+.05)>=3, 'Hamburger glyph lacks meaningful contrast');
      }
    }
    assert(metrics.secondary.size === reading.ui && metrics.secondary.ink === role('secondary-action'), 'Effective secondary action mismatch');
    assert(metrics.callout.size === reading.body, 'Callout prose must use reading body');
    assert(metrics.code.size === reading.code && metrics.code.ink === role('code-ink'), 'Inline code role mismatch');
    assert(metrics.code.padding === 0 && metrics.code.paddingRight === 4, 'Inline code ladder padding mismatch');
    assert(metrics.codeOuter.padding === foundation.spacing.profiles.reading.panel && metrics.codeOuter.paddingRight === foundation.spacing.profiles.reading.panel, 'Code outer padding mismatch');
    for (const component of [metrics.codePre,metrics.codeInner,metrics.codeSpan]) {
      assert(component.size === reading.code && Math.abs(component.line - reading.code * foundation.typography.lineHeights.code) < .02, 'Code block text size or line-height mismatch');
    }
    assert(metrics.codePre.padding === 0 && metrics.codePre.paddingRight === 0 && metrics.codeInner.padding === 0 && metrics.codeInner.paddingRight === 0, 'Nested code padding duplicates outer panel');
    assert(metrics.codePre.ink === role('code-ink') && metrics.codeInner.ink === role('code-ink'), 'Code block base ink mismatch');
    assert(metrics.error.size === reading.ui && metrics.error.ink === rgb(data.states.danger.ink), 'Error role loses cascade');
    assert(Math.abs(metrics.error.line - reading.ui * foundation.typography.lineHeights.ui) < .02, 'Error UI line-height mismatch');
    for (const component of [metrics.table,metrics.cell,metrics.tableHeading]) {
      assert(component.size === reading.ui && Math.abs(component.line - reading.ui * foundation.typography.lineHeights.ui) < .02, 'Table/cell UI typography mismatch');
    }
    assert(metrics.caption.size === reading.metadata && metrics.caption.ink === role('muted'), 'Caption role mismatch');
    assert(metrics.disabled && metrics.invalid === 'invalid-message', 'Native/programmatic state semantics missing');
    assert(!metrics.overflow, 'Document overflows horizontally');
    for (const callout of metrics.calloutStates) {
      const stateName = {note:'info',tip:'success',warning:'warning',important:'danger',caution:'danger'}[callout.kind];
      const state = data.states[stateName];
      assert(callout.ink === rgb(state.ink) && callout.fill === rgb(state.fill) && callout.boundary === rgb(state.boundary), 'Semantic callout pair mismatch: ' + callout.kind);
      if (callout.icon) assert(callout.icon === rgb(state.ink), 'Semantic callout icon mismatch: ' + callout.kind);
    }
    assert(metrics.toc.length > 0, 'Fixture TOC links missing');
    for (const link of metrics.toc) {
      assert(link.ink === role(link.active ? 'accent-text' : 'muted'), 'TOC effective ink mismatch');
      assert(link.size === reading.ui, 'TOC UI size mismatch');
    }
    assert(metrics.semanticActions.length === 27, 'Semantic action fixture incomplete');
    for (const action of metrics.semanticActions) {
      let ink, fill, boundary;
      if (action.phase === 'disabled') {
        ink = role('disabled-ink'); fill = role('disabled-fill'); boundary = role('control-boundary');
        assert(action.disabled && action.opacity === '1', 'Native opaque disabled semantic action missing: ' + action.id);
      } else if (action.state === 'secondary') {
        ink = role('secondary-action');
        fill = role(action.phase === 'active' ? 'panel' : 'paper'); boundary = role('control-boundary');
      } else {
        const state = data.states[action.state];
        ink = rgb(state.ink); fill = action.variant === 'outline' && action.phase === 'normal' ? role('paper') : rgb(state.fill); boundary = role('control-boundary');
      }
      assert(action.ink === ink && action.fill === fill && action.boundary === boundary, 'Semantic action effective pair mismatch: ' + action.id);
      assert(action.image === 'none', 'Semantic action has an untested background image: ' + action.id);
      if (action.phase === 'active') assert(action.decoration.includes('underline'), 'Active semantic action lacks a non-color cue: ' + action.id);
      if (action.phase === 'disabled') assert(action.decoration === 'none', 'Disabled semantic action retains active decoration: ' + action.id);
    }
    metrics.semanticActionInteractions = [];
    for (const action of metrics.semanticActions.filter(item => item.phase === 'normal')) {
      const button = tab.playwright.locator('#' + action.id);
      await button.click();
      const transition = await button.evaluate(el => ({duration:getComputedStyle(el).transitionDuration,delay:getComputedStyle(el).transitionDelay}));
      const delay = Math.max(...transition.duration.split(',').map(milliseconds)) + Math.max(...transition.delay.split(',').map(milliseconds));
      if (delay > 0) await tab.playwright.waitForTimeout(Math.ceil(delay) + 20);
      const hover = await button.evaluate(el => ({ink:getComputedStyle(el).color,fill:getComputedStyle(el).backgroundColor,boundary:getComputedStyle(el).borderColor,image:getComputedStyle(el).backgroundImage,focused:document.activeElement === el}));
      const state = action.state === 'secondary' ? null : data.states[action.state];
      assert(hover.ink === (state ? rgb(state.ink) : role('secondary-action')) && hover.fill === (state ? rgb(state.fill) : role('panel')) && hover.boundary === role('control-boundary'), 'Semantic action hover pair mismatch: ' + action.id);
      assert(hover.image === 'none', 'Semantic action hover has an untested background image: ' + action.id);
      await button.press('Tab');
      const focused = await tab.playwright.evaluate(() => ({outline:getComputedStyle(document.activeElement).outlineWidth,color:getComputedStyle(document.activeElement).outlineColor,offset:getComputedStyle(document.activeElement).outlineOffset}));
      assert(focused.outline === '2px' && focused.color === role('focus') && focused.offset === '4px', 'Semantic action keyboard focus mismatch: ' + action.id);
      metrics.semanticActionInteractions.push({id:action.id,hover,focused});
    }
    observed.push({mode, ...metrics});
    // Many action clicks scroll the page. Confirm the actual toggle reached
    // the other authored paper before continuing; a failed toggle stays a failure.
    const targetMode = mode === 'light' ? 'dark' : 'light';
    const targetData = foundation.modes[targetMode];
    const targetPaper = rgb(targetData.swatches[targetData.roles.paper]);
    // Return to the visible title before using the fixed navbar after the
    // long action sequence; this avoids a scroll/headroom interception.
    await tab.playwright.locator('h1.title').click();
    await tab.getAXState();
    await tab.playwright.locator('.quarto-color-scheme-toggle').first().click();
    let settled = false;
    for (let attempt = 0; attempt < 12; attempt += 1) {
      await tab.playwright.domSnapshot();
      const paper = await tab.playwright.evaluate(() => getComputedStyle(document.body).backgroundColor);
      if (paper === targetPaper) { settled = true; break; }
    }
    assert(settled, 'Mode toggle did not reach expected ' + targetMode + ' paper');
  }
  assert(observed[0].mode !== observed[1].mode, 'Mode control did not switch authored palettes');
  await tab.playwright.getByLabel('Your name', {exact:true}).fill('Grace');
  await tab.playwright.getByLabel('Choose a mode', {exact:true}).selectOption({label:'Second choice'});
  await tab.playwright.getByLabel('Checked choice', {exact:true}).uncheck();
  await tab.playwright.getByLabel('Your name', {exact:true}).press('Tab');
  await tab.playwright.domSnapshot();
  const focus = await tab.playwright.evaluate(() => ({outline:getComputedStyle(document.activeElement).outlineWidth, value:document.querySelector('#name').value, checked:document.querySelector('#checked').checked, selected:document.querySelector('#choice').selectedIndex}));
  assert(focus.outline === '2px' && focus.value === 'Grace' && !focus.checked && focus.selected === 1, 'Keyboard/form interaction failed');
  return {passed: failures.length === 0, failures, observed, focus};
}
