const $ = (selector) => document.querySelector(selector);
const reviewsInput = $('#reviews-input');
const errorMessage = $('#error-message');
const sampleReviews = [
  'I love how easy this app is to use. The design looks great!',
  'The checkout page is very slow and sometimes freezes.',
  'Please add a dark mode option in the next update.',
  'Customer support was helpful and solved my problem quickly.',
  'The subscription is too expensive for the features available.',
  'The app crashed twice when I tried to save my work.',
  'Navigation is simple and the new search feature works well.',
  'I received my order yesterday.'
];
let latestAnalysis = null;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}
function updateReviewCount() {
  const count = reviewsInput.value.split(/\r?\n/).filter(line => line.trim()).length;
  $('#review-count').textContent = `${count} review${count === 1 ? '' : 's'} entered`;
}
function showError(message) {
  errorMessage.textContent = message;
  errorMessage.classList.remove('hidden');
}
function clearError() {
  errorMessage.textContent = '';
  errorMessage.classList.add('hidden');
}
function setLoading(button, loading, label) {
  button.disabled = loading;
  if (loading) {
    button.dataset.originalText = button.innerHTML;
    button.textContent = 'Analyzing…';
  } else if (button.dataset.originalText) {
    button.innerHTML = button.dataset.originalText;
    delete button.dataset.originalText;
  } else if (label) {
    button.textContent = label;
  }
}
function sentimentClass(label) {
  return label === 'Positive' ? 'badge-positive' : label === 'Negative' ? 'badge-negative' : 'badge-neutral';
}
function renderResults(data) {
  latestAnalysis = data;
  $('#empty-state').classList.add('hidden');
  $('#results').classList.remove('hidden');
  $('#export-button').disabled = false;
  $('#total-metric').textContent = data.total;
  const counts = data.sentiment_counts;
  const percentages = data.sentiment_percentages;
  $('#positive-metric').textContent = `${percentages.Positive}%`;
  $('#negative-metric').textContent = `${percentages.Negative}%`;
  $('#positive-count').textContent = `${counts.Positive} review${counts.Positive === 1 ? '' : 's'}`;
  $('#negative-count').textContent = `${counts.Negative} review${counts.Negative === 1 ? '' : 's'}`;
  $('#neutral-count').textContent = `${counts.Neutral} neutral`;
  $('#positive-legend').textContent = `${percentages.Positive}%`;
  $('#neutral-legend').textContent = `${percentages.Neutral}%`;
  $('#negative-legend').textContent = `${percentages.Negative}%`;
  $('.bar-positive').style.width = `${percentages.Positive}%`;
  $('.bar-neutral').style.width = `${percentages.Neutral}%`;
  $('.bar-negative').style.width = `${percentages.Negative}%`;

  const themes = data.theme_counts || [];
  const maxTheme = Math.max(1, ...themes.map(item => item.count));
  $('#theme-list').innerHTML = themes.length ? themes.slice(0, 6).map(item => `
    <div class="theme-item"><span class="theme-name">${escapeHtml(item.theme)}</span><div class="theme-track"><div class="theme-fill" style="width:${Math.max(5, item.count / maxTheme * 100)}%"></div></div><span class="theme-count">${item.count}</span></div>`).join('') : '<p class="subtle-label">No recurring themes detected in this batch.</p>';

  $('#recommendation-list').innerHTML = data.recommendations.map((item, index) => `
    <div class="recommendation"><span class="rec-number">${index + 1}</span><div><strong>${escapeHtml(item.theme)}</strong><p>${escapeHtml(item.action)}</p></div></div>`).join('');
  $('#results-table').innerHTML = data.results.map(row => `
    <tr><td>${escapeHtml(row.review)}</td><td><span class="sentiment-badge ${sentimentClass(row.sentiment)}">${escapeHtml(row.sentiment)}</span></td><td>${Number(row.score).toFixed(3)}</td><td>${escapeHtml(row.theme_text || 'Other')}</td></tr>`).join('');
  $('#table-count').textContent = `${data.results.length} rows`;
}
async function analyzeReviews() {
  clearError();
  const reviews = reviewsInput.value.split(/\r?\n/).map(value => value.trim()).filter(Boolean);
  if (!reviews.length) return showError('Enter at least one review, or load the sample reviews to try the app.');
  if (reviews.length > 1000) return showError('Please analyze no more than 1,000 reviews at a time.');
  const button = $('#analyze-button');
  setLoading(button, true);
  try {
    const response = await fetch('/api/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({reviews})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Analysis failed. Please try again.');
    renderResults(data);
    $('#results').scrollIntoView({behavior:'smooth', block:'start'});
  } catch (error) {
    showError(error.message || 'Could not connect to the server. Please try again.');
  } finally { setLoading(button, false); }
}
async function analyzeCsv() {
  clearError();
  const file = $('#csv-file').files[0];
  if (!file) return showError('Choose a CSV file before analyzing.');
  if (file.size > 5 * 1024 * 1024) return showError('The CSV file must be 5 MB or smaller.');
  const formData = new FormData();
  formData.append('file', file);
  const button = $('#upload-analyze-button');
  setLoading(button, true);
  try {
    const response = await fetch('/api/analyze-csv', {method:'POST', body:formData});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'CSV analysis failed.');
    renderResults(data);
    $('#results').scrollIntoView({behavior:'smooth', block:'start'});
  } catch (error) {
    showError(error.message || 'Could not analyze this CSV. Please check its format.');
  } finally { setLoading(button, false); }
}
function downloadCsv() {
  if (!latestAnalysis) return;
  const headers = ['Review', 'Sentiment', 'Sentiment Score', 'Positive Score', 'Neutral Score', 'Negative Score', 'Themes'];
  const rows = latestAnalysis.results.map(row => [row.review, row.sentiment, row.score, row.positive_score, row.neutral_score, row.negative_score, row.theme_text]);
  const csvCell = value => `"${String(value ?? '').replace(/"/g, '""')}"`;
  const content = '\uFEFF' + [headers, ...rows].map(row => row.map(csvCell).join(',')).join('\r\n');
  const blob = new Blob([content], {type:'text/csv;charset=utf-8;'});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'product-feedback-analysis.csv';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
function switchTab(tab) {
  const paste = tab === 'paste';
  $('#paste-tab').classList.toggle('active', paste);
  $('#upload-tab').classList.toggle('active', !paste);
  $('#paste-tab').setAttribute('aria-selected', String(paste));
  $('#upload-tab').setAttribute('aria-selected', String(!paste));
  $('#paste-view').classList.toggle('hidden', !paste);
  $('#upload-view').classList.toggle('hidden', paste);
  clearError();
}

reviewsInput.value = sampleReviews.slice(0, 3).join('\n');
updateReviewCount();
reviewsInput.addEventListener('input', updateReviewCount);
$('#analyze-button').addEventListener('click', analyzeReviews);
$('#upload-analyze-button').addEventListener('click', analyzeCsv);
$('#sample-button').addEventListener('click', () => { reviewsInput.value = sampleReviews.join('\n'); updateReviewCount(); clearError(); switchTab('paste'); });
$('#clear-button').addEventListener('click', () => { reviewsInput.value = ''; updateReviewCount(); clearError(); });
$('#paste-tab').addEventListener('click', () => switchTab('paste'));
$('#upload-tab').addEventListener('click', () => switchTab('upload'));
$('#export-button').addEventListener('click', downloadCsv);
$('#csv-file').addEventListener('change', event => { $('#file-name').textContent = event.target.files[0]?.name || 'No file selected'; clearError(); });
