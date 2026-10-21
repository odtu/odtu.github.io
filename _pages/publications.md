---
title: "Powerlab - Publications"
layout: gridlay
excerpt: "Powerlab -- Publications."
sitemap: false
permalink: /publications/
---

{% assign pubs = site.data.publications %}
{% assign meta = site.data.publications_meta %}

<div class="team-intro" markdown="0">
Journal and conference papers by PowerLab's principal researchers and their students.
{% if meta %}<span class="pub-meta">{{ meta.total }} papers · updated {{ meta.updated | date: "%B %Y" }}</span>{% endif %}
</div>

<div class="team-nav" markdown="0">
<a href="#highlights">Highlights</a>
<a href="#all">All publications</a>
{% if site.data.patents.size > 0 %}<a href="#patents">Patents</a>{% endif %}
<a href="#theses">Theses &amp; profiles</a>
</div>

{% if pubs %}

{% if site.data.publications_selected.size > 0 %}
<h2 id="highlights">Selected Publications</h2>
{% assign highlight = "" | split: "" %}
{% for d in site.data.publications_selected %}
  {% for p in pubs %}{% if p.doi == d %}{% assign highlight = highlight | push: p %}{% endif %}{% endfor %}
{% endfor %}
{% else %}
<h2 id="highlights">Most Cited</h2>
{% assign highlight = pubs | sort: "cites" | reverse %}
{% endif %}

<div class="pub-list" markdown="0">
{% for p in highlight limit: 6 %}{% include publication.html p=p %}{% endfor %}
</div>

<h2 id="all">All Publications</h2>

<div class="pub-filters" markdown="0">
  <input type="search" id="pub-q" placeholder="Search title, author, venue…" aria-label="Search publications">
  <div class="pub-chips" id="pub-kind">
    <button data-kind="" class="on">All</button>
    <button data-kind="journal">Journal</button>
    <button data-kind="conference">Conference</button>
    <button data-kind="book">Book chapter</button>
  </div>
  <select id="pub-pi" aria-label="Principal researcher">
    <option value="">All researchers</option>
    {% for prof in site.data.professors %}<option>{{ prof.name }}</option>{% endfor %}
  </select>
  <span id="pub-count" class="pub-count"></span>
</div>

<div class="pub-list" id="pub-all" markdown="0">
{% assign lastyear = "" %}
{% for p in pubs %}
{% assign y = p.year | append: "" %}
{% if y != lastyear %}<div class="al-year pub-year" data-year="{{ y }}">{{ y }}</div>{% assign lastyear = y %}{% endif %}
{% include publication.html p=p filter=true %}
{% endfor %}
</div>

{% else %}
<p>The publication list is being prepared. Meanwhile, see the <a href="https://avesis.metu.edu.tr/researchteamsite/powerlab/publications">AVESIS group page</a>.</p>
{% endif %}

{% if site.data.patents.size > 0 %}
<h2 id="patents">Patents</h2>
<div class="pub-list" markdown="0">
{% for pt in site.data.patents %}
<div class="pub">
  <div class="pub-title">{% if pt.url %}<a href="{{ pt.url }}">{{ pt.title }}</a>{% else %}{{ pt.title }}{% endif %}</div>
  <div class="pub-authors">{{ pt.inventors }}</div>
  <div class="pub-venue"><span class="pub-kind pub-k-patent">{% if pt.status == "pending" %}Pending{% elsif pt.status == "granted" %}Granted{% else %}Patent{% endif %}</span>{% if pt.number != "" %}{{ pt.number }}, {% endif %}{{ pt.year }}</div>
</div>
{% endfor %}
</div>
{% endif %}

<h2 id="theses">Theses &amp; Profiles</h2>

<div class="pub-links" markdown="0">
<a href="https://avesis.metu.edu.tr/researchteamsite/powerlab/theses">Graduate theses (AVESIS)</a>
<a href="https://avesis.metu.edu.tr/researchteamsite/powerlab/publications">Full list incl. national papers (AVESIS)</a>
</div>

<div class="al-grid" markdown="0">
{% for prof in site.data.professors %}
<div class="al-card">
  <div class="al-name">{{ prof.name }}</div>
  <div class="al-deg">
    {% if prof.scholar %}<a href="{{ prof.scholar }}">Google Scholar</a>{% endif %}
    {% if prof.orcid %}{% if prof.scholar %} · {% endif %}<a href="https://orcid.org/{{ prof.orcid }}">ORCID</a>{% endif %}
  </div>
</div>
{% endfor %}
</div>

<script>
(function () {
  var q = document.getElementById('pub-q'), pi = document.getElementById('pub-pi'),
      chips = document.querySelectorAll('#pub-kind button'), count = document.getElementById('pub-count'),
      items = document.querySelectorAll('#pub-all .pub'), years = document.querySelectorAll('#pub-all .pub-year'),
      kind = '';
  if (!q) return;
  function run() {
    var text = q.value.trim().toLowerCase(), who = pi.value, shown = 0, perYear = {};
    items.forEach(function (el) {
      var ok = (!kind || el.dataset.kind === kind) &&
               (!who || el.dataset.pis.split('|').indexOf(who) > -1) &&
               (!text || el.dataset.text.indexOf(text) > -1);
      el.style.display = ok ? '' : 'none';
      if (ok) { shown++; perYear[el.dataset.year] = 1; }
    });
    years.forEach(function (h) { h.style.display = perYear[h.dataset.year] ? '' : 'none'; });
    count.textContent = shown + ' of ' + items.length;
  }
  chips.forEach(function (b) {
    b.addEventListener('click', function () {
      chips.forEach(function (c) { c.classList.remove('on'); });
      b.classList.add('on'); kind = b.dataset.kind; run();
    });
  });
  q.addEventListener('input', run); pi.addEventListener('change', run); run();
})();
</script>
