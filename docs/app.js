const DATA_URL = 'data/latest.json';
const SAMPLE_DATA_URL = 'data/sample.json';

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
  usedFallback: false,
};

async function fetchJson(url) {
  const response = await fetch(url, { cache: 'no-cache' });
  if (!response.ok) {
    const error = new Error(`Failed to load data (${response.status})`);
    error.status = response.status;
    error.url = url;
    throw error;

const state = {
  data: null,
};

async function loadData() {
  const response = await fetch(DATA_URL, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`Failed to load data (${response.status})`);
  }
  return response.json();
}

async function loadData() {
  try {
    const payload = await fetchJson(DATA_URL);
    return { payload, usedFallback: false };
  } catch (primaryError) {
    console.warn('Primary data request failed. Attempting to use sample payload.', primaryError);
    try {
      const fallbackPayload = await fetchJson(SAMPLE_DATA_URL);
      return { payload: fallbackPayload, usedFallback: true };
    } catch (fallbackError) {
      const error = new Error('Unable to load compliance briefing data.');
      error.cause = { primaryError, fallbackError };
      throw error;
    }
  }
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

function updateSummary(data, { usedFallback = false } = {}) {
  const summary = data?.summary ?? {};
  const sources = Array.isArray(summary.sources) ? summary.sources : [];

  if (usedFallback) {
    if (data?.generated_at) {
      elements.generatedAt.textContent = `Sample briefing from ${formatDate(data.generated_at, {
        timeZone: 'UTC',
      })} – live feed unavailable.`;
    } else {
      elements.generatedAt.textContent = 'Sample briefing loaded – live feed unavailable.';
    }
  } else {
    elements.generatedAt.textContent = data?.generated_at
      ? `Last refreshed ${formatDate(data.generated_at, { timeZone: 'UTC' })}`
      : 'Last refreshed: unavailable';
  }

  elements.totalItems.textContent = typeof summary.total_items === 'number'
    ? summary.total_items
    : '0';

  elements.sourceCount.textContent = sources.length ? String(sources.length) : '0';
  if (usedFallback) {
    elements.sourcesList.textContent = sources.length
      ? `Offline preview – sample sources: ${sources.join(' • ')}`
      : 'Offline preview shown while the live data endpoint is unavailable.';
  } else {
    elements.sourcesList.textContent = sources.length
      ? `Sources: ${sources.join(' • ')}`
      : 'No sources captured in the latest run.';
  }
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
    const { payload, usedFallback } = await loadData();
    state.data = payload;
    state.usedFallback = usedFallback;
    if (usedFallback) {
      document.body.classList.add('using-fallback-data');
    } else {
      document.body.classList.remove('using-fallback-data');
    }
    updateSummary(payload, { usedFallback });
    renderArticles(flattenArticles(payload));
  } catch (error) {
    console.error(error);
    document.body.classList.remove('using-fallback-data');
    state.usedFallback = false;
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
function formatDate(isoString) {
  if (!isoString) {
    return 'Published date unavailable';
  }
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) {
    return isoString;
  }
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  });
}

function renderSnapshot(summary, generatedAt) {
  const generatedAtEl = document.querySelector('#generatedAt');
  const totalItemsEl = document.querySelector('#totalItems');
  const sourcesEl = document.querySelector('#sourcesList');
  const verticalBreakdownEl = document.querySelector('#verticalBreakdown');
  const complianceBreakdownEl = document.querySelector('#complianceBreakdown');

  generatedAtEl.textContent = `Last refreshed ${formatDate(generatedAt)} (UTC)`;
  totalItemsEl.textContent = summary.total_items ?? 0;
  sourcesEl.textContent = summary.sources?.length
    ? summary.sources.join(', ')
    : 'No sources scanned';

  const buildBreakdown = (items = []) =>
    items
      .map((item) => `<li><span>${item.label}</span><span>(${item.count})</span></li>`)
      .join('');

  verticalBreakdownEl.innerHTML = buildBreakdown(summary.vertical_counts);
  complianceBreakdownEl.innerHTML = buildBreakdown(summary.compliance_counts);
}

