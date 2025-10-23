const DATA_URL = 'data/latest.json';

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
