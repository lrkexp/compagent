const DATA_URL = 'data/latest.json';

const elements = {
  refreshButton: document.querySelector('#refreshButton'),
  generatedAt: document.querySelector('#generatedAt'),
  totalItems: document.querySelector('#totalItems'),
  sourceCount: document.querySelector('#sourceCount'),
  sourcesList: document.querySelector('#sourcesList'),
  articlesContainer: document.querySelector('#articlesContainer'),
};

const state = {
  data: null,
  isLoading: false,
};

async function loadData() {
  const response = await fetch(DATA_URL, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`Failed to load data (${response.status})`);
  }
  return response.json();
}

function formatDate(isoString, { includeTime = true, timeZone } = {}) {
  if (!isoString) {
    return 'Date unavailable';
  }

  const parsed = new Date(isoString);
  if (Number.isNaN(parsed.getTime())) {
    return isoString;
  }

  const options = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };

  if (includeTime) {
    options.hour = '2-digit';
    options.minute = '2-digit';
  }

  if (timeZone) {
    options.timeZone = timeZone;
    options.timeZoneName = 'short';
  }

  return parsed.toLocaleString(undefined, options);
}

function flattenArticles(data) {
  if (!data?.sections?.length) {
    return [];
  }

  const articles = [];

  data.sections.forEach((section) => {
    const verticalFallback = section?.vertical ? [section.vertical] : [];
    section.segments?.forEach((segment) => {
      const complianceFallback = segment?.compliance ? [segment.compliance] : [];
      segment.items?.forEach((item) => {
        articles.push({
          ...item,
          verticals: item.verticals?.length ? item.verticals : verticalFallback,
          compliance: item.compliance?.length ? item.compliance : complianceFallback,
        });
      });
    });
  });

  return articles.sort((a, b) => {
    const first = new Date(b.published ?? 0).getTime();
    const second = new Date(a.published ?? 0).getTime();
    return Number.isNaN(first - second) ? 0 : first - second;
  });
}

function updateSummary(data) {
  const summary = data?.summary ?? {};
  const sources = Array.isArray(summary.sources) ? summary.sources : [];

  elements.generatedAt.textContent = data?.generated_at
    ? `Last refreshed ${formatDate(data.generated_at, { timeZone: 'UTC' })}`
    : 'Last refreshed: unavailable';

  elements.totalItems.textContent = typeof summary.total_items === 'number'
    ? summary.total_items
    : '0';

  elements.sourceCount.textContent = sources.length ? String(sources.length) : '0';
  elements.sourcesList.textContent = sources.length
    ? `Sources: ${sources.join(' • ')}`
    : 'No sources captured in the latest run.';
}

function renderArticles(articles) {
  const container = elements.articlesContainer;
  container.innerHTML = '';

  if (!articles.length) {
    container.innerHTML = '<p class="empty-state">No updates were published in the latest run.</p>';
    return;
  }

  articles.forEach((item) => {
    const article = document.createElement('article');
    article.className = 'briefing-item';

    const title = document.createElement('h3');
    const link = document.createElement('a');
    link.href = item.link || '#';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = item.title || 'Untitled update';
    title.appendChild(link);
    article.appendChild(title);

    if (item.verticals?.length) {
      const verticalsRow = document.createElement('div');
      verticalsRow.className = 'briefing-verticals';

      item.verticals.forEach((vertical) => {
        if (!vertical?.label) {
          return;
        }
        const pill = document.createElement('span');
        pill.className = 'vertical-pill';
        pill.dataset.vertical = vertical.key || 'default';
        pill.textContent = vertical.label;
        verticalsRow.appendChild(pill);
      });

      if (verticalsRow.childElementCount) {
        article.appendChild(verticalsRow);
      }
    }

    const meta = document.createElement('p');
    meta.className = 'briefing-meta';
    const source = item.source || 'Source unavailable';
    meta.textContent = `${source} · ${formatDate(item.published, { includeTime: false })}`;
    article.appendChild(meta);

    if (item.summary) {
      const summary = document.createElement('p');
      summary.className = 'briefing-summary';
      summary.textContent = item.summary;
      article.appendChild(summary);
    }

    if (item.compliance?.length) {
      const compliance = document.createElement('p');
      compliance.className = 'briefing-compliance';
      const labels = item.compliance
        .filter((entry) => Boolean(entry?.label))
        .map((entry) => entry.label);
      if (labels.length) {
        compliance.textContent = `Compliance focus: ${labels.join(' · ')}`;
        article.appendChild(compliance);
      }
    }

    container.appendChild(article);
  });
}

function setLoading(isLoading) {
  state.isLoading = isLoading;
  const button = elements.refreshButton;
  if (!button) {
    return;
  }

  if (isLoading) {
    button.setAttribute('disabled', 'true');
    button.textContent = 'Refreshing…';
  } else {
    button.removeAttribute('disabled');
    button.textContent = 'Refresh briefing';
  }
}

async function refreshData() {
  if (state.isLoading) {
    return;
  }

  setLoading(true);
  elements.articlesContainer.innerHTML = '<p class="loading">Loading the latest briefing…</p>';

  try {
    const data = await loadData();
    state.data = data;
    updateSummary(data);
    renderArticles(flattenArticles(data));
  } catch (error) {
    console.error(error);
    elements.generatedAt.textContent = 'Unable to refresh – please try again later.';
    elements.totalItems.textContent = '0';
    elements.sourceCount.textContent = '0';
    elements.sourcesList.textContent = 'Sources unavailable – please retry.';
    elements.articlesContainer.innerHTML =
      '<p class="empty-state">Unable to load the latest report. Check your network connection and try again.</p>';
  } finally {
    setLoading(false);
  }
}

if (elements.refreshButton) {
  elements.refreshButton.addEventListener('click', refreshData);
}

refreshData();
