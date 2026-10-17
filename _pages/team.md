---
title: "Powerlab - Team"
layout: gridlay
excerpt: "Powerlab: Team members"
sitemap: false
permalink: /team/
---

## Principal Researchers

{% include team_grid.html members=site.data.professors show_contact=true %}

## Graduate Students

{% include team_grid.html members=site.data.team_members show_office=true %}

{% if site.data.undergraduate.size > 0 %}
## Undergraduate Students

{% include team_grid.html members=site.data.undergraduate photo_width="35%" %}
{% endif %}

## Alumni of PowerLab

{% include alumni_grid.html %}