function populateFilters(sections) {
  const verticalFilter = document.querySelector('#verticalFilter');
  const complianceFilter = document.querySelector('#complianceFilter');

  const verticalOptions = new Map();
  const complianceOptions = new Map();

  sections.forEach((section) => {
    verticalOptions.set(section.vertical.key, section.vertical.label);
    section.segments.forEach((segment) => {
      complianceOptions.set(segment.compliance.key, segment.compliance.label);
    });
  });

  const addOptions = (select, options) => {
    options.forEach((label, key) => {
      const option = document.createElement('option');
      option.value = key;
      option.textContent = label;
      select.appendChild(option);
    });
  };

  addOptions(verticalFilter, verticalOptions);
  addOptions(complianceFilter, complianceOptions);

  verticalFilter.addEventListener('change', renderArticles);
  complianceFilter.addEventListener('change', renderArticles);
}

function renderArticles() {
  const container = document.querySelector('#articlesContainer');
  if (!state.data) {
    container.innerHTML = '<p class="loading">No data available.</p>';
    return;
  }

  const verticalFilter = document.querySelector('#verticalFilter').value;
  const complianceFilter = document.querySelector('#complianceFilter').value;

  const sections = state.data.sections;
  const articleFragments = [];

  sections.forEach((section) => {
    if (verticalFilter !== 'all' && section.vertical.key !== verticalFilter) {
      return;
    }

    const matchingSegments = section.segments.filter((segment) =>
      complianceFilter === 'all' || segment.compliance.key === complianceFilter,
    );

    if (!matchingSegments.length) {
      return;
    }

    const verticalBlock = document.createElement('div');
    verticalBlock.className = 'vertical-block';

    const verticalHeader = document.createElement('h3');
    verticalHeader.textContent = section.vertical.label;
    verticalBlock.appendChild(verticalHeader);

    matchingSegments.forEach((segment) => {
      const group = document.createElement('div');
      group.className = 'compliance-group';

      const header = document.createElement('h4');
      header.textContent = segment.compliance.label;
      group.appendChild(header);

      segment.items.forEach((item) => {
        const card = document.createElement('article');
        card.className = 'article-card';

        const title = document.createElement('h5');
        const link = document.createElement('a');
        link.href = item.link || '#';
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = item.title;
        title.appendChild(link);
        card.appendChild(title);

        const meta = document.createElement('p');
        meta.className = 'article-meta';
        meta.textContent = `${item.source} • ${formatDate(item.published)}`;
        card.appendChild(meta);

        if (item.summary) {
          const summary = document.createElement('p');
          summary.className = 'article-summary';
          summary.textContent = item.summary;
          card.appendChild(summary);
        }

        const tags = document.createElement('div');
        tags.className = 'tags';

        const allTags = [...item.verticals, ...item.compliance];
        allTags.forEach((tagInfo) => {
          const tag = document.createElement('span');
          tag.className = 'tag';
          tag.textContent = tagInfo.label;
          tags.appendChild(tag);
        });

        if (item.keyword_hits) {
          Object.entries(item.keyword_hits).forEach(([category, mapping]) => {
            Object.entries(mapping).forEach(([key, hits]) => {
              if (!hits.length) return;
              const keyword = document.createElement('span');
              keyword.className = 'keyword-hit';
              keyword.textContent = `${category === 'verticals' ? 'Vertical keywords' : 'Compliance keywords'}: ${[
                ...new Set(hits),
              ].join(', ')}`;
              tags.appendChild(keyword);
            });
          });
        }

        if (tags.childElementCount) {
          card.appendChild(tags);
        }

        group.appendChild(card);
      });

      verticalBlock.appendChild(group);
    });

    articleFragments.push(verticalBlock);
  });

  container.innerHTML = '';

  if (!articleFragments.length) {
    container.innerHTML = '<p class="empty-state">No articles match the selected filters.</p>';
    return;
  }

  articleFragments.forEach((fragment) => container.appendChild(fragment));
}

async function init() {
  const container = document.querySelector('#articlesContainer');
  try {
    state.data = await loadData();
    renderSnapshot(state.data.summary, state.data.generated_at);
    populateFilters(state.data.sections);
    renderArticles();
  } catch (error) {
    console.error(error);
    container.innerHTML = '<p class="empty-state">Unable to load the latest report. Please try again later.</p>';
  }
}

init();
