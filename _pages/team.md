---
title: "Powerlab - Team"
layout: gridlay
excerpt: "Powerlab: Team members"
sitemap: false
permalink: /team/
---

<div class="team-intro" markdown="0">
PowerLab is a research group in the Electrical-Electronics Engineering Department at METU, working on electrical machines, power electronics, drives and power systems.
</div>

<div class="team-nav" markdown="0">
<a href="#pis">Principal Researchers</a>
<a href="#phd">PhD Students</a>
<a href="#msc">MSc Students</a>
<a href="#ug">Undergraduates</a>
<a href="#alumni">Alumni</a>
</div>

<h2 id="pis">Principal Researchers</h2>

{% include member_cards.html members=site.data.professors pi=true %}

<h2 id="phd">PhD Students</h2>

{% assign phd = site.data.team_members | where: "level", "phd" %}
{% include member_cards.html members=phd %}

<h2 id="msc">MSc Students</h2>

{% assign msc = site.data.team_members | where: "level", "msc" %}
{% include member_cards.html members=msc %}

{% if site.data.undergraduate.size > 0 %}
<h2 id="ug">Undergraduate Researchers</h2>

{% include member_cards.html members=site.data.undergraduate role="Undergraduate Researcher" %}
{% endif %}

<h2 id="alumni">Alumni of PowerLab</h2>

{% include alumni_grid.html %}

<div class="team-join" markdown="0">
<b>Interested in joining?</b> We welcome motivated undergraduate and graduate students. Contact one of the principal researchers with your CV and a short note on your interests.
</div>
